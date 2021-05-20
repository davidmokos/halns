import os
from os.path import join
from pathlib import Path
from typing import List

from firebase_admin import credentials, firestore, initialize_app


class FirebaseManager(object):

    __instance = None

    def __new__(cls, key_json):
        if FirebaseManager.__instance is None:
            FirebaseManager.__instance = object.__new__(cls)
        return FirebaseManager.__instance

    def __init__(self, key_json=join('config', 'godeliver-dev-firebase-key.json')):

        if hasattr(self, 'default_app') and self.default_app is not None:
            return

        firebase_key = os.path.join(self.get_project_root(), key_json)

        self.cred = credentials.Certificate(firebase_key)
        self.default_app = initialize_app(self.cred)

        self.database = firestore.client()

    def get_project_root(self):
        """Returns project root folder."""
        return str(Path(__file__).parent.parent.parent)

