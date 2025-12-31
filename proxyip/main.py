import json
import os
import requests
from pathlib import Path

DATA_FILE = "proxyip/data.json"
API_BASE = "https://check.moesite.workers.dev/check"
TOKEN = os.getenv("TOKEN")

def load_data():
    data_path = Path(DATA_FILE)
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    data_path = Path(DATA_FILE)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_proxy(ip, port):
    url = f"{API_BASE}?proxyip={ip}:{port}&token={TOKEN}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('success', False)
    except Exception as e:
        print(f"    Error checking {ip}:{port}")
        return False

def main():
    data = load_data()
    print(f"Loaded {len(data)} entries from data.json")
    
    valid_entries = []
    removed_count = 0
    
    for entry in data:
        ip = entry.get('ip')
        port = entry.get('port')
        
        print(f"Checking {ip}:{port}...")
        is_valid = check_proxy(ip, port)
        
        if is_valid:
            valid_entries.append(entry)
            print(f"    Valid - keeping")
        else:
            removed_count += 1
            print(f"    Invalid - removing")
    
    save_data(valid_entries)
    print(f"\nTotal checked: {len(data)}")
    print(f"Valid entries: {len(valid_entries)}")
    print(f"Removed entries: {removed_count}")
    print(f"Results saved in data.json")

if __name__ == "__main__":
    main()
