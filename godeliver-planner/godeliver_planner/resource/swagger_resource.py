from flask import render_template, make_response
from flask_restful import Resource


class SwaggerResource(Resource):

    def __init__(self, **kwargs):
        super(SwaggerResource, self).__init__()

    def get(self):
        return make_response(
            render_template('swagger.html'),
            {'Content-Type': 'text/html'}
        )
