import json
import os
from flask import Flask, request, jsonify, render_template

from api_utils import handle_selected_plots
from recommendation.recomendations_manager import get_recommendation_base_on_strategy

CONFIG_PATH = os.path.join(os.path.dirname(__file__),"app_config.json")

def handle_error(e, status_code=500, error_type=None):
    """
    Handles error formatting for consistent JSON responses.

    Input:
        e: Exception - The exception to handle
        status_code: int - HTTP status code to return (default: 500)
        error_type: str (optional) - Custom error type

    Output:
        JSON response with success=False, error type and message

    Explanation:
        Prints error and returns standardized error response for the client.
    """
    print(f"[ERROR] {type(e).__name__}: {str(e)}")
    return jsonify({
        "success": False,
        "error": {
            "type": error_type if error_type else type(e).__name__,
            "message": str(e)
        }
    }), status_code


class Routes:
    def __init__(self, app: Flask, event_methods_instance):
        """
        Initializes the Routes handler.

        Input:
            app: Flask - Flask app instance
            event_methods_instance - Object that handles event logic (e.g. EventApi)

        Output:
            None

        Explanation:
            Saves references and sets up all Flask routes.
        """
        self.app = app
        self.handler = event_methods_instance
        self.setup_routes()

    def setup_routes(self):
        """
        Defines all HTTP routes for the Flask app.

        Input:
            None

        Output:
            None

        Explanation:
            Registers endpoints for UI, API, track creation, recommendations, and event management.
        """
        @self.app.route('/')
        def home():
            """
            Renders the home page with a list of event IDs.

            Input:
                None

            Output:
                Rendered HTML page or JSON error

            Explanation:
                Loads config and event list, then renders the home template.
            """
            try:
                with open(CONFIG_PATH, "r") as file:
                    config = json.load(file)

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
            """
            Health check endpoint.

            Input:
                None

            Output:
                JSON {"status": "ok"} with HTTP 200

            Explanation:
                Used to check if the server is up.
            """
            return jsonify({"status": "ok"}), 200

        @self.app.route('/config', methods=['GET'])
        def get_config():
            """
            Returns the current application configuration.

            Input:
                None

            Output:
                JSON with config data or error

            Explanation:
                Reads the local 'app_config.json' file and returns its content.
            """
            try:
                with open(CONFIG_PATH, "r") as file:
                    config = json.load(file)
                return jsonify({"success": True, "data": config})
            except Exception as e:
                return handle_error(e)

        @self.app.route('/api/events', methods=['GET'])
        def get_events_ids():
            """
            Returns a list of event IDs.

            Input:
                None

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
            """
            Returns all data for a specific event.

            Input:
                event_id: str - Event ID to fetch

            Output:
                JSON with event data or error

            Explanation:
                Uses the handler to load plots, tracks, and correlations for the given event ID.
            """
            try:
                data = self.handler.get_event_data(event_id)
                return jsonify({"success": True, "data": data})
            except Exception as e:
                return handle_error(e)

        @self.app.route('/creat-track', methods=['POST'])
        def create_track():
            """
            Creates a spline track from selected plots.

            Input (JSON):
                data: list - Selected plots
                smoothingFactor: float or int

            Output:
                JSON with list of spline points

            Explanation:
                Uses smoothing to calculate a curve for the selected points.
            """
            try:
                selected_plots = request.json.get('data', [])
                smoothing_factor = request.json.get('smoothingFactor')

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
            """
            Returns recommended tracks based on selected plots.

            Input (JSON):
                plots: list - Selected plots
                eventId: str
                recommendationType: str - Strategy to use

            Output:
                JSON with recommended tracks

            Explanation:
                Uses a strategy-based function to generate recommended tracks based on input plots.
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
