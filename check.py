import json
import requests
import time

INPUT_FILE = "sources.json"
ACTIVE_FILE = "active.json"
DISABLED_FILE = "disabled.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

TIMEOUT = 8


def is_valid_content(text: str) -> bool:
    """判断内容是否真实可用"""
    if not text:
        return False

    t = text.strip().lower()

    # ❌ 明确失效关键词
    bad_keywords = [
        "404", "not found", "expired", "域名", "出售",
        "error", "invalid", "公告", "测试", "closed"
    ]

    if any(k in t for k in bad_keywords):
        return False

    # ❌ 太短基本是空接口
    if len(t) < 50:
        return False

    return True


def check_url(item):
    url = item.get("url", "").strip()

    if not url:
        return False, "empty url"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)

        content = r.text or ""

        # 1️⃣ HTTP检查
        if r.status_code != 200:
            return False, f"status {r.status_code}"

        # 2️⃣ 内容长度检查
        if len(content) < 50:
            return False, "too short"

        # 3️⃣ 内容有效性检查
        if not is_valid_content(content):
            return False, "invalid content"

        # 4️⃣ JSON接口检测（可选增强）
        ctype = r.headers.get("Content-Type", "")
        if "application/json" in ctype:
            try:
                json.loads(content)
            except:
                return False, "broken json"

        return True, "ok"

    except requests.exceptions.RequestException as e:
        return False, str(e)


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    active = []
    disabled = []

    print(f"Total sources: {len(sources)}")

    for i, item in enumerate(sources, 1):
        ok, reason = check_url(item)

        item["reason"] = reason

        if ok:
            active.append(item)
            print(f"[OK] {i}/{len(sources)} {item.get('name','')}")
        else:
            disabled.append(item)
            print(f"[FAIL] {i}/{len(sources)} {reason}")

        time.sleep(0.2)  # 防止请求过快

    with open(ACTIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(active, f, ensure_ascii=False, indent=2)

    with open(DISABLED_FILE, "w", encoding="utf-8") as f:
        json.dump(disabled, f, ensure_ascii=False, indent=2)

    print("\nDone!")
    print(f"Active: {len(active)}")
    print(f"Disabled: {len(disabled)}")


if __name__ == "__main__":
    main()
