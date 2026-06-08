#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_proposal.py — SchooMy 写真入り提案書HTML自動生成（柔軟版）

使い方:
  python build_proposal.py --tools オレンジボード2,加速度センサー,スイッチ,湿度センサー,OLED,延長ケーブル,書き込み機2 \
      --magazines 冷蔵庫,通学路 --ver v1.6

設計方針:
- 既定は self-contained HTML 1枚を出力（写真base64・フォント埋め込み・右上ロゴ）。出力はHTMLのみ。
- 出力は「1枚物の縦長Webページ」。A4・@page・改ページは使わず、固定高さも作らない。
  ヘッダー（黒バンド＋右上ロゴ＋オレンジサブバー）は最上部に1回、フッターは最下部に1回だけ。
  コンテンツは中央寄せ（max-width 980px）・背景white基調・レスポンシブで、内容に応じて連続して伸びる。
  ※A4 PDFへの書き出しはデザイン確定後に別途対応する（render_pdf は将来用に温存。既定では呼ばない）。
- 入力は型番でも製品名でも可。表記ゆれ・部分一致で catalog.json から型番に解決（柔軟な名前解決）。
  ダイブ号は号名・通称・キーワード（例「冷蔵庫」「通学路」「p5.js」）でも解決。
  一意に決まらない場合は候補を提示して安全に停止（誤った型番を確定しない）。
- 各品目に数量を指定可（例 オレンジボード:2 / 書き込み機×2 / S-UT-AA1*2）。未指定は1個。
  カードに数量を表示し、合計は (単価×数量) で税抜/税込を再計算。
- どんな指示でも各カードに「名前・型番・金額・画像」の4点は必ず入る（画像が無ければプレースホルダ）。

