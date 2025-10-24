import os
import re
import time
import json
import requests
from typing import List, Set, Dict

# 确保输出目录存在
os.makedirs(os.path.dirname(__file__), exist_ok=True)

USER_AGENT = 'Mozilla/5.0 (compatible; IP-Collector/1.0)'
SESSION = requests.Session()
SESSION.headers.update({'User-Agent': USER_AGENT})

def extract_ips(text: str) -> List[str]:
    ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)
    valid_ips = [ip for ip in ips if all(0 <= int(octet) <= 255 for octet in ip.split('.'))]
    unique_sorted = sorted(set(valid_ips), key=lambda ip: tuple(map(int, ip.split('.'))))
    return unique_sorted

def fetch_direct(url: str) -> str:
    resp = SESSION.get(url, timeout=10)
    resp.raise_for_status()
    return resp.text

def fetch_via_phantomjs_cloud(url: str) -> str:
    api_url = 'https://PhantomJsCloud.com/api/browser/v2/a-demo-key-with-low-quota-per-ip-address/'
    payload = {"url": url, "renderType": "html"}
    resp = SESSION.post(api_url, json=payload, timeout=20)
    resp.raise_for_status()
    return resp.text

def save_ips_to_file(ips: List[str], filename: str):
    filepath = os.path.join(os.path.dirname(__file__), filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ips))
    print(f"✅ 已保存 {len(ips)} 个 IP 到 {filename}")

def aggregate_all_ips_to_data_txt():
    ip_set: Set[str] = set()
    dir_path = os.path.dirname(__file__)
    for file in os.listdir(dir_path):
        if file.endswith('.txt') and file != 'data.txt':
            filepath = os.path.join(dir_path, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        ip = line.strip()
                        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
                            if all(0 <= int(octet) <= 255 for octet in ip.split('.')):
                                ip_set.add(ip)
            except Exception as e:
                print(f"⚠️ 读取文件 {file} 时出错: {e}")

    sorted_ips = sorted(ip_set, key=lambda ip: tuple(map(int, ip.split('.'))))
    data_file = os.path.join(dir_path, 'data.txt')
    with open(data_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted_ips))
    print(f"✅ 聚合完成：共 {len(sorted_ips)} 个唯一 IP 已写入 data.txt")

def enrich_ips_with_geo_info():
    """第三步：调用 ip-api.com 获取地理位置信息，生成 data.json"""
    dir_path = os.path.dirname(__file__)
    data_txt = os.path.join(dir_path, 'data.txt')
    data_json = os.path.join(dir_path, 'data.json')

    if not os.path.exists(data_txt):
        print("❌ data.txt 不存在，无法进行地理信息增强。")
        return

    with open(data_txt, 'r', encoding='utf-8') as f:
        ips = [line.strip() for line in f if line.strip()]

    results: List[Dict[str, str]] = []
    total = len(ips)
    print(f"🌍 正在为 {total} 个 IP 查询地理位置信息（每秒最多1个请求）...")

    for i, ip in enumerate(ips, 1):
        try:
            print(f"  ({i}/{total}) 查询 {ip} ...")
            url = f"http://ip-api.com/json/{ip}?lang=zh-CN"
            resp = SESSION.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "success":
                    results.append({
                        "ip": ip,
                        "country": data.get("country", ""),
                        "regionName": data.get("regionName", ""),
                        "city": data.get("city", "")
                    })
                else:
                    print(f"    ⚠️ 查询失败: {data.get('message', 'Unknown error')}")
            else:
                print(f"    ⚠️ HTTP {resp.status_code}")
        except Exception as e:
            print(f"    ❌ 请求异常: {e}")

        # 遵守免费 API 限流（建议 ≥1.4 秒间隔）
        if i < total:
            time.sleep(1.5)

    # 保存为 JSON
    with open(data_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ 地理信息增强完成，共 {len(results)} 条记录已写入 data.json")

# 数据源定义
SOURCES = [
    ("https://ipdb.api.030101.xyz/?type=bestcf&country=true", "030101.txt", "direct"),
    ("https://ip.164746.xyz", "164746.txt", "direct"),
    ("https://stock.hostmonit.com/CloudFlareYes", "CloudFlareYes.txt", "phantomjs"),
    ("https://ip.haogege.xyz", "haogege.txt", "direct"),
    ("https://api.uouin.com/cloudflare.html", "uouin", "direct"),
    ("https://www.wetest.vip/page/cloudflare/address_v4.html", "wetest.txt", "direct"),
    ("hhttps://vps789.com/public/sum/cfIpApi", "vps789.txt", "direct"),
]

def main():
    # 第一步：抓取各源 IP
    for url, filename, strategy in SOURCES:
        try:
            print(f"📡 正在抓取 {url} ({strategy}) ...")
            if strategy == "direct":
                html = fetch_direct(url)
            elif strategy == "phantomjs":
                html = fetch_via_phantomjs_cloud(url)
            else:
                raise ValueError(f"未知策略: {strategy}")

            ips = extract_ips(html)
            save_ips_to_file(ips, filename)

        except Exception as e:
            print(f"❌ 抓取失败 {url}: {e}")

    # 第二步：聚合到 data.txt
    print("\n🔄 正在聚合所有 IP 到 data.txt...")
    aggregate_all_ips_to_data_txt()

    # 第三步：地理信息增强 → data.json
    print("\n📍 正在执行地理信息增强（调用 ip-api.com）...")
    enrich_ips_with_geo_info()

if __name__ == "__main__":
    main()