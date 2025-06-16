# Flask Event API Server

This Flask-based application exposes a secure, modular event-processing HTTP API with CORS support.

## Features

* **CORS Enabled**: Allows cross-origin requests from frontends (including credentials).
* **Modular Design**: Uses interface abstraction for better testing and extensibility.
* **HTTPS-Ready**: Runs securely using local SSL certificates.
* **Clear Separation of Concerns**:

  * `AbstractEventsAPI`: defines the contract for all event logic.
  * `EventApi`: concrete implementation using the filesystem.
  * `Routes`: maps HTTP routes to backend logic cleanly.

---

## Main Class: `main_class`

```python
from flask import Flask
from flask_cors import CORS
from events_logic.interface.AbstractEventsAPI import AbstractEventsAPI
from events_logic.events_api import EventApi
from routes import Routes
import os

basedir = os.getcwd()
cert_path = os.path.join(basedir, 'resource', 'cert.pem')
key_path = os.path.join(basedir, 'resource', 'key.pem')

class main_class:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app, supports_credentials=True)

        # Dependency injection of the backend logic
        event_methods_instance: AbstractEventsAPI = EventApi()
        Routes(self.app, event_methods_instance)

    def run(self):
        self.app.run(ssl_context=(cert_path, key_path))
```

---

## How to Run

```bash
python -m cd back-end
```

```bash
python -m python src/app.py
```

---

## 🔍 Endpoints

| Method | Route              | Description             |
| ------ | ------------------ | ----------------------- |
| GET    | `/health`          | Server status check     |
| GET    | `/config`          | App config              |
| POST   | `/create-track`    | create smooth line from plots      |
| POST   | `/get-recommendation`    | get tecommedation of lpots that are part of the tarck from the plots that I received |
| POST   | `/api/events`      | Submit a new event      |
| GET    | `/api/events/<id>` | Get event data by ID    |
| POST   | `/submit-event`    | Save or update an event |

---

## HTTPS Details

* Certificates are loaded from:

  * `resource/cert.pem`
  * `resource/key.pem`
* These enable local testing of secure requests (e.g., from localhost React frontend).

---

## References

* [Flask Documentation](https://flask.palletsprojects.com/)
* [Flask-CORS](https://flask-cors.readthedocs.io/)
