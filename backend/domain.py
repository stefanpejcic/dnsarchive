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

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", DOMAIN)
os.makedirs(OUTDIR, exist_ok=True)
OUTFILE = os.path.join(OUTDIR, f"{datetime.now():%Y-%m-%d}.json")
TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def query_dns(name, record_type):
    try:
        return [r.to_text() for r in dns.resolver.resolve(name, record_type)]
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

# CRT.SH
def fetch_subdomains():
    try:
        resp = requests.get(f"https://crt.sh/?q=%25.{DOMAIN}&output=json", timeout=10)
        resp.raise_for_status()
        subs = sorted({entry["name_value"].replace("*.", "") for entry in resp.json()})
        subdomains_data = {sub: {rtype: query_dns(sub, rtype) for rtype in ["A", "AAAA", "MX", "TXT"]} for sub in subs}

        with open(OUTFILE, "r+") as f:
            data = json.load(f)
            data["subdomains"] = subdomains_data
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        print(f"Background: subdomain DNS records added to {OUTFILE}")
    except Exception as e:
        print(f"Background error fetching subdomains: {e}")

Thread(target=fetch_subdomains, daemon=True).start()
