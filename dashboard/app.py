from flask import Flask, jsonify, render_template

from config.loader import load_config
from storage.db import latest_readings, readings_history, latest_prediction


def create_app(config: dict | None = None) -> Flask:
    """App factory, not a bare module-level `app = Flask(__name__)`.
    Lets tests spin up an isolated app instance pointed at a throwaway
    tmp_path database, instead of every test sharing one global app
    tied to the real frost_edge.db."""
    app = Flask(__name__)
    app.config["DB_PATH"] = (config or load_config())["storage"]["db_path"]

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/latest")
    def api_latest():
        db_path = app.config["DB_PATH"]
        return jsonify({
            "readings": latest_readings(db_path),
            "prediction": latest_prediction(db_path),
        })

    @app.route("/api/history/<key>")
    def api_history(key):
        rows = readings_history(key, limit=100, db_path=app.config["DB_PATH"])
        return jsonify([{"ts": ts, "value": value} for ts, value in rows])

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