データ: catalog.json のみ参照（ダイブ詳細は catalog.json の各 dive に保持済み。実行時にシートは読まない）。
"""
import argparse, base64, io, json, os, re, sys, html

ROOT = os.path.dirname(os.path.abspath(__file__))
# ブランド色。NAVY は「開発事業紹介」PDFのヘッダー/フッター帯から実測した濃いネイビー。
TEAL="#3AABA8"; CREAM="#F5E4C4"; ORANGE="#E88A0A"; BLUE="#2E8EC4"; INK="#1a1a1a"; NAVY="#1F2A30"

# 既定の問い合わせ先（PDFフッターと同一）。--contact-* で上書き可。
DEFAULT_CONTACT = {
    "person": "髙坂 幹男",
    "tel":    "080-4729-5996",
    "email":  "mikio.kousaka@schoomy.com",
}

# ---------- catalog / 名前解決 ----------
def load_catalog(path):
    doc=json.load(open(path,encoding="utf-8"))
    return doc, {p["model"]:p for p in doc["products"]}

# ダイブ詳細のうち、キーワード検索の対象にするテキスト項目
DIVE_TEXT_KEYS=["headline","title","folderName","features","pickupSensor",
                "learnKeyword","subjects","equipment","description"]
def _dive_blob(p):
    d=p.get("dive") or {}
    return " ".join(str(d.get(k,"")) for k in DIVE_TEXT_KEYS)

_STRIP=["月刊みんなのダイブ特集号","月刊みんなのダイブ","みんなのダイブ","特集号","通常号","特別号"]
def _norm(q):
    q=q.strip()
    for s in _STRIP: q=q.replace(s,"")
    q=re.sub(r"のもの$","",q); q=re.sub(r"号$","",q)
    return q.strip()

def find_models(token, cat):
    """型番 or 製品名/通称/キーワードを型番候補に解決。返り値 (候補list, 判定tier)。
    階層的に判定し、最初にヒットしたtierの候補（0/1/複数）を返す。"""
    qo=token.strip(); ql=qo.lower()
    # 1) 型番 完全一致（大小無視）
    t=[m for m in cat if m.lower()==ql]
    if t: return t,"型番"
    # 2) 通称(legacyName) 完全一致
    t=[m for m,p in cat.items() if (p.get("legacyName") or "").lower()==ql]
    if t: return t,"通称"
    # 3) 製品名 完全一致
    t=[m for m,p in cat.items() if (p.get("name") or "").lower()==ql]
    if t: return t,"製品名"
    qn=_norm(qo) or qo
    # 4) 製品名/通称 への部分一致（製品の同一性フィールド）
    t=[m for m,p in cat.items() if qn in (p.get("name") or "") or qn in (p.get("legacyName") or "")]
    if t: return t,"名称部分一致"
    # 5) 機能説明(can)・ダイブ詳細 への部分一致（拡張キーワード）
    t=[m for m,p in cat.items() if qn in (p.get("can") or "") or qn in _dive_blob(p)]
    if t: return t,"キーワード"
    return [],"none"

def resolve_model(token, cat):
    """型番に一意解決。曖昧・不一致は候補を提示して安全に停止（誤った型番を確定しない）。"""
    ms,tier=find_models(token,cat)
    if len(ms)==1: return ms[0]
    if len(ms)>1:
        cand=[f"{m}（{cat[m]['name']}）" for m in ms]
        sys.exit(f"『{token}』は一意に決まりません（{tier}で{len(ms)}件該当）。型番で指定してください:\n  - "
                 + "\n  - ".join(cand))
    sys.exit(f"型番・製品名がカタログに見つかりません: 『{token}』")

_QTY_SEP_RE=re.compile(r"^(.*?)\s*[:：xX×*]\s*(\d+)\s*(?:個|冊|点|つ)?$")   # 明示区切り
_QTY_SUF_RE=re.compile(r"^(.+?)\s*(\d+)\s*(?:個|冊|点|つ)$")               # 数字+助数詞
_QTY_BARE_RE=re.compile(r"^(.+?)(\d+)$")                                   # 末尾の素の数字
def parse_item(token, cat):
    """数量つき指定を (query, qty) に分解。未指定は1。型番末尾の数字は誤分割しない。
    対応例: 'S-UT-AA1*2' / 'オレンジボード:2' / '書き込み機×2' / 'オレンジボード2個' / 'オレンジボード2'"""
    t=token.strip()
    for rx in (_QTY_SEP_RE,_QTY_SUF_RE):
        m=rx.match(t)
        if m and m.group(1).strip():
            return m.group(1).strip(), max(1,int(m.group(2)))
    # 既に解決できるトークン（型番/通称/名）はそのまま → 型番末尾の数字を数量と誤認しない
    if find_models(t,cat)[0]:
        return t,1
    # 残りが一意解決できる場合のみ、末尾の素の数字を数量とみなす
    m=_QTY_BARE_RE.match(t)
    if m and m.group(1).strip() and len(find_models(m.group(1).strip(),cat)[0])==1:
        return m.group(1).strip(), max(1,int(m.group(2)))
    return t,1

# ---------- 画像 / フォント / ロゴ ----------
def placeholder_png(model):
    from PIL import Image, ImageDraw
    w,h=600,600
    im=Image.new("RGB",(w,h),CREAM)
    d=ImageDraw.Draw(im)
    d.rectangle([8,8,w-8,h-8],outline=ORANGE,width=4)
    d.text((w//2-90,h//2-20),model,fill=INK)
    d.text((w//2-70,h//2+10),"写真未登録",fill=ORANGE)
    b=io.BytesIO(); im.save(b,"PNG"); return b.getvalue()

def img_data_uri(model, imgdir):
    p=os.path.join(ROOT,imgdir,f"{model}.png")
    data=open(p,"rb").read() if os.path.exists(p) else placeholder_png(model)
    return "data:image/png;base64,"+base64.b64encode(data).decode()

def logo_data_uri(path):
    if path and os.path.exists(path):
        try:
            return "data:image/png;base64,"+base64.b64encode(open(path,"rb").read()).decode()
        except Exception as e:
            print(f"⚠ ロゴ読込に失敗（{path}）: {e} — ロゴ無しで生成します。", file=sys.stderr)
    return None

def subset_font_face(ttf_path, used_chars, family, weight):
    from fontTools import subset
    font=subset.load_font(ttf_path, subset.Options())
    opt=subset.Options(); opt.layout_features="*"; opt.glyph_names=False
    s=subset.Subsetter(options=opt)
    s.populate(text="".join(sorted(used_chars))+" 0123456789円￥（）()／/・,.-×")
    s.subset(font)
    buf=io.BytesIO()
    try:
        font.flavor="woff2"; font.save(buf); fmt="woff2"; mime="font/woff2"
    except Exception:
        buf=io.BytesIO(); font.flavor=None; font.save(buf); fmt="truetype"; mime="font/ttf"
    b64=base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
            f"src:url(data:{mime};base64,{b64}) format('{fmt}');}}")

def yen(n): return f"{n:,}円"

def is_magazine(p):
    return p.get("type")=="教材" or p["model"].startswith("S-MZ")

# ---------- カード（名前・型番・金額・画像の4点を必ず含む） ----------
def product_card(p):
    qty=p["_qty"]; ex=p["priceExTax"]; inc=p["priceIncTax"]
    mag=is_magazine(p)
    cls="card mag" if mag else "card"
    qty_html=f'<span class="qty">×{qty}</span>' if qty>1 else ""
    # 金額（数量込み）。単価と小計を併記。
    if qty>1:
        price=(f'<div class="price"><span>単価 税込 {yen(inc)}</span>'
               f'<b>小計 税込 {yen(inc*qty)}</b><span class="ex">（税抜 {yen(ex*qty)}）</span></div>')
    else:
        price=(f'<div class="price"><span>税抜 {yen(ex)}</span><b>税込 {yen(inc)}</b></div>')
    # 補足（あれば）。ダイブ号は大見出しキャッチ＋ピックアップ等を簡潔に。
    sub=""
    d=p.get("dive")
    if mag and d:
        bits=[d.get("headline"), (("ピックアップ："+d["pickupSensor"]) if d.get("pickupSensor") else None),
              d.get("subjects"), d.get("grades")]
        sub=" / ".join(b for b in bits if b)
    else:
        sub=p.get("can") or ""
    meta=""
    if mag:
        jan=p.get("jan")
        meta=f'<div class="meta">{html.escape("JAN "+jan if jan else "JAN 未登録")}</div>'
    return f"""<div class="{cls}">
  <div class="thumb"><img src="{p['_img']}" alt=""></div>
  <div class="info">
    <div class="badgerow"><span class="badge">{html.escape(p['model'])}</span>{qty_html}</div>
    <div class="cname">{html.escape(p['name'])}</div>
    <div class="can">{html.escape(sub)}</div>
    {meta}
    {price}
  </div>
