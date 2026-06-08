#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
harvest_images.py — catalog.json の photoFileId から全画像をDriveで取得し img/<型番>.png に保存。
型番→fileId を直接使うので、ファイル名マッチのズレは発生しない。
公開URL（uc?export=download）で取得し、PNG/JPEGのマジックバイトを検証。失敗型番は最後に一覧報告。

依存: pip install requests pillow
使い方: python harvest_images.py
※ Driveファイルが「リンクを知っている全員」公開になっている必要があります。
   非公開の場合は rclone 等の認証取得に切り替えてください（その場合 fetch() を差し替え）。
"""
import io, json, os, sys, requests
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SESSION = requests.Session()

def fetch(file_id):
    url = "https://drive.google.com/uc?export=download"
    r = SESSION.get(url, params={"id": file_id}, stream=True, timeout=60)
    # 大きいファイルはウイルススキャン確認トークンが必要
    token = next((v for k, v in r.cookies.items() if k.startswith("download_warning")), None)
    if token:
        r = SESSION.get(url, params={"id": file_id, "confirm": token}, stream=True, timeout=60)
    return r.content

def is_image(b):
    return b[:8] == b"\x89PNG\r\n\x1a\n" or b[:3] == b"\xff\xd8\xff"

def main():
    doc = json.load(open(os.path.join(ROOT, "catalog.json"), encoding="utf-8"))
    os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
    ok, failed, skipped = [], [], []
    for p in doc["products"]:
        fid = p.get("photoFileId")
        model = p["model"]
        if not fid:
            skipped.append(model); continue
        try:
            data = fetch(fid)
            if not is_image(data):
                failed.append((model, "not-image(HTMLの可能性)")); continue
            im = Image.open(io.BytesIO(data))
            if im.mode not in ("RGB", "L"):
                im = im.convert("RGB")
            w, h = im.size
            longest = max(w, h)
            if longest > 1200:
                s = 1200 / longest
                im = im.resize((int(w * s), int(h * s)))
            out = os.path.join(ROOT, "img", f"{model}.png")
            im.save(out, "PNG", optimize=True)
            ok.append(model)
            print(f"OK  {model}  {im.size}  {os.path.getsize(out)//1024}KB")
        except Exception as e:
            failed.append((model, str(e)))
    print(f"\n=== 取得成功 {len(ok)} / 失敗 {len(failed)} / 画像なし {len(skipped)} ===")
    if failed:
        print("失敗:", failed)
    if skipped:
        print("画像なし(要登録):", skipped)

if __name__ == "__main__":
    main()
