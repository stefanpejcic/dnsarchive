from flask import Flask, render_template, request
import os
import subprocess
import json

app = Flask(__name__)

FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(FRONTEND_DIR, "..", "scripts")
SUMMARY_DIR = os.path.join(FRONTEND_DIR, "..", "summary")

@app.route("/", methods=["GET", "POST"])
def index():
    domains = sorted([d for d in os.listdir(SUMMARY_DIR) if os.path.isdir(os.path.join(SUMMARY_DIR, d))])
    selected_domain = None
    domain_summary = {}
    day_data = {}

    if request.method == "POST":
        selected_domain = request.form.get("domain")
        day = request.form.get("day")  #  YYYY-MM-DD
        domain_script = os.path.join(SCRIPTS_DIR, "domain.py")
        subprocess.Popen(["python3", domain_script, selected_domain])
        summary_file = os.path.join(SUMMARY_DIR, selected_domain, "summary.json")

        if os.path.isfile(summary_file):
            with open(summary_file) as f:
                domain_summary = json.load(f)
            if day in domain_summary:
                day_data = domain_summary[day]

    return render_template("index.html",
                           domains=domains,
                           selected_domain=selected_domain,
                           domain_summary=domain_summary,
                           day_data=day_data)

if __name__ == "__main__":
    app.run(debug=True)
