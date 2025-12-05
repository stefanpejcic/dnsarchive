from db import get_conn, init_db
import sys
import json

domain = sys.argv[1]
init_db()
conn = get_conn()
c = conn.cursor()

c.execute("INSERT OR IGNORE INTO domains (domain, monitor) VALUES (?,1)", (domain,))
conn.commit()
conn.close()

print(f"Added domain: {domain}")
