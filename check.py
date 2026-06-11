import json
import requests
from datetime import datetime

with open("sources.json", "r", encoding="utf-8") as f:
    sources = json.load(f)

active = []
disabled = []

for item in sources:

    url = item.get("url", "")

    try:
        r = requests.get(
            url,
            timeout=10,
            allow_redirects=True,
            headers={
                "User-Agent":"Mozilla/5.0"
            }
        )

        if r.status_code == 200:

            item["enable"] = True
            item["status"] = "alive"
            item["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            active.append(item)

        else:

            item["enable"] = False
            item["status"] = "dead"
            item["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            disabled.append(item)

    except:

        item["enable"] = False
        item["status"] = "dead"
        item["last_check"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        disabled.append(item)

with open(
    "active.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        active,
        f,
        ensure_ascii=False,
        indent=2
    )

with open(
    "disabled.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        disabled,
        f,
        ensure_ascii=False,
        indent=2
    )

print(
    f"active:{len(active)} disabled:{len(disabled)}"
)
