"""service template package."""
import json
import os
import time
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Callable, Final

from flask import Flask, current_app, request, _app_ctx_stack
from simple_cloudevent import from_queue_message

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

        call_back = get_callback()

        if request.data and \
           (ce := from_queue_message(request.data)
        ):
            app.logger.info('call back for ce:{ce}')
            rc = call_back(ce)
            app.logger.debug('call back returned:{rc.status_code} for ce:{ce}')

        return {}, rc if ('rc' in locals()) else 200

    return app
