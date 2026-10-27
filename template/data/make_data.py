"""Writes customers.csv and orders.csv, the data of the demo, as plain CSV.

    python3 data/make_data.py      # deterministic: same seed, same files
    ACCOUNT_MANAGERS="<viewer UPN of your tenant>:Ticino,giulia.bernasconi@example.com:Lombardia,luca.ferrari@example.com:Piemonte" python3 data/make_data.py

60 customers, three account managers with 20 each, credit limits 50k to 500k. 600 orders in 2026. Only the
first account manager should be a real user of your tenant (the viewer identity): RLS role members must exist
in the tenant; the other two are not, are refused, and the sessions record that as an open point. Without
ACCOUNT_MANAGERS the first one is the placeholder viewer@contoso.example; replace it before you build.
"""
import csv
import datetime
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = "viewer@contoso.example:Ticino,giulia.bernasconi@example.com:Lombardia,luca.ferrari@example.com:Piemonte"
MANAGERS = [tuple(x.strip().rsplit(":", 1)) for x in os.environ.get("ACCOUNT_MANAGERS", DEFAULT).split(",")]
CUSTOMERS, ORDERS = 60, 600

rnd = random.Random(2026_10_30)
ids = list(range(1, CUSTOMERS + 1))
mgr = [MANAGERS[(i - 1) // (CUSTOMERS // len(MANAGERS))] for i in ids]
credit = [rnd.choice([50, 100, 250, 500]) * 1000 for _ in ids]
with open(os.path.join(HERE, "customers.csv"), "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["customer_id", "customer_name", "region", "account_manager_upn", "credit_limit"])
    for i, m, cl in zip(ids, mgr, credit):
        w.writerow([i, f"Cliente {i:02d} SA", m[1], m[0], cl])
start = datetime.date(2026, 1, 1)
cust = [rnd.choice(ids) for _ in range(ORDERS)]
dates = [start + datetime.timedelta(days=rnd.randrange(290)) for _ in range(ORDERS)]
amounts = [rnd.randrange(500, 25000) for _ in range(ORDERS)]
with open(os.path.join(HERE, "orders.csv"), "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["order_id", "customer_id", "order_date", "amount"])
    for n, (cid, d, a) in enumerate(zip(cust, dates, amounts), 1):
        w.writerow([n, cid, d.isoformat(), a])
print(f"customers.csv {CUSTOMERS} rows, orders.csv {ORDERS} rows")
