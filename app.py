import os

from flask import (
    Flask,
    render_template,
    jsonify
)

from config import Config
from supabase_client import init_supabase

Config.validate()

app = Flask(__name__)
app.config.from_object(Config)

# Initialize Supabase if credentials are available
init_supabase()


@app.route("/")
def home():
    return render_template("dashboard.html")


@app.route("/health")
def health():
    return jsonify({
        "status": "success",
        "application": "School Work ERP",
        "message": "Application is running"
    }), 200


@app.route("/api/system-status")
def system_status():
    from supabase_client import get_supabase

    return jsonify({
        "application": "School Work ERP",
        "flask": "running",
        "supabase": (
            "configured"
            if get_supabase() is not None
            else "not_configured"
        )
    })


@app.errorhandler(404)
def page_not_found(error):
    return "Page not found", 404


@app.errorhandler(500)
def internal_error(error):
    return "Internal Server Error", 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )
