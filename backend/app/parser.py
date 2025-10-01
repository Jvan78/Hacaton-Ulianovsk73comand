# parser.py
import re
import json
import math
import hashlib
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any

# -----------------------
# helpers
# -----------------------
def _is_nan(v):
    return isinstance(v, float) and math.isnan(v)

def safe_str(v):
    if v is None:
        return None
    if _is_nan(v):
        return None
    return str(v)

def safe_get_str(d: Dict, key: str):
    v = d.get(key) if isinstance(d, dict) else None
    return safe_str(v)

# 1) parse compact coordinate like 5957N02905E or 440846N0430829E
def parse_compact_coord(s: Optional[str]) -> Optional[Tuple[float, float]]:
    if not s:
        return None
    s = re.sub(r'[^0-9NSEWnsew]', '', str(s))
    s = s.upper()
    # try with deg/min (no seconds): 5957N02905E or 5152N08600E
    m = re.match(r'^(\d{2,4})(\d{2})(N|S)(\d{2,3})(\d{2})(E|W)$', s)
    if m:
        lat_part = m.group(1)
        lat_deg = int(lat_part[:-2]) if len(lat_part) > 2 else int(lat_part)
        lat_min = int(m.group(2))
        lat_hem = m.group(3)
        lon_deg = int(m.group(4))
        lon_min = int(m.group(5))
        lon_hem = m.group(6)
        lat = lat_deg + lat_min / 60.0
        lon = lon_deg + lon_min / 60.0
        if lat_hem == 'S':
            lat = -lat
        if lon_hem == 'W':
            lon = -lon
        return (round(lat, 8), round(lon, 8))
    # try with deg/min/sec: 564630N0620220E (DDMMSSN DDDMMSSE)
    m2 = re.match(r'^(\d{2})(\d{2})(\d{2})(N|S)(\d{3})(\d{2})(\d{2})(E|W)$', s)
    if m2:
        lat = int(m2.group(1)) + int(m2.group(2))/60 + int(m2.group(3))/3600
        lon = int(m2.group(5)) + int(m2.group(6))/60 + int(m2.group(7))/3600
        if m2.group(4) == 'S':
            lat = -lat
        if m2.group(8) == 'W':
            lon = -lon
        return (round(lat,8), round(lon,8))
    return None

