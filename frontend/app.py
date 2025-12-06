from flask import Flask, render_template, request, abort, jsonify
import os
import subprocess
import json
import re
from functools import wraps
from datetime import datetime

app = Flask(__name__)

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(FRONTEND_DIR, "..", "backend")
SUMMARY_DIR = os.path.join(FRONTEND_DIR, "..", "summary")

# stricter domain regex
DOMAIN_REGEX = re.compile(r'^(?!-)(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$')

# --- Helper Functions ---

def safe_domain_path(domain):
    if not DOMAIN_REGEX.match(domain):
        return None
    safe_domain = domain.replace("/", "").replace("\\", "")
    path = os.path.join(SUMMARY_DIR, safe_domain, "summary.json")
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(SUMMARY_DIR)):
        return None
    return abs_path

def validate_day(day_str):
    if day_str:
        try:
            datetime.strptime(day_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    return False

# --- Decorator for API or Template response ---
def api_or_template(template_name):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if isinstance(result, tuple):
                data, status = result
            else:
                data, status = result, 200

            if request.path.startswith("/api/"):
                return jsonify(data), status
            else:
                return render_template(template_name, **data), status
        return wrapper
    return decorator

# --- Routes ---

@app.route("/")
@app.route("/api/")
@api_or_template("index.html")
def index():
    total_file = os.path.join(SUMMARY_DIR, "total.json")
    if not os.path.exists(total_file):
        summarize_script = os.path.join(SCRIPTS_DIR, "total.py")
        try:
            subprocess.run(["python3", summarize_script], check=True)
        except subprocess.CalledProcessError as e:
            return {"error": f"Error running summarize script: {e}"}, 500

    summary = {}
    if os.path.isfile(total_file):
        try:
            with open(total_file, "r") as f:
                summary = json.load(f)
        except json.JSONDecodeError:
            summary = {}

    return {"summary": summary}

@app.route("/domain/<domain>")
@app.route("/api/domain/<domain>")
@api_or_template("domain.html")
def domain_page(domain):
    summary_file = safe_domain_path(domain)
    if not summary_file:
        return {"error": "Invalid or unsafe domain"}, 400
    
    day = request.args.get("day")
    if day and not validate_day(day):
        return {"error": "Invalid day format, should be YYYY-MM-DD"}, 400

    domain_script = os.path.join(SCRIPTS_DIR, "domain.py")
    try:
        subprocess.Popen(["python3", domain_script, domain])
    except Exception as e:
        return {"error": f"Error running domain script: {e}"}, 500

    domain_summary = {}
    day_data = {}

    summarize_script = os.path.join(SCRIPTS_DIR, "summarize.py")
    try:
        subprocess.Popen(["python3", summarize_script])
    except Exception as e:
        return {"error": f"Error running domain script: {e}"}, 500
    
    if os.path.isfile(summary_file):
        try:
            with open(summary_file) as f:
                domain_summary = json.load(f)
            if day and day in domain_summary:
                day_data = domain_summary[day]
        except json.JSONDecodeError:
            domain_summary = {}

    return {
        "selected_domain": domain,
        "domain_summary": domain_summary,
        "day_data": day_data
    }

# --- Run App ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
