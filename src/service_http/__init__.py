"""service template package."""
import base64
import json
import os
import time
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Callable, Final, MutableMapping

from flask import Flask, current_app, request, _app_ctx_stack
from simple_cloudevent import CloudEventVersionException, InvalidCloudEventError, from_queue_message

from .config import Config
from .logging import structured_log
from .version import __version__


CALL_BACK_NAME: Final = 'service_runner_callback'


def default_call_back(msg):
    return HTTPStatus.OK

def get_callback() -> Callable:
    cb = current_app.config[CALL_BACK_NAME]
    return cb

def set_callback(cb: Callable):
    current_app.config.setdefault(CALL_BACK_NAME, cb)

def create_app(env: str = None, call_back: Callable = default_call_back):
    app = Flask(__name__)
    app.config.from_object(Config())

    with app.app_context():
        set_callback(call_back)

    @app.route("/", methods=["POST"])
    def process_message():
        '''Post should receive a SimpleCloudEvent message.'''

        app.logger.info('got a POST message')
        structured_log(request=request, severity='NOTICE', message='a POST')

        if not (call_back := get_callback()):
            app.logger.error('no callback set')
            # return a non 200 so that the message is requeued
            # TODO: figure out if this should Panic or not
            return HTTPStatus.SERVICE_UNAVAILABLE

        if not (envelope := request.get_json()) or not (pubsub_message := envelope.get('message')):
            app.logger.debug('no valid pubsub message in request: %s', request.data)
            # return a 200 so the message is removed from the queue
            return HTTPStatus.OK

        try:
            ce = alt = None
            if isinstance(pubsub_message, MutableMapping) \
            and (raw_data := pubsub_message.get('data')) \
            and (str_data := base64.b64decode(raw_data).decode("utf-8").strip()) \
            and (data := json.loads(str_data)):
                try:
                    ce = from_queue_message(data)
                except (CloudEventVersionException, InvalidCloudEventError, ValueError, Exception) as e:
                    alt = data
            else:
                alt = pubsub_message

            app.logger.info('call back for ce:{ce}, alt {alt}'.format(ce=ce, alt=alt))
            rc = call_back(ce, alt)
            app.logger.debug('call back returned:{rc} for ce:{ce}, alt {alt}'.format(rc=rc, ce=ce, alt=alt))

            return {}, rc if ('rc' in locals()) else 200
        
        except Exception as e:
            app.logger.exception('exception in call back: %s', e)
            return {}, HTTPStatus.INTERNAL_SERVER_ERROR

    return app
