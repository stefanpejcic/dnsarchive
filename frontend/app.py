from flask import Flask, render_template, request, abort
import os
import subprocess
import json
import re

app = Flask(__name__)

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(FRONTEND_DIR, "..", "backend")
SUMMARY_DIR = os.path.join(FRONTEND_DIR, "..", "summary")
DOMAIN_REGEX = re.compile(r'^(?:[a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,}$')

def safe_domain_path(domain):
    if not DOMAIN_REGEX.match(domain):
        return None
    safe_domain = domain.replace("/", "").replace("\\", "")
    path = os.path.join(SUMMARY_DIR, safe_domain, "summary.json")
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath(SUMMARY_DIR)):
        return None
    return abs_path

@app.route("/")
def index():
    total_file = os.path.join(SUMMARY_DIR, "total.json")
    with open(total_file, "r") as f:
        summary = json.load(f)
    return render_template("index.html", summary=summary)

@app.route("/domain/<domain>")
def domain_page(domain):
    summary_file = safe_domain_path(domain)
    if not summary_file:
        return abort(400, description="Invalid or unsafe domain")
    
    day = request.args.get("day")  # YYYY-MM-DD
    domain_script = os.path.join(SCRIPTS_DIR, "domain.py")
    
    try:
        subprocess.Popen(["python3", domain_script, domain])
    except Exception as e:
        return f"Error running domain script: {e}", 500

    domain_summary = {}
    day_data = {}

    if os.path.isfile(summary_file):
        with open(summary_file) as f:
            domain_summary = json.load(f)
        if day and day in domain_summary:
            day_data = domain_summary[day]

    return render_template(
        "domain.html",
        selected_domain=domain,
        domain_summary=domain_summary,
        day_data=day_data
    )

if __name__ == "__main__":
    app.run(debug=True)
