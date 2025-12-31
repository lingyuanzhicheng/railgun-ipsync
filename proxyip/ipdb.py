import json
from pathlib import Path
import shutil

DATA_FILE = "proxyip/data.json"
OUTPUT_DIR = "proxyip/data"

def load_data():
    data_path = Path(DATA_FILE)
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def clear_output_dir():
    output_path = Path(OUTPUT_DIR)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"Directory initialization: {OUTPUT_DIR}")

def classify_by_code(data):
    classified = {}
    for entry in data:
        code = entry.get('code')
        if code:
            if code not in classified:
                classified[code] = []
            classified[code].append(entry)
    return classified

def save_classified_data(classified):
    output_path = Path(OUTPUT_DIR)
    total_files = 0
    total_entries = 0
    
    for code, entries in classified.items():
        file_path = output_path / f"{code}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"  Saved {len(entries)} entries to {code}.json")
        total_files += 1
        total_entries += len(entries)
    
    return total_files, total_entries

def main():
    data = load_data()
    print(f"Loaded {len(data)} entries from data.json")
    
    clear_output_dir()
    
    classified = classify_by_code(data)
    print(f"\nClassified into {len(classified)} country codes")
    
    total_files, total_entries = save_classified_data(classified)
    
    print(f"\nTotal files created: {total_files}")
    print(f"Total entries saved: {total_entries}")

if __name__ == "__main__":
    main()
