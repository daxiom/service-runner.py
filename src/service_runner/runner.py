from __future__ import annotations

import multiprocessing
import os
from typing import Callable

import gunicorn.app.base
from dotenv import find_dotenv, load_dotenv

from service_http import create_app


load_dotenv(find_dotenv())


def number_of_workers():
    return (multiprocessing.cpu_count() * 2) + 1


def run(call_back: Callable = None):
    """This starts the main run of the http listener.
    
    Defaults:
    bind: 0.0.0.0:8080
    threads: 8
    workers: 1
    timeout: 0 ; keep set to 0 to support out-scaling
    """
    print('starting http server.')

    options = {
        'bind': '%s:%s' % ('0.0.0.0', os.environ.get('PORT', '8080')),
        'forwarded_allow_ips': '*',
        'secure_scheme_headers': {'X-Forwarded-Proto': 'https'},
        'threads': int(os.environ.get('GUNICORN_THREADS', '8')),
        'timeout': int(os.environ.get('GUNICORN_TIMEOUT', '0')),
        'workers': int(os.environ.get('GUNICORN_PROCESSES', '1')),
    }
    handler_app = create_app(call_back=call_back)
    StandaloneApplication(handler_app, options).run()


class StandaloneApplication(gunicorn.app.base.BaseApplication):

    def __init__(self, app, options=None, call_back=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
