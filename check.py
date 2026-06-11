import json
import requests
import time
import os

INPUT_FILE = "sources.json"
ACTIVE_FILE = "active.json"
DISABLED_FILE = "disabled.json"
HISTORY_FILE = "history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
}

TIMEOUT = 8


# =========================
# 🔥 评分系统（单次检测）
# =========================
def calculate_score(status_code, content, is_json, error=None):
    score = 0

    # HTTP
    if status_code == 200:
        score += 30
    elif status_code:
        score += 10

    # 内容长度
    length = len(content or "")
    if length > 1000:
        score += 30
    elif length > 300:
        score += 20
    elif length > 50:
        score += 10

    # JSON
    if is_json:
        score += 20

    # 关键词扣分
    bad_keywords = ["404", "not found", "expired", "域名", "出售", "error", "测试", "公告"]
    if content:
        lower = content.lower()
        if any(k in lower for k in bad_keywords):
            score -= 30

    # 请求错误
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


# =========================
# 🔥 历史稳定性系统
# =========================
def update_history(history, name, ok):
    if name not in history:
        history[name] = []

    history[name].append(1 if ok else 0)

    # 保留7天
    history[name] = history[name][-7:]


def get_stability(history_list):
    if not history_list:
        return 0
    return int(sum(history_list) / len(history_list) * 100)


# =========================
# 检测接口
# =========================
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


# =========================
# 主程序
# =========================
def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        sources = json.load(f)

    # 历史加载
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    else:
        history = {}

    active = []
    disabled = []

    print(f"Total sources: {len(sources)}")

    for i, item in enumerate(sources, 1):

        name = item.get("name", "")

        ok, score, grade = check_url(item)

        # 基础评分
        item["score"] = score
        item["grade"] = grade

        # 历史记录
        update_history(history, name, ok)

        # 稳定性评分（核心升级）
        stability = get_stability(history.get(name, []))
        item["stability"] = stability

        if ok:
            active.append(item)
            print(f"[OK] {i}/{len(sources)} score={score} stability={stability} {name}")
        else:
            disabled.append(item)
            print(f"[FAIL] {i}/{len(sources)} score={score} {name}")

        time.sleep(0.2)

    # =========================
    # 🔥 智能排序（关键）
    # =========================
    active.sort(key=lambda x: x.get("stability", 0), reverse=True)

    # =========================
    # 🔥 TOP10输出（最终接口）
    # =========================
    top10 = active[:10]

    tvbox_data = {
    "sites": [
        {
            "key": x.get("name", ""),
            "name": x.get("name", ""),
            "type": 3,
            "api": x.get("url", ""),
            "searchable": 1,
            "quickSearch": 1,
            "filterable": 0
        }
        for x in top10
    ]
}

    # =========================
    # 写文件
    # =========================
    with open(ACTIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(active, f, ensure_ascii=False, indent=2)

    with open(DISABLED_FILE, "w", encoding="utf-8") as f:
        json.dump(disabled, f, ensure_ascii=False, indent=2)

    with open("tvbox.json", "w", encoding="utf-8") as f:
        json.dump(tvbox_data, f, ensure_ascii=False, indent=2)

    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print("\nDone!")
    print(f"Active: {len(active)}")
    print(f"Disabled: {len(disabled)}")
    print(f"TOP10: {len(top10)}")


if __name__ == "__main__":
    main()
