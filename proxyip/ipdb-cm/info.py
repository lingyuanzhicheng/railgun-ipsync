import json
import os
import requests
from pathlib import Path

DATA_FILE = "proxyip/ipdb-cm/data.txt"
OUTPUT_FILE = "proxyip/ipdb-cm/data.json"
API_BASE = "https://check.moesite.workers.dev/ip-info"
TOKEN = os.getenv("TOKEN")
PORT = 443

def load_ips():
    data_path = Path(DATA_FILE)
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    return []

def get_ip_info(ip):
    url = f"{API_BASE}?ip={ip}&token={TOKEN}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'error':
            return None
        
        return {
            'countryCode': data.get('countryCode'),
            'org': data.get('org')
        }
    except Exception as e:
        print(f"    Error getting info for {ip}")
        return None

def main():
    ips = load_ips()
    print(f"Loaded {len(ips)} IPs from data.txt")
    
    results = []
    success_count = 0
    error_count = 0
    
    for ip in ips:
        print(f"Processing {ip}...")
        ip_info = get_ip_info(ip)
        
        if ip_info:
            result = {
                'ip': ip,
                'port': PORT,
                'code': ip_info['countryCode'],
                'org': ip_info['org']
            }
            results.append(result)
            success_count += 1
            print(f"    Success: {ip_info['countryCode']} - {ip_info['org']}")
        else:
            error_count += 1
    
    output_path = Path(OUTPUT_FILE)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal processed: {len(ips)}")
    print(f"Successful: {success_count}")
    print(f"Errors/Skipped: {error_count}")
    print(f"Results saved in data.json")

if __name__ == "__main__":
    main()