</div>"""

# ---------- HTML 組み立て ----------
def build_html(items, ver, title, logo_uri=None, contact=None):
    tools=[p for p in items if not is_magazine(p)]
    mags =[p for p in items if is_magazine(p)]
    contact=contact or DEFAULT_CONTACT

    used=set(title)
    for p in items:
        for k in ("model","name","can","jan"):
            v=p.get(k)
            if v: used.update(str(v))
        d=p.get("dive") or {}
        for k in ("headline","pickupSensor","subjects","grades"):
            if d.get(k): used.update(str(d[k]))
    used.update("ご提案書株式会社スクーミーツール教材月刊みんなのダイブ価格構成合計税抜税込点内容のご案内"
                "ピックアップ写真未登録項目数本書はに関するです年月日単価小計数量ご対象学年情報数学理科化学英語")
    # ヘッダー/フッターの固定文言（M PLUS サブセットに確実に含める：問い合わせ・社名・ドメイン・記号・英数）
    used.update("お問い合わせ営業担当TELEmail © SchooMy, Inc. 株式会社スクーミー fox.schoomy.com 開発事業紹介"
                "@:/.-_0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
    used.update(str(contact.get("person","")))
    used.update(str(contact.get("tel","")))
    used.update(str(contact.get("email","")))
    reg=subset_font_face(os.path.join(ROOT,"fonts","MPLUS1p-Regular.ttf"),used,"MPLUS1p",400)
    bold=subset_font_face(os.path.join(ROOT,"fonts","MPLUS1p-Bold.ttf"),used,"MPLUS1p",700)

    ex=sum(p['priceExTax']*p['_qty'] for p in items)
    inc=sum(p['priceIncTax']*p['_qty'] for p in items)
    total_qty=sum(p['_qty'] for p in items)

    rows=""
    for p in items:
        q=p['_qty']
        rows+=(f"<tr><td class='m'>{html.escape(p['model'])}</td><td>{html.escape(p['name'])}</td>"
               f"<td class='r'>{q}</td><td class='r'>{yen(p['priceExTax']*q)}</td>"
               f"<td class='r'>{yen(p['priceIncTax']*q)}</td></tr>")

    logo_html=f'<img class="hlogo" src="{logo_uri}" alt="SchooMy">' if logo_uri else ''
    css=f"""
{reg}
{bold}
*{{margin:0;padding:0;box-sizing:border-box}}
/* 1枚物の縦長Webページ。@page/改ページ/固定高さは使わず、コンテンツが連続して伸びる */
html{{background:#eef0f2}}
body{{font-family:'MPLUS1p','Meiryo',sans-serif;color:{INK};background:#eef0f2;line-height:1.6;
  -webkit-print-color-adjust:exact;print-color-adjust:exact}}
.wrap{{max-width:980px;margin:0 auto;background:#fff;min-height:100vh}}
/* ヘッダーは最上部に1回だけ。PDF「開発事業紹介」に準拠：濃紺の帯＋白タイトル＋右上ロゴ＋直下のオレンジ細ライン */
.hband{{background:{NAVY};color:#fff;display:flex;align-items:center;justify-content:space-between;gap:24px;
  padding:16px 44px;border-bottom:4px solid {ORANGE}}}
.htitle{{font-weight:700;font-size:25px;letter-spacing:.04em}}
.hver{{font-size:14px;font-weight:700;opacity:.8;margin-left:10px}}
.hlogo{{height:52px;width:auto;display:block;object-fit:contain;margin-left:24px}}
/* バージョン等の細い案内バー（薄色・最上部に1回） */
.subbar{{background:#fff;color:#7a8590;padding:8px 44px;font-size:13px;font-weight:700;border-bottom:1px solid #eee}}
/* フッターは最下部に1回だけ（PDFに準拠：濃紺帯＋お問い合わせ＋著作権/ドメイン） */
.foot{{background:{NAVY};color:#fff}}
.foot-contact{{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:14px 44px}}
.foot-label{{background:{ORANGE};color:#fff;font-weight:700;font-size:13px;padding:5px 14px;border-radius:6px;white-space:nowrap}}
.foot-cinfo{{font-size:13px;color:#e9ecef;line-height:1.7}}
.foot-cinfo .o{{color:#F2A23A;font-weight:700}}
.foot-copy{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;
  padding:9px 44px;font-size:11.5px;color:#9aa4ad;border-top:1px solid rgba(255,255,255,.10)}}
.foot-copy .dom{{color:#c2c9cf}}
.doc{{padding:30px 36px 36px}}
.lead{{font-size:15px;line-height:1.95;margin-bottom:22px}}
table.sum{{width:100%;border-collapse:collapse;font-size:14px}}
table.sum th{{background:{TEAL};color:#fff;padding:11px;text-align:left}}
table.sum td{{border-bottom:1px solid #eee;padding:10px 11px}}
table.sum td.r,table.sum th.r{{text-align:right;white-space:nowrap}}
table.sum td.m{{color:{BLUE};font-weight:700;white-space:nowrap}}
.total{{margin-top:22px;background:{CREAM};border-left:6px solid {ORANGE};padding:18px 22px;border-radius:8px;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}}
.total .lab{{font-weight:700;font-size:15px}}
.total .ex{{font-size:15px;margin-right:24px;color:#555}}
.total .inc{{font-size:22px;font-weight:700;color:{ORANGE}}}
.secbar{{margin-top:36px;background:{ORANGE};color:#fff;padding:10px 18px;font-size:15px;font-weight:700;border-radius:8px}}
.secttl{{padding:18px 0 8px;font-size:17px;font-weight:700;color:{TEAL}}}
.cards{{display:flex;flex-direction:column;gap:18px}}
.card{{display:flex;gap:22px;align-items:center;background:#fff;border:1px solid #eee;border-radius:12px;padding:18px}}
/* サムネ：黒フチ/枠/濃い影なし、背景white統一。ツールは正方形センタークロップ */
.card .thumb{{width:150px;height:150px;flex:0 0 150px;background:#fff;border:none;box-shadow:none;border-radius:8px;overflow:hidden}}
.card .thumb img{{width:100%;height:100%;object-fit:cover;object-position:center;display:block}}
/* 教材表紙：元比率のまま全体表示（contain・歪ませない／切らない） */
.card.mag .thumb{{width:150px;height:196px;flex:0 0 150px;display:flex;align-items:center;justify-content:center}}
.card.mag .thumb img{{width:100%;height:100%;object-fit:contain}}
.card .info{{flex:1;min-width:0}}
.badgerow{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.badge{{display:inline-block;background:{BLUE};color:#fff;font-size:12px;font-weight:700;padding:3px 10px;border-radius:6px}}
.qty{{display:inline-block;background:{INK};color:#fff;font-size:12px;font-weight:700;padding:3px 10px;border-radius:6px}}
.cname{{font-size:18px;font-weight:700;margin-bottom:5px}}
.can{{font-size:13.5px;line-height:1.7;color:#333;margin-bottom:7px}}
.meta{{font-size:12px;color:#777;margin-bottom:7px}}
.price{{font-size:14px}}
.price span{{margin-right:18px;color:#555}}
.price .ex{{font-size:12.5px}}
.price b{{color:{ORANGE};font-size:16px;margin-right:18px}}
.empty{{color:#999;font-size:14px;padding:10px 0}}
/* レスポンシブ：狭い画面ではカードを縦積み */
@media (max-width:620px){{
  .hband{{padding:14px 20px;flex-wrap:wrap;gap:10px}}
  .htitle{{font-size:20px}} .hlogo{{height:46px;margin-left:0}}
  .subbar,.doc{{padding-left:20px;padding-right:20px}}
  .foot-contact,.foot-copy{{padding-left:20px;padding-right:20px}}
  .card{{flex-direction:column;align-items:stretch}}
  .card .thumb{{width:100%;height:auto;aspect-ratio:1/1;flex:none}}
  .card.mag .thumb{{width:100%;height:auto;aspect-ratio:3/4;flex:none}}
}}
"""
    sections=""
    # 1) サマリ（必ず表示）
    sections+=f"""<section>
  <p class="lead">本書は、株式会社スクーミーの教育用ツールおよび教材「月刊みんなのダイブ」に関するご提案です。選定いただいた構成（全{total_qty}点）の内容と価格を以下にまとめております。</p>
  <table class="sum"><tr><th>型番</th><th>品名</th><th class="r">数量</th><th class="r">税抜</th><th class="r">税込</th></tr>{rows}</table>
  <div class="total"><div class="lab">合計（{total_qty}点）</div><div><span class="ex">税抜 {yen(ex)}</span><span class="inc">税込 {yen(inc)}</span></div></div>
</section>"""
    # 2) ツール（あれば）
    if tools:
        cards="".join(product_card(p) for p in tools)
        sections+=f"""<section>
  <div class="secbar">ご提案内容｜ツール</div>
  <div class="secttl">オレンジボードと各種コネクター</div>
  <div class="cards">{cards}</div>
</section>"""
    # 3) 教材（あれば）
    if mags:
        cards="".join(product_card(p) for p in mags)
        sections+=f"""<section>
  <div class="secbar">ご提案内容｜教材（月刊みんなのダイブ）</div>
  <div class="secttl">授業でそのまま使える教材誌</div>
  <div class="cards">{cards}</div>
</section>"""

    person=html.escape(str(contact.get("person","")))
    tel=html.escape(str(contact.get("tel","")))
    email=html.escape(str(contact.get("email","")))
    footer=f"""<footer class="foot">
  <div class="foot-contact">
    <span class="foot-label">お問い合わせ</span>
    <span class="foot-cinfo">営業担当：{person}　<span class="o">TEL {tel}</span>　<span class="o">Email {email}</span></span>
  </div>
  <div class="foot-copy">
    <span>© SchooMy, Inc. 株式会社スクーミー</span>
    <span class="dom">fox.schoomy.com</span>
  </div>
</footer>"""
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} {html.escape(ver)}</title><style>{css}</style></head><body>
<div class="wrap">
<header class="hband"><div class="htitle">{html.escape(title)}<span class="hver">{html.escape(ver)}</span></div>{logo_html}</header>
<div class="subbar">ご提案内容のご案内　{html.escape(ver)}</div>
<main class="doc">
{sections}
</main>
{footer}
</div>
</body></html>"""

def render_pdf(html_path, pdf_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch()
        pg=b.new_page()
        pg.goto("file://"+os.path.abspath(html_path))
        pg.evaluate("document.fonts.ready")
        # フルブリード（余白0）。ヘッダー/フッターは本文フロー内。内容量に応じてページが自然に伸びる。
        pg.pdf(path=pdf_path,format="A4",print_background=True,
               margin={"top":"0","bottom":"0","left":"0","right":"0"})
        b.close()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tools",default="")
    ap.add_argument("--magazines",default="")
    ap.add_argument("--ver",default="v1.6")
    ap.add_argument("--title",default="ご提案書")
    ap.add_argument("--catalog",default=os.path.join(ROOT,"catalog.json"))
    ap.add_argument("--imgdir",default="img")
    ap.add_argument("--logo",default=os.path.join(ROOT,"assets","logo.png"))
    # 問い合わせ先（既定は髙坂さん。PDFフッターと同一）。必要時のみ上書き。
    ap.add_argument("--contact-person",default=DEFAULT_CONTACT["person"])
    ap.add_argument("--contact-tel",default=DEFAULT_CONTACT["tel"])
    ap.add_argument("--contact-email",default=DEFAULT_CONTACT["email"])
    ap.add_argument("--pdf",action="store_true",help="PDFも出力（既定はHTMLのみ）")
    a=ap.parse_args()
    doc,cat=load_catalog(a.catalog)
    contact={"person":a.contact_person,"tel":a.contact_tel,"email":a.contact_email}

    def pick(csv):
        out=[]
        for tok in [x.strip() for x in csv.split(",") if x.strip()]:
            query,qty=parse_item(tok,cat)
            m=resolve_model(query,cat)
            p=dict(cat[m]); p["_qty"]=qty; p["_img"]=img_data_uri(m,a.imgdir)
            out.append(p)
        return out

    items=pick(a.tools)+pick(a.magazines)
    if not items:
        sys.exit("少なくとも1点を --tools か --magazines で指定してください。")

    logo_uri=logo_data_uri(a.logo)
    if a.logo and not logo_uri:
        print(f"⚠ ロゴ画像が見つかりません（{a.logo}）。ロゴ無しで生成します。", file=sys.stderr)

    html_str=build_html(items,a.ver,a.title,logo_uri,contact)
    os.makedirs(os.path.join(ROOT,"out"),exist_ok=True)
    hp=os.path.join(ROOT,"out",f"proposal_{a.ver}.html")
    open(hp,"w",encoding="utf-8").write(html_str)
    print("HTML:",hp,f"({len(html_str)//1024} KB)")
    print("  品目:", ", ".join(f"{p['model']}×{p['_qty']}" for p in items))
    if a.pdf:
        pp=os.path.join(ROOT,"out",f"proposal_{a.ver}.pdf")
        render_pdf(hp,pp); print("PDF :",pp)

if __name__=="__main__":
    main()
