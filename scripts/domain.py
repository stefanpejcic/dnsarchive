#!/usr/bin/env python3
import os
import sys
import json
import requests
import dns.resolver
from datetime import datetime
from threading import Thread

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <domain>")
    sys.exit(1)

DOMAIN = sys.argv[1]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)  # One level above
OUTDIR = os.path.join(PARENT_DIR, "results")
os.makedirs(OUTDIR, exist_ok=True)
DATE = datetime.now().strftime("%Y-%m-%d")
TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
OUTFILE = os.path.join(OUTDIR, f"{DATE}.json")

def query_dns(name, record_type):
    try:
        answers = dns.resolver.resolve(name, record_type)
        return [r.to_text() for r in answers]
    except Exception:
        return []

dns_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA"]
dns_records = {rtype: query_dns(DOMAIN, rtype) for rtype in dns_types}

output = {
    "domain": DOMAIN,
    "timestamp": TIMESTAMP,
    "dns_records": dns_records,
    "subdomains": {} 
}

with open(OUTFILE, "w") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))

# 2. Background function for CRT.SH + subdomains
def fetch_subdomains():
    try:
        crt_url = f"https://crt.sh/?q=%25.{DOMAIN}&output=json"
        resp = requests.get(crt_url, timeout=10)
        if resp.status_code != 200:
            raise Exception(f"CRT.SH returned status {resp.status_code}")

        data = resp.json()
        subs = sorted({entry["name_value"].replace("*.", "") for entry in data})
        subdomains_data = {}

        for sub in subs:
            subrecords = {rtype: query_dns(sub, rtype) for rtype in ["A", "AAAA", "MX", "TXT"]}
            subdomains_data[sub] = subrecords

        with open(OUTFILE, "r+") as f:
            current_data = json.load(f)
            current_data["subdomains"] = subdomains_data
            f.seek(0)
            json.dump(current_data, f, indent=2)
            f.truncate()

        print(f"Background: subdomain DNS records added to {OUTFILE}")

    except Exception as e:
        print(f"Background error fetching subdomains: {e}")

thread = Thread(target=fetch_subdomains, daemon=True)
thread.start()
