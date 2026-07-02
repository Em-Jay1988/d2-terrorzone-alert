import requests
import json

URLS = [
    "https://d2emu.com/api/v1/tz",
    "https://d2tz.info/api",
    "https://d2runewizard.com/api/terror-zone",
]

for url in URLS:
    print("\n==============================")
    print(url)
    print("==============================")
    try:
        r = requests.get(url, timeout=20)
        print("STATUS:", r.status_code)
        print("CONTENT-TYPE:", r.headers.get("content-type"))
        print(r.text[:2000])
    except Exception as e:
        print("ERROR:", repr(e))
