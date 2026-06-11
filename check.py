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


def calculate_score(status_code, content, is_json, error=None):
    score = 0

    # 1️⃣ HTTP状态
    if status_code == 200:
        score += 30
    elif status_code:
        score += 10

    # 2️⃣ 内容长度
    length = len(content or "")
    if length > 1000:
        score += 30
    elif length > 300:
        score += 20
    elif length > 50:
        score += 10

    # 3️⃣ JSON质量
    if is_json:
        score += 20

    # 4️⃣ 内容稳定性
    bad_keywords = ["404", "not found", "expired", "域名", "出售", "error", "测试", "公告"]

    if content:
        lower = content.lower()
        if any(k in lower for k in bad_keywords):
            score -= 30

    # 5️⃣ 错误扣分
    if error:
        score -= 20

    return max(score, 0)


def classify(score):
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "FAIL"


def check_url(item):
    url = item.get("url", "").strip()

    if not url:
        return False, 0, "empty url"

    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)

        content = r.text or ""
        status = r.status_code

        is_json = False
        try:
            if "application/json" in r.headers.get("Content-Type", ""):
                json.loads(content)
                is_json = True
        except:
            is_json = False

        score = calculate_score(status, content, is_json)

        grade = classify(score)

        if score < 40:
            return False, score, grade

        return True, score, grade

    except requests.exceptions.RequestException as e:
        return False, 0, str(e)


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    active = []
    disabled = []

    print(f"Total sources: {len(sources)}")

    for i, item in enumerate(sources, 1):

        ok, score, grade = check_url(item)

        item["score"] = score
        item["grade"] = grade

        if ok:
            active.append(item)
            print(f"[ACTIVE A] {i}/{len(sources)} score={score} grade={grade} {item.get('name','')}")
        else:
            disabled.append(item)
            print(f"[FAIL] {i}/{len(sources)} score={score} grade={grade}")

        time.sleep(0.2)

    # 🔥 按评分排序（关键升级）
    active.sort(key=lambda x: x.get("score", 0), reverse=True)

    with open(ACTIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(active, f, ensure_ascii=False, indent=2)

    with open(DISABLED_FILE, "w", encoding="utf-8") as f:
        json.dump(disabled, f, ensure_ascii=False, indent=2)

    print("\nDone!")
    print(f"Active: {len(active)}")
    print(f"Disabled: {len(disabled)}")


if __name__ == "__main__":
    main()