# 2) extract flight id (REG/, SID/, RF..., RA..., numeric SID)
def extract_flight_id_from_text(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    txt = text.upper()
    # REG/xxx or REG xxx, take first comma-separated
    m = re.search(r'\bREG[/\s]*([A-Z0-9\-\_\,]+)', txt)
    if m:
        v = m.group(1).split(',')[0].strip()
        if v and v not in {'TITLE','IDEP','IARR','ADEP','ARR','DEP'}:
            return v
    # SID (some rows contain SID/777...)
    m2 = re.search(r'\bSID/(\d{4,})\b', txt)
    if m2:
        return m2.group(1)
    # try common aircraft codes RFxxx or RA-xxx or alnum combos (fallback)
    m3 = re.search(r'\b([A-Z]{1,3}[-]?[0-9]{2,6}[A-Z0-9]{0,3})\b', txt)
    if m3:
        token = m3.group(1)
        if token not in {'TITLE','IDEP','IARR','ADEP','ARR','DEP','M0000','K0300'}:
            return token
    return None

# 3) parse DOF (date) and ATD/ATA tokens
def parse_dof(txt: Optional[str]) -> Optional[str]:
    if not txt:
        return None
    m = re.search(r'\bDOF[/\s]?(\d{6})\b', txt)
    if m:
        return m.group(1)
    return None

def parse_time_token(txt: Optional[str]) -> Optional[str]:
    if not txt:
        return None
    # ATD 0705 or -ATD0705 etc.
    m = re.search(r'\bATD[\s:/-]?(\d{3,4})\b', txt)
    if m:
        hhmm = m.group(1)
        if len(hhmm) == 3:
            hh = int(hhmm[0])
            mm = int(hhmm[1:])
        else:
            hh = int(hhmm[:2]); mm = int(hhmm[2:])
        if 0 <= hh < 24 and 0 <= mm < 60:
            return f"{hh:02d}:{mm:02d}"
    m2 = re.search(r'\bATA[\s:/-]?(\d{3,4})\b', txt)
    if m2:
        hhmm = m2.group(1)
        if len(hhmm) == 3:
            hh = int(hhmm[0]); mm = int(hhmm[1:])
        else:
            hh = int(hhmm[:2]); mm = int(hhmm[2:])
        if 0 <= hh < 24 and 0 <= mm < 60:
            return f"{hh:02d}:{mm:02d}"
    # fallback: some rows include just time like -ZZZZ0705 line; pick 4 digits
    m3 = re.search(r'\b(\d{4})\b', txt)
    if m3:
        hhmm = m3.group(1)
        hh = int(hhmm[:2]); mm = int(hhmm[2:])
        if 0 <= hh < 24 and 0 <= mm < 60:
            return f"{hh:02d}:{mm:02d}"
    return None

def combine_dof_time_iso(dof6: Optional[str], hhmm: Optional[str]) -> Optional[str]:
    """
    dof6: DDMMYY
    hhmm: 'HH:MM'
    returns ISO zulu 'YYYY-MM-DDTHH:MM:00Z' or None
    """
    if not dof6:
        return None
    dof6 = re.sub(r'\D','', dof6)
    if len(dof6) != 6:
        return None
    dd = int(dof6[0:2]); mm = int(dof6[2:4]); yy = int(dof6[4:6])
    year = 2000 + yy
    hh = 0; minute = 0
    if hhmm:
        try:
            hh, minute = map(int, hhmm.split(':'))
        except Exception:
            hh, minute = 0, 0
    try:
        dt = datetime(year, mm, dd, hh, minute, tzinfo=timezone.utc)
        return dt.isoformat().replace('+00:00','Z')
    except Exception:
        return None

# 4) fingerprint
def make_fingerprint(flight_id: Optional[str], start_time: Optional[str],
                     start_lat, start_lon) -> str:
    a = (flight_id or "") + "|" + (start_time or "") + "|" + (str(start_lat) if start_lat is not None else "") + "|" + (str(start_lon) if start_lon is not None else "")
    return hashlib.sha256(a.encode('utf-8')).hexdigest()

# -----------------------
# main normalizer
# -----------------------
def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Input: row dict with keys like 'SHR','DEP','ARR','center' (from Excel).
    Output: normalized dict with:
      flight_id, uav_type, start_time (ISO), end_time, duration_seconds,
      start_lat, start_lon, end_lat, end_lon, raw_payload (dict), fingerprint
    """
    # prepare raw_payload: keep strings or None
    raw = {
        'SHR': safe_get_str(row, 'SHR') or safe_get_str(row, 'Shr') or None,
        'DEP': safe_get_str(row, 'DEP') or safe_get_str(row, 'Dep') or None,
        'ARR': safe_get_str(row, 'ARR') or safe_get_str(row, 'Arr') or None,
        'center': safe_get_str(row, 'center') or safe_get_str(row, 'Центр ЕС ОрВД') or None
    }

    # 1) flight_id
    flight_id = None
    for src in (raw.get('DEP'), raw.get('SHR'), raw.get('ARR')):
        fid = extract_flight_id_from_text(src)
        if fid:
            flight_id = fid
            break

    # 2) coordinates: ADEPZ / ADARRZ or compact coords inside SHR or DEP lines
    start_lat = start_lon = end_lat = end_lon = None

    # search in DEP block for ADEPZ / compact coordinates
    deptxt = raw.get('DEP') or ''
    arrtxt = raw.get('ARR') or ''
    shrtxt = raw.get('SHR') or ''

    # helper to search ADEPZ/ADARRZ and DEP/ARR with pattern like DEP/5957N02905E or ADEPZ 5957N02905E
    def find_coord_in_text(txt):
        if not txt:
            return None
        # ADEPZ or ADARRZ
        m = re.search(r'\bADEPZ[\s/:]*([0-9NSEWnsew\ \-]+)', txt)
        if m:
            c = m.group(1).strip()
            r = parse_compact_coord(c)
            if r:
                return r
        m2 = re.search(r'\bADARRZ[\s/:]*([0-9NSEWnsew\ \-]+)', txt)
        if m2:
            r = parse_compact_coord(m2.group(1).strip())
            if r:
                return r
        # DEP/xxxxx or ADARR/xxxxx
        m3 = re.search(r'(?:DEP|ADARR|ADEP|ADARRZ|DEP/)\s*[/:]*\s*([0-9]{4,15}[NSEWnsew0-9]*)', txt)
        # fallback: find first compact-looking token in text
        if not m3:
            tokens = re.findall(r'([0-9]{4,15}[NSEWnsew])', txt)
            if tokens:
                m3 = (None, tokens[0])  # trick to return value below
        if m3:
            token = m3.group(1) if hasattr(m3, 'group') else m3[1]
            r = parse_compact_coord(token)
            if r:
                return r
        # fallback: inside RMK lines there might be plain coordinates like 593600N0291600E - try find any
        found = re.findall(r'(\d{4,6}[NSns]\d{5,7}[EWew])', txt)
        for cand in found:
            r = parse_compact_coord(cand)
            if r:
                return r
        return None

    dep_coord = find_coord_in_text(deptxt)
    arr_coord = find_coord_in_text(arrtxt)
    shr_coord = find_coord_in_text(shrtxt)

    if dep_coord:
        start_lat, start_lon = dep_coord
    elif shr_coord:
        start_lat, start_lon = shr_coord

    if arr_coord:
        end_lat, end_lon = arr_coord
    elif shr_coord:
        # if only SHR polygon or center included, use it for both start/end if needed
        end_lat, end_lon = shr_coord

    # 3) times
    dof = parse_dof(shrtxt) or parse_dof(deptxt) or parse_dof(arrtxt)
    atd = parse_time_token(deptxt) or parse_time_token(shrtxt)
    ata = parse_time_token(arrtxt) or None

    start_time = combine_dof_time_iso(dof, atd)
    end_time = combine_dof_time_iso(dof, ata)

    # 4) uav_type: try detect TYP/ or words like BLA / AER / SHAR
    uav_type = None
    for block in (shrtxt, deptxt, arrtxt):
        if not block:
            continue
        m = re.search(r'\bTYP/([A-Z0-9\-\_]+)', block.upper())
        if m:
            uav_type = m.group(1)
            break
        if re.search(r'\bBLA\b', block.upper()):
            uav_type = 'BLA'
            break
        if re.search(r'\bAER\b', block.upper()):
            uav_type = 'AER'
            break

    # 5) duration_seconds - if both times present
    duration_seconds = None
    if start_time and end_time:
        try:
            dt1 = datetime.fromisoformat(start_time.replace('Z','+00:00'))
            dt2 = datetime.fromisoformat(end_time.replace('Z','+00:00'))
            delta = (dt2 - dt1).total_seconds()
            duration_seconds = int(delta) if delta >= 0 else None
        except Exception:
            duration_seconds = None

    # 6) raw_payload keep original strings and parsed snippets
    raw_payload = {
        'SHR': safe_get_str(row, 'SHR'),
        'DEP': safe_get_str(row, 'DEP'),
        'ARR': safe_get_str(row, 'ARR'),
        'center': safe_get_str(row, 'center')
    }

    # 7) fingerprint
    fingerprint = make_fingerprint(flight_id, start_time, start_lat, start_lon)

    out = {
        'flight_id': flight_id,
        'uav_type': uav_type,
        'start_time': start_time,
        'end_time': end_time,
        'duration_seconds': duration_seconds,
        'start_lat': start_lat,
        'start_lon': start_lon,
        'end_lat': end_lat,
        'end_lon': end_lon,
        'time_token': atd,
        'raw_payload': raw_payload,
        'fingerprint': fingerprint
    }

    # ensure no NaN floats (convert to None)
    for k,v in list(out.items()):
        if isinstance(v, float) and math.isnan(v):
            out[k] = None

    return out

# quick test-run if invoked directly
if __name__ == "__main__":
    sample = {
        'SHR': "(SHR-ZZZZZ\n-ZZZZ0705\n-DEP/5957N02905E DOF/250201 ... SID/7772187998)",
        'DEP': "-TITLE IDEP\n-SID 7772187998\n-ATD 0705\n-ADEP ZZZZ\n-ADEPZ 5957N02905E\n",
        'ARR': None,
        'center': "Санкт-Петербургский"
    }
    print(json.dumps(normalize_row(sample), indent=2, ensure_ascii=False))
