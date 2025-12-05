#!/usr/bin/env python3
import os
import sys
import json
import requests
import dns.resolver
from datetime import datetime, timedelta
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
    file_mtime = datetime.fromtimestamp(os.path.getmtime(OUTFILE))
    if datetime.now() - file_mtime < timedelta(hours=24):
        with open(OUTFILE, "r") as f:
            existing_content = json.load(f)
        existing_content["message"] = f"DANGER: Domain {DOMAIN} was already scanned in the last 24h."

        print(json.dumps(existing_content, indent=2))
        sys.exit(0)


TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def query_dns(name, record_type):
    try:
        return [r.to_text() for r in dns.resolver.resolve(name, record_type)]
    except Exception:
        return []

dns_types = ["A", "AAAA", "MX", "NS", "TXT", "SOA"]
dns_records = {rtype: query_dns(DOMAIN, rtype) for rtype in dns_types}

# 1st json save
output = {
    "domain": DOMAIN,
    "message": f"INFO: Scanning in progress..",
    "timestamp": TIMESTAMP,
    "dns_records": dns_records,
    "subdomains": {},
    "changes": 0,
    "previous": None
}

with open(OUTFILE, "w") as f:
    json.dump(output, f, indent=2)

print(json.dumps(output, indent=2))


def fetch_subdomains_and_compare():
    try:
        # compare with previous file and 2nd json update
        date_pattern = re.compile(r"(\d{4}-\d{2}-\d{2})\.json$")
        previous_file = None
        latest_date = None
        for f in os.listdir(OUTDIR):
            match = date_pattern.search(f)
            if match and f != os.path.basename(OUTFILE):
                file_date = datetime.strptime(match.group(1), "%Y-%m-%d")
                if latest_date is None or file_date > latest_date:
                    latest_date = file_date
                    previous_file = os.path.join(OUTDIR, f)

        previous_data = {}
        changes_count = 0
        if previous_file:
            with open(previous_file, "r") as f:
                previous_data = json.load(f)

            for rtype, records in dns_records.items():
                old_set = set(previous_data.get("dns_records", {}).get(rtype, []))
                new_set = set(records)
                changes_count += len(new_set - old_set) - len(old_set - new_set)

        with open(OUTFILE, "r+") as f:
            data = json.load(f)
            data["changes"] = changes_count
            data["previous"] = previous_file
            data["message"] = f"WARNING: Checking subdomains.."
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        # fetch data from CRT.sh
        resp = requests.get(f"https://crt.sh/?q=%25.{DOMAIN}&output=json", timeout=10)
        resp.raise_for_status()
        subs = sorted({entry["name_value"].replace("*.", "") for entry in resp.json()})
        MAX_SUBDOMAINS = 50
        subs = subs[:MAX_SUBDOMAINS]
        subdomains_data = {sub: {rtype: query_dns(sub, rtype) for rtype in ["A", "AAAA", "MX", "TXT"]} for sub in subs}

        # fetch DNS for subdomains
        prev_subs = previous_data.get("subdomains", {})
        for sub, records in subdomains_data.items():
            old_records = prev_subs.get(sub, {})
            for rtype, rdata in records.items():
                old_set = set(old_records.get(rtype, []))
                new_set = set(rdata)
                changes_count += len(new_set - old_set) - len(old_set - new_set)

        # 3rd json update
        with open(OUTFILE, "r+") as f:
            data = json.load(f)
            start_time = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.now()
            duration = end_time - start_time
        
            data["subdomains"] = subdomains_data
            data["changes"] = changes_count
            data["message"] = f"SUCCESS: Completed in {str(duration)}"           
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

    except Exception as e:
        print(f"Background error: {e}")

Thread(target=fetch_subdomains_and_compare, daemon=True).start()
