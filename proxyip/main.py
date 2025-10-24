# Modified by user request - Proxy checker with JSON output
import socket
import ssl
import json
import concurrent.futures
import re

IP_RESOLVER = "speed.cloudflare.com"
PATH_RESOLVER = "/meta"
PROXY_FILE = "proxyip/data.txt"      # Input: each line is "ip:port"
OUTPUT_FILE = "proxyip/data.json"       # Output: JSON array

# Thread-safe list to collect results
active_proxies = []

def check(host, path, proxy=None):
    """Send HTTPS request to host/path, optionally via proxy (dict with 'ip', 'port')."""
    payload = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.10240\r\n"
        "Connection: close\r\n\r\n"
    )

    target_ip = proxy["ip"] if proxy else host
    target_port = int(proxy["port"]) if proxy else 443

    conn = None
    try:
        ctx = ssl.create_default_context()
        conn = socket.create_connection((target_ip, target_port), timeout=5)
        conn = ctx.wrap_socket(conn, server_hostname=host)

        conn.sendall(payload.encode())

        resp = b""
        while True:
            data = conn.recv(4096)
            if not data:
                break
            resp += data

        resp_str = resp.decode("utf-8", errors="ignore")
        if "\r\n\r\n" not in resp_str:
            return {}
        _, body = resp_str.split("\r\n\r\n", 1)

        return json.loads(body)
    except (json.JSONDecodeError, ValueError):
        pass  # Invalid JSON
    except (socket.error, ssl.SSLError, OSError):
        pass  # Connection issues
    finally:
        if conn:
            conn.close()
    return {}

def parse_proxy_line(line):
    """Parse 'ip:port' line into dict."""
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if ':' not in line:
        return None
    ip, port_str = line.rsplit(':', 1)
    try:
        port = int(port_str)
        socket.inet_aton(ip)  # Basic IP validation
        return {"ip": ip, "port": port}
    except (ValueError, OSError):
        return None

def process_proxy_line(line):
    proxy = parse_proxy_line(line)
    if not proxy:
        print(f"Invalid proxy line: {line.strip()}")
        return

    ip = proxy["ip"]
    port = proxy["port"]

    try:
        # Get origin IP info (direct connection)
        ori = check(IP_RESOLVER, PATH_RESOLVER)

        # Get proxy IP info (via proxy)
        pxy = check(IP_RESOLVER, PATH_RESOLVER, proxy)

        if ori and pxy and ori.get("clientIp") != pxy.get("clientIp"):
            country = pxy.get("country", "").strip()
            as_org = pxy.get("asOrganization", "").strip()

            # Only include if country and as_org are present (optional: adjust as needed)
            if country and as_org:
                result = {
                    "ip": ip,
                    "port": port,
                    "code": country,
                    "asn": as_org
                }
                active_proxies.append(result)
                print(f"✅ LIVE: {ip}:{port} → {country} | {as_org}")
            else:
                print(f"⚠️  LIVE but missing info: {ip}:{port}")
        else:
            print(f"❌ DEAD: {ip}:{port}")

    except Exception as e:
        print(f"Error processing {ip}:{port} – {e}")

# --- Main Execution ---
if __name__ == "__main__":
    # Clear output file content (optional, since we overwrite at end)
    print(f"Loading proxies from {PROXY_FILE}...")

    try:
        with open(PROXY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ File not found: {PROXY_FILE}")
        exit(1)

    print(f"Found {len(lines)} lines. Starting concurrent check (max 20 workers)...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(process_proxy_line, line) for line in lines]
        concurrent.futures.wait(futures)

    # Write final JSON output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        json.dump(active_proxies, f_out, indent=2, ensure_ascii=False)

    print(f"\n✅ Done! {len(active_proxies)} live proxies saved to {OUTPUT_FILE}")