# analyze_sample.py
import json
import itertools

# Загрузка JSON
with open("sample_parsed.json", encoding="utf-8") as f:
    data = json.load(f)

# Фильтрация по категориям
no_start = [r for r in data if r.get('start_lat') is None or r.get('start_lon') is None]
no_end = [r for r in data if r.get('end_lat') is None or r.get('end_lon') is None]
no_fid = [r for r in data if not r.get('flight_id')]

# Статистика
print(f"Total records: {len(data)}")
print(f"No start coords: {len(no_start)} ({len(no_start)/len(data)*100:.1f}%)")
print(f"No end coords: {len(no_end)} ({len(no_end)/len(data)*100:.1f}%)")
print(f"No flight_id: {len(no_fid)} ({len(no_fid)/len(data)*100:.1f}%)")

# Примеры
def show_examples(title, lst):
    print(f"\nExamples ({title}):")
    for r in itertools.islice(lst, 10):
        print(json.dumps(r, ensure_ascii=False, indent=2))

show_examples("no start coords", no_start)
show_examples("no end coords", no_end)
show_examples("no flight_id", no_fid)
