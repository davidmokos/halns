import logging
from flask import jsonify
from flask_restful_swagger_2 import Api

from app_factory import AppFactory


class CustomApi(Api):

    def __init__(self, app):
        super(Api, self).__init__(app=app)

    def handle_error(self, e):
        print(e.description)
        return jsonify({'message': e.description}), e.code


# Gunicorn setup before init
if __name__ != '__main__':

    app = AppFactory.create_app()

    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

# Classic setup before init
if __name__ == '__main__':

    app = AppFactory.create_app()

    app.run(host='0.0.0.0', port=6004)


