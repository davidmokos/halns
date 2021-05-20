import os
from godeliver_planner.helper.utils import YamlConfig
from godeliver_planner.model.planner_config import PlannerConfig


class ConfigProvider:

    _default_config = PlannerConfig()

    @staticmethod
    def get_config() -> PlannerConfig:
        try:
            from flask import g
            if 'planner_config' not in g:
                return ConfigProvider._default_config

            return g.planner_config

        except RuntimeError:
            return ConfigProvider._default_config

    @staticmethod
    def set_current_config(planner_config: PlannerConfig):
        if not planner_config:
            return

        try:
            from flask import g

            g.planner_config = planner_config

        except RuntimeError as e:
            raise Exception("When running outside of Flask application you can only work with the default config") from e

    @staticmethod
    def set_default_config(planner_config: PlannerConfig):
        if not planner_config:
            return

        ConfigProvider._default_config = planner_config



