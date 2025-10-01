import json

infn = r".\data\parsed.ndjson"
outfn = r".\data\parsed_normalized.ndjson"

with open(infn, encoding="utf-8") as f, open(outfn, "w", encoding="utf-8") as o:
    for line in f:
        if not line.strip():
            continue
        obj = json.loads(line)
        # экранируем переносы строк в raw_payload.SHR и других текстах
        def escape_text(d):
            for k, v in d.items():
                if isinstance(v, str):
                    d[k] = v.replace("\n", "\\n")
                elif isinstance(v, dict):
                    escape_text(v)
            return d
        obj['raw_payload'] = escape_text(obj.get('raw_payload', {}))
        o.write(json.dumps(obj, ensure_ascii=False) + "\n")

print("Normalized NDJSON saved to parsed_normalized.ndjson")
