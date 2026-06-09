#!/usr/bin/env python3
# SchooMy 月刊みんなのダイブ Instagram auto-poster (GitHub Actions)
# 毎日 JST 09:00 に起動し、その日が投稿日(status=pending)の項目を Instagram Graph API で投稿する。
import os, glob, json, time, datetime, urllib.request, urllib.parse, urllib.error

TOKEN = os.environ.get("IG_ACCESS_TOKEN", "").strip()
GRAPH = "https://graph.instagram.com/v21.0"

def jst_today():
    return (datetime.datetime.utcnow() + datetime.timedelta(hours=9)).date()

def post_json(url, payload):
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            return True, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return False, json.loads(e.read())

def publish_one(ig_user_id, image_url, caption):
    ok, r = post_json(f"{GRAPH}/{ig_user_id}/media",
                      {"image_url": image_url, "caption": caption, "access_token": TOKEN})
    if not ok or "id" not in r:
        return None, "container: " + json.dumps(r, ensure_ascii=False)[:300]
    creation_id = r["id"]
    time.sleep(5)
    ok, r = post_json(f"{GRAPH}/{ig_user_id}/media_publish",
                      {"creation_id": creation_id, "access_token": TOKEN})
    if not ok or "id" not in r:
        return None, "publish: " + json.dumps(r, ensure_ascii=False)[:300]
    return r["id"], ""

def main():
    if not TOKEN:
        print("ERROR: IG_ACCESS_TOKEN secret is not set."); return 1
    today = jst_today()
    changed = False
    for path in sorted(glob.glob("mnd/schedule_*.json")):
        m = json.load(open(path, encoding="utf-8"))
        ig_user_id = os.environ.get("IG_USER_ID", "").strip() or m.get("ig_user_id", "")
        for it in m["items"]:
            if it.get("status") != "pending":
                continue
            d = datetime.datetime.strptime(it["date"], "%Y/%m/%d").date()
            if d != today:
                continue
            print(f"posting {it['date']} ...")
            pid, err = publish_one(ig_user_id, it["image_url"], it["caption"])
            if pid:
                it["status"], it["post_id"], it["error"] = "posted", pid, ""
                print("  OK post_id=", pid)
            else:
                it["status"], it["error"] = "error", err
                print("  FAIL", err)
            changed = True
        if changed:
            json.dump(m, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    if not changed:
        print(f"no posts due today ({today}).")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
