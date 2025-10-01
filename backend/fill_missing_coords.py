# fill_missing_coords.py
import re, json, math, psycopg2
from psycopg2.extras import RealDictCursor

RE = re.compile(r'(\d{2,4}[NS]\d{2,4}[EW])')

def parse_compact_coord(s):
    # examples: 5957N02905E or 5152N08600E or 440846N0430829E (longer)
    s = re.sub(r'[^0-9NSEW]', '', s.upper())
    m = re.search(r'(\d{2,4})(\d{2,4})?([NS])(\d{2,4})(\d{2,4})?([EW])', s)
    if not m:
        # fallback simple pair like 5957N02905E -> lat_deg=59 lat_min=57 etc
        # try short pattern:
        m2 = re.match(r'(\d{2})(\d{2})([NS])(\d{3})(\d{2})([EW])', s)
        if not m2:
            return None
        la_deg = int(m2.group(1)); la_min = int(m2.group(2))
        lo_deg = int(m2.group(4)); lo_min = int(m2.group(5))
        lat = la_deg + la_min/60.0
        lon = lo_deg + lo_min/60.0
        if m2.group(3) == 'S': lat = -lat
        if m2.group(6) == 'W': lon = -lon
        return lat, lon
    # best-effort parsing
    groups = m.groups()
    # brute convert: take first two digits as degrees, next two as minutes if exist
    la = m.group(1)
    # fallback: if la length 4 -> deg+min else handle
    def conv_lat(la, ns):
        if len(la) >= 4:
            deg = int(la[:-2]); mins = int(la[-2:])
        else:
            deg = int(la); mins = 0
        latv = deg + mins/60.0
        if ns == 'S': latv = -latv
        return latv
    def conv_lon(lo, ew):
        if len(lo) >= 5:
            deg = int(lo[:-2]); mins = int(lo[-2:])
        else:
            deg = int(lo); mins = 0
        lonv = deg + mins/60.0
        if ew == 'W': lonv = -lonv
        return lonv
    la_raw, ns = m.group(1), m.group(3)
    lo_raw, ew = m.group(4), m.group(6)
    return conv_lat(la_raw, ns), conv_lon(lo_raw, ew)

def find_first_coord_in_text(txt):
    if not txt: return None
    for m in RE.finditer(txt):
        coord = m.group(1)
        res = parse_compact_coord(coord)
        if res:
            return res
    return None

def main():
    conn = psycopg2.connect("host=localhost dbname=gis user=postgres password=postgres")
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, flight_id, raw_payload::text FROM flights WHERE start_geom IS NULL LIMIT 500;")
    rows = cur.fetchall()
    print("Rows to check:", len(rows))
    for r in rows:
        pid = r['id']
        raw = r['raw_payload__text'] if 'raw_payload__text' in r else r['raw_payload']
        if isinstance(raw, str):
            text = raw
        else:
            text = json.dumps(raw, ensure_ascii=False)
        found = find_first_coord_in_text(text)
        if found:
            lat, lon = found
            # write start_lat/start_lon and geom
            cur2 = conn.cursor()
            cur2.execute(
                "UPDATE flights SET start_lat=%s, start_lon=%s, start_geom=ST_SetSRID(ST_Point(%s,%s),4326) WHERE id=%s",
                (lat, lon, lon, lat, pid)
            )
            conn.commit()
            print("Updated", pid, "->", lat, lon)
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
