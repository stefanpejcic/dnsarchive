import json
import dns.resolver
from db import init_db, get_conn

def get_dns_records(domain):
    records = {}
    types = ["A", "AAAA", "MX", "NS"]

    for t in types:
        try:
            answers = dns.resolver.resolve(domain, t)
            records[t] = sorted([str(r.to_text()) for r in answers])
        except Exception:
            records[t] = []

    return records

def scan_domain(domain_id, domain):
    conn = get_conn()
    c = conn.cursor()

    new_records = get_dns_records(domain)
    new_json = json.dumps(new_records)

    c.execute("""
        SELECT records_json
        FROM dns_results
        WHERE domain_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (domain_id,))
    row = c.fetchone()

    changed = 1
    if row and row[0] == new_json:
        changed = 0

    c.execute("""
        INSERT INTO dns_results (domain_id, records_json, changed)
        VALUES (?, ?, ?)
    """, (domain_id, new_json, changed))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()

    conn = get_conn()
    c = conn.cursor()

    c.execute("SELECT id, domain FROM domains WHERE monitor = 1")
    domains = c.fetchall()
    conn.close()

    for domain_id, domain in domains:
        print(f"Scanning {domain}…")
        scan_domain(domain_id, domain)

    print("Scan complete.")
