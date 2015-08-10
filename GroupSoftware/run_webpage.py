#!/usr/bin/python
import logging
import sys
from gqweb import app
from werkzeug.serving import run_simple

URL_PREFIX = '/farmdebug'


class ScriptNameEdit(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        url = environ['SCRIPT_NAME']
        environ['SCRIPT_NAME'] = URL_PREFIX + url
        return self.app(environ, start_response)


class RemoteUserMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        user = environ.get('HTTP_X_MYREMOTE_USER', None)
        environ['REMOTE_USER'] = user
        return self.app(environ, start_response)

app = ScriptNameEdit(app)
app = RemoteUserMiddleware(app)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    run_simple('0.0.0.0', 5000, app,
               use_reloader=True, use_debugger=True, use_evalex=True)
