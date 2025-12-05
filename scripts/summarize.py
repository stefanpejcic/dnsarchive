#!/usr/bin/env python3
import os
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
SUMMARY_BASE_DIR = os.path.join(SCRIPT_DIR, "summary")

DNS_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "SOA"]

if not os.path.isdir(RESULTS_DIR):
    print(f"No folder named '{RESULTS_DIR}' found.")
    exit(1)

domains = [d for d in sorted(os.listdir(RESULTS_DIR)) if os.path.isdir(os.path.join(RESULTS_DIR, d))]
total_domains = len(domains)
print(f"Found {total_domains} domains.")

for idx, domain in enumerate(domains, start=1):
    print(f"Processing {idx}/{total_domains}: {domain}")
    domain_results_dir = os.path.join(RESULTS_DIR, domain)
    domain_summary_dir = os.path.join(SUMMARY_BASE_DIR, domain)
    os.makedirs(domain_summary_dir, exist_ok=True)

    summary = {}

    for filename in sorted(os.listdir(domain_results_dir)):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(domain_results_dir, filename)
        with open(filepath) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {filepath}, skipping.")
                continue

        record_counts = {rtype: 0 for rtype in DNS_TYPES}
        subdomain_count = len(data.get("subdomains", {}))

        for rtype in DNS_TYPES:
            record_counts[rtype] += len(data.get("dns_records", {}).get(rtype, []))

        for subdata in data.get("subdomains", {}).values():
            for rtype in DNS_TYPES:
                record_counts[rtype] += len(subdata.get(rtype, []))

        total_count = sum(record_counts.values())

        summary[filename.replace(".json", "")] = {
            "subdomain_count": subdomain_count,
            **record_counts,
            "total": total_count
        }

    summary_file = os.path.join(domain_summary_dir, "summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved summary for {domain} to {summary_file}")
