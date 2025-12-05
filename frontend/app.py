from flask import Flask, render_template, request
import os
import subprocess
import json

app = Flask(__name__)

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(FRONTEND_DIR, "..", "backend")
SUMMARY_DIR = os.path.join(FRONTEND_DIR, "..", "summary")

@app.route("/")
def index():
    total_file = os.path.join(SUMMARY_DIR, "total.json")
    with open(total_file, "r") as f:
        summary = json.load(f)
    return render_template("index.html", summary=summary)

@app.route("/domain/<domain>")
def domain_page(domain):
    day = request.args.get("day")  # YYYY-MM-DD
    domain_script = os.path.join(SCRIPTS_DIR, "domain.py")
    subprocess.Popen(["python3", domain_script, domain])
    summary_file = os.path.join(SUMMARY_DIR, domain, "summary.json")
    domain_summary = {}
    day_data = {}
    if os.path.isfile(summary_file):
        with open(summary_file) as f:
            domain_summary = json.load(f)
        if day and day in domain_summary:
            day_data = domain_summary[day]

    return render_template("domain.html",
                           selected_domain=domain,
                           domain_summary=domain_summary,
                           day_data=day_data)

if __name__ == "__main__":
    app.run(debug=True)
