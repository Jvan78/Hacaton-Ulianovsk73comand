# backend/app/parser.py
import re
import hashlib
from typing import Optional, Tuple, Dict, Any
import datetime
import math
import re
from datetime import datetime, timezone, timedelta
# --- вспомогательные парсеры ---
def parse_compact_coord(s: str):
    """
    Примеры:
      "5957N02905E" -> (59 + 57/60, 29 + 05/60)
      "440846N0430829E" -> (44 + 08/60 + 46/3600, 43 + 08/60 + 29/3600)
    """
    if not s or not isinstance(s, str):
        return None
    s = s.strip().upper()
    # убрать лишние символы
    s = s.replace(" ", "")
    m = re.match(r'(\d{2,4})(\d{2})(N|S)(\d{2,3})(\d{2})(E|W)', s)
    if m:
        lat_deg = int(m.group(1)[:-2]) if len(m.group(1))>2 else int(m.group(1)[:len(m.group(1))-2])
        lat_min = int(m.group(2))
        lat_hem = m.group(3)
        lon_deg = int(m.group(4))
        lon_min = int(m.group(5))
        lon_hem = m.group(6)
        lat = lat_deg + lat_min/60.0
        lon = lon_deg + lon_min/60.0
        if lat_hem == 'S':
            lat = -lat
        if lon_hem == 'W':
            lon = -lon
        return (round(lat, 8), round(lon, 8))
    # попытка для форматов с секундами (6+ digits deg+min+sec)
    m2 = re.match(r'(\d{2})(\d{2})(\d{2})(N|S)(\d{2,3})(\d{2})(\d{2})(E|W)', s)
    if m2:
        lat = int(m2.group(1)) + int(m2.group(2))/60 + int(m2.group(3))/3600
        lon = int(m2.group(5)) + int(m2.group(6))/60 + int(m2.group(7))/3600
        if m2.group(4) == 'S':
            lat = -lat
        if m2.group(8) == 'W':
            lon = -lon
        return (round(lat,8), round(lon,8))
    return None

# --- extract time tokens and combine with DOF
def parse_time_token(hhmm: str):
    if not hhmm:
        return None
    hhmm = hhmm.strip().replace(':','')
    if not re.match(r'^\d{3,4}$', hhmm):
        return None
    if len(hhmm) == 3:
        hh = int(hhmm[0])
        mm = int(hhmm[1:])
    else:
        hh = int(hhmm[:2])
        mm = int(hhmm[2:])
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None
    return (hh, mm)

def combine_dof_and_time(dof_str, hhmm_str):
    """
    dof_str examples: 250201 (DDMMYY)
    returns ISO string 'YYYY-MM-DDTHH:MM:00Z' (UTC) if possible
    - If DOF absent, returns None
    """
    if not dof_str:
        return None
    dof_str = re.sub(r'\D','', str(dof_str))
    if len(dof_str) != 6:
        return None
    dd = int(dof_str[0:2]); mm = int(dof_str[2:4]); yy = int(dof_str[4:6])
    # интерпретация года: 20xx для yy<70, else 19xx unlikely -> use 2000+
    year = 2000 + yy
    t = parse_time_token(hhmm_str)
    if t:
        hh,mi = t
    else:
        hh,mi = 0,0
    try:
        dt = datetime(year, mm, dd, hh, mi, tzinfo=timezone.utc)
        return dt.isoformat().replace('+00:00','Z')
    except Exception:
        return None

# --- extract flight id (улучшенный)
def extract_flight_id_from_text(text: str):
    if not text:
        return None
    txt = text.upper()
    # REG/ pattern
    m = re.search(r'\bREG[/\s]?([A-Z0-9\-,]+)', txt)
    if m:
        v = m.group(1).split(',')[0].strip()
        if v and v not in {"TITLE","IDEP","IARR","ADEP","ARR","DEP","PAP","RMK","SHR","DOF","DEST","SID"}:
            return v
    m = re.search(r'\bSID/(\d+)\b', txt)
    if m:
        return m.group(1)
    # RF..., RA-, alnum with digits
    m2 = re.search(r'\b([A-Z]{1,3}[-]?[0-9]{2,6}[A-Z0-9]{0,3})\b', txt)
    if m2:
        tok = m2.group(1)
        if tok not in {"TITLE","IDEP","IARR","ADEP"}:
            return tok
    return None

# распознаёт compact coord форматы:
# lat: DDMM or DDMMSS + N/S
# lon: DDDMM or DDDMMSS + E/W
# примеры: 5957N02905E, 440846N0430829E
_COMPACT_RE = re.compile(r'(?P<lat>\d{4,6}[NS])(?P<lon>\d{5,7}[EW])')

