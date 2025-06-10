from typing import Tuple
from flask import jsonify

def handle_error(e, status_code=500, error_type=None) -> Tuple:
    """Handle an exception and return a standardized JSON error response.

    Parameters:
        e (Exception): The exception that was raised.
        status_code (int): HTTP status code to return. Defaults to 500.
        error_type (str, optional): Custom error type identifier.

    Returns:
        tuple[flask.Response, int]: A JSON response with structure 
            {
                "success": False,
                "error": {
                    "type": error_type or type(e).__name__,
                    "message": str(e)
                }
            }
        and the HTTP status code.
    """
    print(f"[ERROR] {type(e).__name__}: {e}")
    error_payload = {
        "success": False,
        "error": {
            "type": error_type or type(e).__name__,
            "message": str(e)
        }
    }
    return jsonify(error_payload), status_code
