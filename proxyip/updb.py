import json
from pathlib import Path

DATA_SOURCES = {
    "ipdb": "no",
    "ipdb-cm": "yes"
}

DATA_FILE = "proxyip/data.json"

def load_json_file(file_path):
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_json_file(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_existing_entries(main_data):
    existing = set()
    for entry in main_data:
        key = f"{entry['ip']}:{entry['port']}"
        existing.add(key)
    return existing

def merge_data():
    main_data = load_json_file(DATA_FILE)
    print(f"Loaded {len(main_data)} entries from main data.json")
    
    existing_entries = get_existing_entries(main_data)
    total_new = 0
    
    for db_name, enabled in DATA_SOURCES.items():
        if enabled != "yes":
            print(f"\nSkipping {db_name} (disabled)")
            continue
        
        print(f"\nProcessing {db_name}...")
        source_file = BASE_DIR / db_name / "data.json"
        
        if not source_file.exists():
            print(f"  File not found: {source_file}")
            continue
        
        source_data = load_json_file(source_file)
        print(f"  Loaded {len(source_data)} entries from {db_name}/data.json")
        
        new_entries = 0
        for entry in source_data:
            key = f"{entry['ip']}:{entry['port']}"
            
            if key not in existing_entries:
                main_data.append(entry)
                existing_entries.add(key)
                new_entries += 1
        
        print(f"  Added {new_entries} new entries from {db_name}")
        total_new += new_entries
    
    save_json_file(DATA_FILE, main_data)
    print(f"\nTotal new entries added: {total_new}")
    print(f"Total entries in main data.json: {len(main_data)}")

if __name__ == "__main__":
    merge_data()
