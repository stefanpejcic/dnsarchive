#!/usr/bin/env python3
import os
import sys
import json
import requests
import dns.resolver
from datetime import datetime
from threading import Thread
import re

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <domain>")
    sys.exit(1)

DOMAIN = sys.argv[1]

OUTDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results", DOMAIN)
os.makedirs(OUTDIR, exist_ok=True)
OUTFILE = os.path.join(OUTDIR, f"{datetime.now():%Y-%m-%d}.json")

if os.path.exists(OUTFILE):
    print(f"Abort: domain {DOMAIN} was already scanned in the last 24h.")
    sys.exit(0)


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
    "subdomains": {},
    "changes": {
        "total_changes": 0,
        "subdomain_changes": 0,
        "previous_file": None
    }
}

with open(OUTFILE, "w") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))

# runs in bg
def fetch_subdomains_and_compare():
    try:
        date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\.json$")
        previous_file = None
        latest_date = None
        for f in os.listdir(OUTDIR):
            match = date_pattern.search(f)
            if match:
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                if f != os.path.basename(OUTFILE):
                    if latest_date is None or file_date > latest_date:
                        latest_date = file_date
                        previous_file = os.path.join(OUTDIR, f)

        previous_data = {}
        if previous_file:
            with open(previous_file, "r") as f:
                previous_data = json.load(f)

        # CRT.sh
        resp = requests.get(f"https://crt.sh/?q=%25.{DOMAIN}&output=json", timeout=10)
        resp.raise_for_status()
        subs = sorted({entry["name_value"].replace("*.", "") for entry in resp.json()})
        MAX_SUBDOMAINS = 50 # todo
        subs = subs[:MAX_SUBDOMAINS]
        subdomains_data = {sub: {rtype: query_dns(sub, rtype) for rtype in ["A", "AAAA", "MX", "TXT"]} for sub in subs}
        prev_subs = previous_data.get("subdomains", {})
        subdomain_change_count = 0
        for sub, records in subdomains_data.items():
            old_records = prev_subs.get(sub, {})
            for rtype, rdata in records.items():
                old_set = set(old_records.get(rtype, []))
                new_set = set(rdata)
                subdomain_change_count += len(new_set - old_set) + len(old_set - new_set)

        total_change_count = subdomain_change_count
        if previous_data:
            for rtype, records in dns_records.items():
                old_set = set(previous_data.get("dns_records", {}).get(rtype, []))
                new_set = set(records)
                total_change_count += len(new_set - old_set) + len(old_set - new_set)

        with open(OUTFILE, "r+") as f:
            data = json.load(f)
            data["subdomains"] = subdomains_data
            data["changes"] = {
                "total_changes": total_change_count,
                "subdomain_changes": subdomain_change_count,
                "previous_file": previous_file
            }          
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        print(f"Background: subdomain DNS records updated and compared with {previous_file}")
        print(json.dumps(data["changes"], indent=2))

    except Exception as e:
        print(f"Background error: {e}")

Thread(target=fetch_subdomains_and_compare, daemon=True).start()
