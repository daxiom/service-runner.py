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

        if not (request_data := request.data):
            app.logger.error('no data in POST')
            # return OK so that the message is not re-queued
            return HTTPStatus.OK
        app.logger.debug(f'raw message: {request_data}')
        
        if not (call_back := get_callback()):
            app.logger.error('no callback set')
            # return a non 200 so that the message is requeued
            # TODO: figure out if this should Panic or not
            return HTTPStatus.SERVICE_UNAVAILABLE
        
        message_bytes = request_data
        if isinstance(msg_dict := json.loads(request_data.decode('UTF8')), MutableMapping):
            if msg_dict.get('subscription') and msg_dict.get('message'):
                base64_bytes = msg_dict['message']['data']
                message_bytes = base64.b64decode(base64_bytes)

        ce = alt = None
        try:
            ce = from_queue_message(message_bytes)
        except (CloudEventVersionException, InvalidCloudEventError, ValueError) as e:
            alt = message_bytes.decode("utf-8").strip()
    
        app.logger.info('call back for ce:{ce}, alt {alt}'.format(ce=ce, alt=alt))
        rc = call_back(ce, alt)
        app.logger.debug('call back returned:{rc} for ce:{ce}, alt {alt}'.format(rc=rc, ce=ce, alt=alt))

        return {}, rc if ('rc' in locals()) else 200

    return app
