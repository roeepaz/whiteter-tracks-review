from flask import Flask, request, jsonify, render_template
from api_utils import handle_selected_plots
from recommendation.recomendations_manager import get_recommendation_base_on_strategy
from config_loader import load_config

def handle_error(e, status_code=500, error_type=None):
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


class Routes:
    def __init__(self, app: Flask, event_methods_instance):
        """Initialize the Routes handler by registering all Flask routes.

        Parameters:
            app (Flask): The Flask application instance.
            event_methods_instance (AbstractEventsAPI): Object that handles event logic (e.g., EventApi).
        """
        self.app = app
        self.handler = event_methods_instance
        self.setup_routes()

    def setup_routes(self):
        """ Defines all HTTP routes for the Flask app.
        Explanation:
            Registers endpoints for UI, API, track creation, recommendations, and event management.
        """
        @self.app.route('/')
        def home():
            """ Renders the home page with a list of event IDs.

            Output:
                Rendered HTML page or JSON error

            Explanation:
                Loads config and event list, then renders the home template.
            """
            try:
                config = load_config()
                if self.handler is None:
                    raise RuntimeError("Handler not initialized")

                event_ids = self.handler.get_events_ids_list()
                return render_template("home.html",
                                       message="Welcome to the whiteter-tracks Server",
                                       events_count=len(event_ids),
                                       event_ids=event_ids,
                                       config=config)
            except Exception as e:
                return handle_error(e)

        @self.app.route('/health')
        def health():
            """ Health check endpoint.

            Output:
                JSON {"status": "ok"} with HTTP 200

            Explanation:
                Used to check if the server is up.
            """
            return jsonify({"status": "ok"}), 200

        @self.app.route('/config', methods=['GET'])
        def get_config():
            """ Returns the current application configuration.
            Output:
                JSON with config data or error

            Explanation:
                Reads the local 'app_config.json' file and returns its content.
            """
            try:
                config = load_config()
                return jsonify({"success": True, "data": config})
            except Exception as e:
                return handle_error(e)

        @self.app.route('/api/events', methods=['GET'])
        def get_events_ids():
            """ Returns a list of event IDs.
            Output:
                JSON list of event IDs or error

            Explanation:
                Uses the handler to fetch event folder names. Validates them.
            """
            try:
                if self.handler is None:
                    raise RuntimeError("Handler not initialized")

                event_ids = self.handler.get_events_ids_list()

                for event_id in event_ids:
                    if not isinstance(event_id, str):
                        raise TypeError(f"Expected a string, but got {type(event_id).__name__}")

                if not event_ids:
                    raise ValueError("No events found")

                return jsonify({"success": True, "data": event_ids}), 200

            except (RuntimeError, TypeError, ValueError) as e:
                return handle_error(e, 400)
            except Exception as e:
                return handle_error(e)

        @self.app.route('/api/get-event/<event_id>', methods=['GET'])
        def get_event(event_id):
            """Return all data for a specific event.

            Parameters:
                event_id (str): The ID of the event to fetch.

            Returns:
                flask.Response: JSON response containing:
                    - 1: List of plot records.
                    - 2: List of white track records.
                    - 3: List of white track correlation records.
                or
                tuple(flask.Response, int): On error, a JSON payload with an "error" field and the HTTP status code.
            """
            try:
                data = self.handler.get_event_data(event_id)
                return jsonify({"success": True, "data": data})
            except Exception as e:
                return handle_error(e)

        @self.app.route('/creat-track', methods=['POST'])
        def create_track():
            """Create a smoothing spline track from selected plots.

            Parameters:
                data (list[dict]): Selected plot records from the request JSON payload.
                smoothingFactor (float | int): Smoothing factor for the spline calculation.

            Returns:
                flask.Response: JSON response containing:
                    {
                        "splinePoints": list  # Evaluated points along the generated spline
                    }
            """
            try:
                selected_plots = request.json.get('data', [])
                smoothing_factor = request.json.get('smoothingFactor',0.8)

                if not selected_plots:
                    raise ValueError("No plots received")

                spline_points = handle_selected_plots(selected_plots, smoothing_factor)
                return jsonify({"success": True, "data": spline_points})

            except ValueError as e:
                return handle_error(e, 400)
            except Exception as e:
                return handle_error(e)

        @self.app.route('/submit-event', methods=['POST'])
        def submit_event():
            """
            Finalizes an event and saves tracks + notes.

            Input (JSON):
                event_id: str
                tracks: dict - All user-defined tracks
                notes: str - General notes

            Output:
                JSON success or error message

            Explanation:
                Sends all event data to handler to save as CSV and JSON files.
            """
            try:
                data = request.get_json()
                event_id = data.get('event_id', '')
                tracks = data.get('tracks', {})
                notes = data.get('notes', '')

                if not tracks:
                    raise ValueError("No tracks provided")

                self.handler.close_event(event_id, tracks, notes)
                return jsonify({"success": True, "message": "Tracks and notes saved successfully!"}), 200

            except ValueError as e:
                return handle_error(e, 400)
            except Exception as e:
                return handle_error(e)

        @self.app.route('/get-recommendation', methods=['POST'])
        def get_recommendation_server():
            """Return recommended tracks based on selected plots.

            Parameters:
                plots (list[dict]): Selected plot records from the request JSON payload.
                eventId (str): ID of the event for which to generate recommendations.
                recommendationType (str): Name of the strategy to use for recommendation.

            Returns:
                flask.Response: JSON response with the following structure on success:
                    {
                        "recommendedTracks": list  # List of recommended plots records
                    }
                or
                tuple(flask.Response, int): On error, a JSON payload with an "error" field and appropriate HTTP status code.
            """
            try:
                selected_plots = request.json.get('plots', [])
                event_id = request.json.get('eventId', '')
                recommendation_type = request.json.get('recommendationType', '')

                if not selected_plots and recommendation_type:
                    raise ValueError("No data received")

                result = get_recommendation_base_on_strategy(recommendation_type, event_id, selected_plots)
                return jsonify({"success": True, "data": result})

            except ValueError as e:
                return handle_error(e, 400)
            except Exception as e:
                return handle_error(e)
