from typing import Tuple
from flask import jsonify

def handle_error(e: Exception, status_code: int =500, error_type :str=None) -> Tuple:
    """Handle an exception and return a standardized JSON error response.

    Parameters:
        e: The exception that was raised.
        status_code: HTTP status code to return. Defaults to 500.
        error_type (optional): Custom error type identifier.

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