def parse_compact_coord(s: str) -> Optional[Tuple[float, float]]:
    """Парсит компактные координаты и возвращает (lat, lon) в десятичных градусах."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip().replace(" ", "")
    m = _COMPACT_RE.search(s)
    if not m:
        return None
    lat_raw = m.group('lat')[:-1]
    lat_dir = m.group('lat')[-1]
    lon_raw = m.group('lon')[:-1]
    lon_dir = m.group('lon')[-1]

    def _to_deg(digits: str, is_lat: bool) -> float:
        # lat: 4 (DDMM) or 6 (DDMMSS)
        # lon: 5 (DDDMM) or 7 (DDDMMSS)
        if is_lat:
            if len(digits) == 4:
                deg = int(digits[:2]); minute = int(digits[2:4]); sec = 0
            elif len(digits) == 6:
                deg = int(digits[:2]); minute = int(digits[2:4]); sec = int(digits[4:6])
            else:
                return float('nan')
        else:
            if len(digits) == 5:
                deg = int(digits[:3]); minute = int(digits[3:5]); sec = 0
            elif len(digits) == 7:
                deg = int(digits[:3]); minute = int(digits[3:5]); sec = int(digits[5:7])
            else:
                return float('nan')
        return deg + minute / 60.0 + sec / 3600.0

    lat = _to_deg(lat_raw, True)
    lon = _to_deg(lon_raw, False)
    if math.isnan(lat) or math.isnan(lon):
        return None
    if lat_dir == 'S':
        lat = -lat
    if lon_dir == 'W':
        lon = -lon
    return lat, lon

_time_re = re.compile(r'(?:\bATD\b|\bATA\b)[:\s\/-]?(\d{3,4})', re.IGNORECASE)
_time_token_re = re.compile(r'\b(\d{3,4})\b')

def parse_time_token(block: str) -> Optional[str]:
    """Ищет ATD/ATA в тексте и возвращает ISO-строку времени (HH:MM) или None."""
    if not block or not isinstance(block, str):
        return None
    m = _time_re.search(block)
    if not m:
        # запасной вариант: найти просто 4-значное число в DEP/ARR (ATD/ATA могли быть пропущены)
        m2 = _time_token_re.search(block)
        if not m2:
            return None
        tok = m2.group(1)
    else:
        tok = m.group(1)
    tok = tok.zfill(4)  # '600' -> '0600', '700'-> '0700'
    hh = tok[:2]; mm = tok[2:4]
    try:
        # возвращаем только время в строковом формате YYYY-MM-DDT HH:MM? Лучше - HH:MM (чтобы main.py мог обработать)
        return f"{hh}:{mm}"
    except Exception:
        return None

def extract_flight_id_from_text(text: str) -> Optional[str]:
    """Извлекает корректный flight id. Игнорируем служебные токены как TITLE/IDEP/IARR/ZZZZ."""
    if not text or not isinstance(text, str):
        return None
    txt = text.upper()

    # blacklist слов, которые не должны стать flight_id
    blacklist = {"TITLE","IDEP","IARR","ADEP","ARR","DEP","PAP","RMK","SHR","DOF","DEST","SID"}

    # 1) REG/xxxxx (включая REG/00724,REG00725) — берём первый приемлемый токен
    m = re.search(r'\bREG[/\s]?([A-Z0-9\-,]+)', txt, re.IGNORECASE)
    if m:
        v = m.group(1)
        v = re.split(r'[,\s/]+', v)[0]
        v = v.strip()
        if v and v.upper() not in blacklist:
            return v

    # 2) SID/(\d+) — допустим как flight id
    m = re.search(r'\bSID/(\d+)\b', txt, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    # 3) явные alnum-хеши с букв+цифрами (например RF37362, RA-0938G, RF-123)
    #    условие: длина > 2, содержит букву и цифру, и не в blacklist.
    tokens = re.findall(r'\b[A-Z0-9\-]{2,20}\b', txt)
    for t in tokens:
        tt = t.strip().upper()
        if tt in blacklist:
            continue
        # должен содержать букву и цифру или дефис+цифры/буквы
        if re.search(r'[A-Z]', tt) and re.search(r'[0-9]', tt):
            return tt

    # 4) fallback: первое слово не из blacklist (только если это явно не TITLE/IDEP)
    for t in tokens:
        if t.strip().upper() not in blacklist:
            return t.strip()

    return None

def safe_str(x):
    if x is None:
        return None
    return str(x)

def make_fingerprint(flight_id: Optional[str], start_time: Optional[str], start_lat: Optional[float], start_lon: Optional[float]) -> str:
    s = (flight_id or "") + "|" + (start_time or "") + "|" + (str(start_lat) if start_lat is not None else "") + "|" + (str(start_lon) if start_lon is not None else "")
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

# --- Основная функция нормализации одной строки (row) ---
def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    row: словарь с колонками из Excel (ключи точно как в pandas row.to_dict()).
    Возвращает нормализованный dict с полями:
      flight_id, start_lat, start_lon, end_lat, end_lon, start_time, end_time, time_token, uav_type, raw_payload, fingerprint
    """
    # делаем безопасные значения
    def _get(key):
        # ищем ключи без учёта регистра (обычно колонки "SHR","DEP","ARR","center")
        for k in (key, key.lower(), key.upper()):
            if k in row and row[k] is not None and (not (isinstance(row[k], float) and math.isnan(row[k]))):
                return row[k]
        # попытка: найти by substring
        for k in row.keys():
            if k.lower().strip() == key.lower().strip():
                val = row[k]
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    return None
                return val
        return None

    shr = _get("SHR") or _get("shr") or ""
    dep = _get("DEP") or _get("dep") or ""
    arr = _get("ARR") or _get("arr") or ""
    center = _get("center") or _get("Center") or _get("Центр") or None

    raw_payload = {"SHR": safe_str(shr), "DEP": safe_str(dep), "ARR": safe_str(arr), "center": safe_str(center)}

    # flight_id
    flight_id = None
    # попробуем из DEP/ARR блоков сначала
    for block in (dep, arr, shr):
        if block:
            fid = extract_flight_id_from_text(str(block))
            if fid:
                flight_id = fid
                break

    # парсим координаты
    start_coord = None
    end_coord = None

    # 1) явные поля ADEPZ / ADARRZ внутри DEP/ARR блоков
    def find_adepz(block):
        if not block or not isinstance(block, str):
            return None
        # ищем "ADEPZ 5957N02905E" или "-ADEPZ 5957N02905E" или "ADEPZ5957N02905E"
        m = re.search(r'ADEPZ[:\s\/-]?([0-9NSWEnswe]+)', block, re.IGNORECASE)
        if m:
            return parse_compact_coord(m.group(1))
        # AD? alternative patterns e.g. "ADEPZ 440846N0430829E"
        m2 = _COMPACT_RE.search(block)
        if m2:
            return parse_compact_coord(m2.group(0))
        return None

    start_coord = find_adepz(dep) or find_adepz(shr)
    end_coord = find_adepz(arr) or find_adepz(shr)

    # 2) если не найдено — искать в RMK/тексте компактные координаты (первые два найденных считаем start/end)
    if not start_coord or not end_coord:
        # найдём все в SHR/DEP/ARR вместе
        combined = " ".join([str(x) for x in (shr, dep, arr) if x])
        all_coords = list(_COMPACT_RE.finditer(combined))
        if all_coords:
            # преобразуем все найденные в пары lat/lon
            parsed_coords = []
            for mm in all_coords:
                parsed = parse_compact_coord(mm.group(0))
                if parsed:
                    parsed_coords.append(parsed)
            if parsed_coords:
                if not start_coord:
                    start_coord = parsed_coords[0]
                if not end_coord:
                    if len(parsed_coords) >= 2:
                        end_coord = parsed_coords[1]
                    else:
                        end_coord = parsed_coords[0]

    # 3) parse times ATD/ATA
    start_time = parse_time_token(dep) or parse_time_token(shr)
    end_time = parse_time_token(arr) or parse_time_token(shr)

    # 4) fallback: if start_coord still None but DEP contains pattern "DEP/5957N02905E" etc
    if not start_coord:
        m = re.search(r'DEP[:\s\/-]*([0-9NSWEnswe]+)', str(dep))
        if m:
            start_coord = parse_compact_coord(m.group(1))
    if not end_coord:
        m = re.search(r'ADARRZ[:\s\/-]*([0-9NSWEnswe]+)', str(arr))
        if m:
            end_coord = parse_compact_coord(m.group(1))

    # unpack coordinates safely
    start_lat = float(start_coord[0]) if start_coord else None
    start_lon = float(start_coord[1]) if start_coord else None
    end_lat = float(end_coord[0]) if end_coord else None
    end_lon = float(end_coord[1]) if end_coord else None

    # нормализация времени: превращаем '07:05' в ISO-like '2025-09-01T07:05:00Z' не делаем — оставляем HH:MM
    # (main.py ожидает строку, можно переделать при интеграции)
    time_token = start_time or None

    fingerprint = make_fingerprint(flight_id, time_token, start_lat, start_lon)

    normalized = {
        "flight_id": flight_id,
        "start_lat": start_lat,
        "start_lon": start_lon,
        "end_lat": end_lat,
        "end_lon": end_lon,
        "start_time": None,  # оставляем None: main.py ждет start_time в формате ISO timestamp; время токен можно применять отдельно
        "end_time": None,
        "time_token": time_token,
        "uav_type": None,
        "raw_payload": raw_payload,
        "fingerprint": fingerprint
    }
    return normalized

# для быстрой проверки
if __name__ == "__main__":
    tests = [
        "5957N02905E",
        "440846N0430829E",
        "5152N08600E",
        "515252N0860012E",  # пример с секундами (если есть)
        "No coords"
    ]
    for t in tests:
        print(t, "->", parse_compact_coord(t))
