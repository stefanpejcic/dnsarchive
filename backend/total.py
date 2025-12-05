#!/usr/bin/env python3
import os
import json

SUMMARY_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "summary")
OUTDIR = SUMMARY_BASE_DIR
OUTPUT_FILE = os.path.join(OUTDIR, "total.json")

if not os.path.isdir(SUMMARY_BASE_DIR):
    print(f"No folder named '{SUMMARY_BASE_DIR}' found.")
    exit(1)

domains = sorted(d for d in os.listdir(SUMMARY_BASE_DIR) if os.path.isdir(os.path.join(SUMMARY_BASE_DIR, d)))

total_checks = 0
total_records = 0

for domain in domains:
    summary_file = os.path.join(SUMMARY_BASE_DIR, domain, "summary.json")
    if not os.path.isfile(summary_file):
        print(f"Warning: {summary_file} not found, skipping.")
        continue

    try:
        with open(summary_file) as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Could not parse {summary_file}, skipping.")
        continue

    total_checks += len(data)
    total_records += sum(entry.get("total", 0) for entry in data.values())

global_summary = {
    "total_domains": len(domains),
    "total_checks": total_checks,
    "total_records": total_records
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(global_summary, f, indent=2)

print(f"Global summary saved to {OUTPUT_FILE}")
