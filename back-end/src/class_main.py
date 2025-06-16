from flask import Flask
from flask_cors import CORS
from events_logic.abstract_events_api import AbstractEventsAPI
from events_logic.events_api import EventApi
from routes import Routes
import os

basedir = os.getcwd()
cert_path = os.path.join(basedir,'resource', 'cert.pem')
key_path = os.path.join(basedir,'resource', 'key.pem')

class main_class:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, supports_credentials=True)

        # Create an instance of the interface
        event_methods_instance: AbstractEventsAPI = EventApi()
        Routes(self.app, event_methods_instance)

    def run(self):
        self.app.run(ssl_context=(cert_path, key_path))
