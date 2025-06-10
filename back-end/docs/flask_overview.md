# Flask Application Overview

This Flask application provides a secure, CORS-enabled HTTP API for event management:

* **App Initialization**:

  * Creates a `Flask(__name__)` instance.
  * Applies CORS middleware to allow cross-origin requests with credentials.

* **Modular Design**:

  * Defines an `AbstractEventsAPI` interface for event operations (e.g., load, list, close).
  * Implements `EventApi` as the concrete class reading/writing events on disk.
  * Uses a `Routes` helper to register endpoints on the Flask app (e.g., `/api/events`, `/submit-event`).

* **SSL Configuration**:

  * Loads `cert.pem` and `key.pem` from the `resource` directory.
  * Starts the server with HTTPS (`ssl_context=(cert_path, key_path)`), ensuring encrypted communication.

* **Entry Point**:

  * Encapsulated in `main_class`, which wires up CORS, the API implementation, and routes, then runs the server.

## Usage

```bash
python -m your_module.main_class
```

Access the health check at:

```
https://<host>:<port>/health
```

## Reference

* [Flask Official Documentation](https://flask.palletsprojects.com/en/latest/)
