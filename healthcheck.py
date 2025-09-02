import os, requests, json
from dotenv import load_dotenv
load_dotenv()
token = os.getenv("WHATSAPP_ACCESS_TOKEN")
ids = [os.getenv("WHATSAPP_PHONE_NUMBER_ID"), os.getenv("ALT_WHATSAPP_PHONE_NUMBER_ID")]
base = "https://graph.facebook.com/v20.0"
headers = {"Authorization": f"Bearer {token}"}
best = None
for pid in ids:
    if not pid: continue
    r = requests.get(f"{base}/{pid}", params={"fields":"id,display_phone_number,quality_rating"}, headers=headers, timeout=15)
    try: data = r.json()
    except: data = {"raw": r.text}
    ok = 200 <= r.status_code < 300
    print(f"[{pid}] status={r.status_code} ok={ok} -> {json.dumps(data, ensure_ascii=False)}")
    if ok and not best: best = pid
print(f"SELECTED={best}")
