# tests/test_parser.py
from app.parser import parse_compact_coord, extract_flight_id_from_text, normalize_row

def test_parse_compact_coord_basic():
    r = parse_compact_coord("5957N02905E")
    assert r is not None
    assert abs(r[0] - (59 + 57/60.0)) < 1e-6
    assert abs(r[1] - (29 + 5/60.0)) < 1e-6

def test_extract_flight_id():
    s = "DOF/250101 OPR/X REG/FL123,FL124 SID/777777"
    fid = extract_flight_id_from_text(s)
    assert fid in ("FL123", "777777")  # accept REG or SID

def test_normalize_row_minimal():
    row = {'SHR':"(SHR-ZZZZZ\n-DOF/250101\nSID/777111)", 'DEP':"-ATD 0705 -ADEP ZZZZ -ADEPZ 5957N02905E"}
    out = normalize_row(row)
    assert out['flight_id'] is not None
    assert out['start_lat'] is not None
