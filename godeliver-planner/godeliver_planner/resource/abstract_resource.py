from abc import ABC
from collections import Callable

from flask_restful import Resource

from godeliver_planner.helper.exceptions import APIException
from flask import jsonify, abort


class AbstractResource(Resource):

    @staticmethod
    def _execute_with_check(fun, inp, code):
        try:
            if fun is not None:
                if inp is not None:
                    return fun(**inp)
                else:
                    return fun()
            else:
                return inp
        except Exception as e:
            raise APIException(code, str(e))

    def handle_request(self, request_parameters: dict = None,
                       parse_body=None, get_entities=None, validate_input=None, execute=None):
        try:
            args_as_ids = self._execute_with_check(parse_body, request_parameters, 400)
            args_as_entities = self._execute_with_check(get_entities, args_as_ids, 404)
            self._execute_with_check(validate_input, args_as_entities, 406)
            ret_args = self._execute_with_check(execute, args_as_entities, 500)

        except APIException as e:
            abort(e.code, e.message)
            return

        if ret_args is None:
            return jsonify(status='success')
        return jsonify(status='success', **ret_args)

