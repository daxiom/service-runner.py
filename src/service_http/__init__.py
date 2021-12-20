"""service template package."""
import json
import os
import time
from datetime import datetime, timezone
from http import HTTPStatus
from typing import Callable

from flask import Flask, request
from simple_cloudevent import from_queue_message

from .config import Config
from .logging import structured_log
from .version import __version__

def default_call_back(msg):
    return HTTPStatus.OK

def create_app(env: str = None, call_back: Callable = default_call_back):
    app = Flask(__name__)
    app.config.from_object(Config())


    @app.route("/", methods=["POST"])
    def process_message(call_back: Callable = default_call_back):
        '''Post should receive a SimpleCloudEvent message.'''

        app.logger.info('got a POST message')
        structured_log(request=request, severity='NOTICE', message='a POST')

        if request.data and \
           (ce := from_queue_message(request.data)
        ):
            app.logger.info('call back for ce:{ce}')
            call_back = call_back or default_call_back
            rc = call_back(ce)
            app.logger.debug('call back returned:{rc.status_code} for ce:{ce}')

        return {}, rc if ('rc' in locals()) else 200

    return app
