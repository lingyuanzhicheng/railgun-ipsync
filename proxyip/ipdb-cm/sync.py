import json
import os
import requests
from pathlib import Path

IATA_FILE = "proxyip/ipdb.v2/iata.json"
DATA_FILE = "proxyip/ipdb.v2/data.txt"
API_BASE = "https://check.moesite.workers.dev/resolve"
TOKEN = os.getenv("TOKEN")

def load_existing_ips():
    data_path = Path(DATA_FILE)
    if data_path.exists():
        with open(data_path, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_ips(new_ips):
    data_path = Path(DATA_FILE)
    with open(data_path, 'a', encoding='utf-8') as f:
        for ip in new_ips:
            f.write(ip + '\n')

def resolve_domain(domain):
    url = f"{API_BASE}?domain={domain}&token={TOKEN}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get('ips', [])
    except Exception as e:
        print(f"    Error resolving {domain}")
        return []

def main():
    if not TOKEN:
        print("Error: PROXYIP_TOKEN environment variable is not set")
        return
    
    with open(IATA_FILE, 'r', encoding='utf-8') as f:
        iata_data = json.load(f)
    
    existing_ips = load_existing_ips()
    total_new_ips = 0
    
    for country_code, iata_codes in iata_data.items():
        print(f"\nProcessing country: {country_code}")
        
        country_domain = f"proxyip.{country_code}.cmliussss.net"
        print(f"  Resolving {country_domain}...")
        country_ips = resolve_domain(country_domain)
        
        new_country_ips = [ip for ip in country_ips if ip not in existing_ips]
        if new_country_ips:
            save_ips(new_country_ips)
            existing_ips.update(new_country_ips)
            total_new_ips += len(new_country_ips)
            print(f"    Added {len(new_country_ips)} new IPs from country domain")
        else:
            print(f"    No new IPs from country domain")
        
        for iata_code in iata_codes:
            iata_domain = f"{iata_code}.proxyip.cmliussss.net"
            print(f"  Resolving {iata_domain}...")
            iata_ips = resolve_domain(iata_domain)
            
            new_iata_ips = [ip for ip in iata_ips if ip not in existing_ips]
            if new_iata_ips:
                save_ips(new_iata_ips)
                existing_ips.update(new_iata_ips)
                total_new_ips += len(new_iata_ips)
                print(f"    Added {len(new_iata_ips)} new IPs from IATA domain")
            else:
                print(f"    No new IPs from IATA domain")
    
    print(f"\nTotal new IPs added: {total_new_ips}")
    print(f"Results saved in data.txt: {len(existing_ips)}")

if __name__ == "__main__":
    main()
