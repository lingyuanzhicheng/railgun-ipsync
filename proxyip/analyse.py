import json
import os
from collections import defaultdict

input_file = "proxyip/data.json"
output_dir = "proxyip/data"

os.makedirs(output_dir, exist_ok=True)

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ File not found: {input_file}")
    exit(1)

country_groups = defaultdict(list)
for proxy in data:
    code = proxy.get('code', '')
    if code:
        country_groups[code].append(proxy)

for code, proxies in country_groups.items():
    filename = f"{code}.json"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(proxies, f, indent=2, ensure_ascii=False)

count_data = {}
for code, proxies in country_groups.items():
    count_data[code.upper()] = len(proxies)

count_file = "proxyip/count.json"
with open(count_file, 'w', encoding='utf-8') as f:
    json.dump(count_data, f, indent=2, ensure_ascii=False)

print(f"✅ Grouped proxies into {len(country_groups)} country files")
print(f"✅ Generated count.json with {len(count_data)} countries")
for code, count in count_data.items():
    print(f"  {code}: {count} proxies")