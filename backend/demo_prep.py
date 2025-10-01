import psycopg2
import os
import json
from matplotlib import pyplot as plt

DB_DSN = os.getenv("DB_DSN", "host=localhost dbname=gis user=postgres password=postgres")

def top_regions(n=10):
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    cur.execute("SELECT r.name, COUNT(*) FROM flights f JOIN public.regions r ON f.start_region_id=r.id GROUP BY r.name ORDER BY COUNT(*) DESC LIMIT %s;", (n,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def plot_top_regions(rows, outpath="regions_top.png"):
    names = [r[0] for r in rows]
    counts = [r[1] for r in rows]
    plt.figure(figsize=(10,6))
    plt.bar(range(len(names)), counts)
    plt.xticks(range(len(names)), names, rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(outpath)
    print("Wrote", outpath)

if __name__ == "__main__":
    rows = top_regions(10)
    print(rows)
    plot_top_regions(rows)
