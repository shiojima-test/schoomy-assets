#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_proposal.py — SchooMy 写真入り提案書HTML自動生成

使い方:
  python build_proposal.py --tools S-BD-AA1,S-CN-A10,S-UT-AA1 --magazines S-MZ-A16 --ver v1.2 --pdf

入力: 型番 or 製品名リスト（--tools ツール / --magazines 教材）
      型番は完全一致を優先、見つからなければ catalog.json の name に部分一致で型番へ変換。
出力: out/proposal_<ver>.html （--pdf 指定で out/proposal_<ver>.pdf も）
写真は img/<型番>.png を base64 でHTMLに直接埋め込み（単一ファイルで完結）。
ロゴ assets/logo.png を base64 で各ページ右上に埋め込み（無ければロゴ無しで生成）。
フォントは M PLUS 1p を使用文字だけサブセット化して woff2 を埋め込み。
"""
import argparse, base64, io, json, os, sys, html

ROOT = os.path.dirname(os.path.abspath(__file__))
TEAL="#3AABA8"; CREAM="#F5E4C4"; ORANGE="#E88A0A"; BLUE="#2E8EC4"; INK="#1a1a1a"

def load_catalog(path):
    doc=json.load(open(path,encoding="utf-8"))
    return {p["model"]:p for p in doc["products"]}

def placeholder_png(model):
    from PIL import Image, ImageDraw
    w,h=600,450
    im=Image.new("RGB",(w,h),CREAM)
    d=ImageDraw.Draw(im)
    d.rectangle([8,8,w-8,h-8],outline=ORANGE,width=4)
    d.text((w//2-90,h//2-20),model,fill=INK)
    d.text((w//2-70,h//2+10),"写真未登録",fill=ORANGE)
    b=io.BytesIO(); im.save(b,"PNG"); return b.getvalue()

def img_data_uri(model, imgdir):
    p=os.path.join(ROOT,imgdir,f"{model}.png")
    if os.path.exists(p):
        data=open(p,"rb").read()
    else:
        data=placeholder_png(model)
    return "data:image/png;base64,"+base64.b64encode(data).decode()

def logo_data_uri(path):
    """assets/logo.png を base64 data URI で返す。無ければ None（ロゴ無しフォールバック）。"""
    if path and os.path.exists(path):
        try:
            data=open(path,"rb").read()
            return "data:image/png;base64,"+base64.b64encode(data).decode()
        except Exception as e:
            print(f"⚠ ロゴ読込に失敗（{path}）: {e} — ロゴ無しで生成します。", file=sys.stderr)
    return None

def resolve_model(token, cat):
    """型番（完全一致）優先、無ければ製品名の部分一致で型番に変換。後方互換。"""
    t=token.strip()
    if t in cat:                                   # 型番 完全一致（従来仕様）
        return t
    low={m.lower():m for m in cat}
    if t.lower() in low:                           # 型番 大文字小文字無視
        return low[t.lower()]
    hits=[m for m,p in cat.items() if t in (p.get("name") or "")]  # 製品名 部分一致
    if len(hits)==1:
        return hits[0]
    if len(hits)>1:
        sys.exit(f"製品名 '{t}' が複数の型番に一致します（型番で指定してください）: {hits}")
    sys.exit(f"型番・製品名がカタログに見つかりません: {token}")

def subset_font_face(ttf_path, used_chars, family, weight):
    """Subset TTF to used chars, return @font-face CSS with embedded woff2(or ttf)."""
    from fontTools import subset
    font=subset.load_font(ttf_path, subset.Options())
    opt=subset.Options(); opt.layout_features="*"; opt.glyph_names=False
    try: opt.flavor="woff2"; fmt="woff2"
    except Exception: fmt="truetype"
    s=subset.Subsetter(options=opt)
    s.populate(text="".join(sorted(used_chars))+" 0123456789円￥（）()／/・,.-")
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

def tool_card(p):
    return f"""<div class="card">
  <div class="thumb"><img src="{p['_img']}" alt=""></div>
  <div class="info">
    <div class="badge">{html.escape(p['model'])}</div>
    <div class="cname">{html.escape(p['name'])}</div>
    <div class="can">{html.escape(p.get('can') or '')}</div>
    <div class="price"><span>税抜 {yen(p['priceExTax'])}</span><b>税込 {yen(p['priceIncTax'])}</b></div>
  </div>
</div>"""

def mag_card(p):
    jan=f"JAN {p['jan']}" if p.get('jan') else "JAN 未登録"
    return f"""<div class="card mag">
  <div class="thumb"><img src="{p['_img']}" alt=""></div>
  <div class="info">
    <div class="badge">{html.escape(p['model'])}</div>
    <div class="cname">{html.escape(p['name'])}</div>
    <div class="can">{html.escape(p.get('can') or '')}</div>
    <div class="meta">{html.escape(jan)}</div>
    <div class="price"><span>税抜 {yen(p['priceExTax'])}</span><b>税込 {yen(p['priceIncTax'])}</b></div>
  </div>
</div>"""

def build_html(tools, mags, ver, title, logo_uri=None):
    used=set(title)
    for p in tools+mags:
        for k in ("model","name","can","jan"):
            v=p.get(k)
            if v: used.update(str(v))
    used.update("ご提案書株式会社スクーミーツール教材月刊みんなのダイブ価格構成合計税抜税込点内容のご案内"
                "ピックアップ写真未登録項目数本書はに関するです年月日")
    reg=subset_font_face(os.path.join(ROOT,"fonts","MPLUS1p-Regular.ttf"),used,"MPLUS1p",400)
    bold=subset_font_face(os.path.join(ROOT,"fonts","MPLUS1p-Bold.ttf"),used,"MPLUS1p",700)
    ex=sum(p['priceExTax'] for p in tools+mags)
    inc=sum(p['priceIncTax'] for p in tools+mags)
    rows=""
    for p in tools+mags:
        rows+=f"<tr><td class='m'>{html.escape(p['model'])}</td><td>{html.escape(p['name'])}</td><td class='r'>{yen(p['priceExTax'])}</td><td class='r'>{yen(p['priceIncTax'])}</td></tr>"
    logo_html=f'<img class="hlogo" src="{logo_uri}" alt="SchooMy">' if logo_uri else ''
    def header(sub):
        return f"""<div class="hband"><div class="htitle">{html.escape(title)}</div>{logo_html}</div><div class="subbar">{html.escape(sub)}</div>"""
    foot=f"""<div class="foot">© 株式会社スクーミー　fox.schoomy.com　|　{html.escape(ver)}</div>"""
    css=f"""
{reg}
{bold}
*{{margin:0;padding:0;box-sizing:border-box}}
@page{{size:A4;margin:0}}
html,body{{font-family:'MPLUS1p','Meiryo',sans-serif;color:{INK};-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:210mm;height:297mm;position:relative;overflow:hidden;page-break-after:always;background:#fff}}
.page:last-child{{page-break-after:auto}}
.hband{{background:{INK};color:#fff;height:22mm;display:flex;align-items:center;justify-content:space-between;padding:5mm 14mm}}
.htitle{{font-weight:700;font-size:20pt;letter-spacing:.04em}}
.hlogo{{height:10mm;width:auto;max-width:50mm;display:block;object-fit:contain;margin-left:8mm}}
.subbar{{background:{ORANGE};color:#fff;height:8mm;display:flex;align-items:center;padding:0 12mm;font-size:10.5pt;font-weight:700}}
.body{{padding:10mm 12mm}}
.lead{{font-size:11pt;line-height:1.9;margin-bottom:7mm}}
table.sum{{width:100%;border-collapse:collapse;font-size:10.5pt}}
table.sum th{{background:{TEAL};color:#fff;padding:3mm;text-align:left}}
table.sum td{{border-bottom:1px solid #ddd;padding:2.6mm 3mm}}
table.sum td.r,table.sum th.r{{text-align:right}}
table.sum td.m{{color:{BLUE};font-weight:700;white-space:nowrap}}
.total{{margin-top:6mm;background:{CREAM};border-left:6px solid {ORANGE};padding:5mm 6mm;display:flex;justify-content:space-between;align-items:center}}
.total .lab{{font-weight:700}}
.total .ex{{font-size:11pt;margin-right:8mm}}
.total .inc{{font-size:16pt;font-weight:700;color:{ORANGE}}}
.cards{{display:flex;flex-direction:column;gap:5mm;padding:8mm 12mm}}
.card{{display:flex;gap:6mm;border:1px solid #e3e3e3;border-radius:3mm;padding:5mm;align-items:center}}
/* ツール写真：正方形枠に中央センタークロップ（cover） */
.card .thumb{{width:40mm;height:40mm;flex:0 0 40mm;background:{CREAM};border-radius:2mm;overflow:hidden}}
.card .thumb img{{width:100%;height:100%;object-fit:cover;object-position:center;display:block}}
/* 教材表紙：元比率のまま全体表示（contain・歪ませない／切らない） */
.card.mag .thumb{{width:40mm;height:52mm;flex:0 0 40mm;display:flex;align-items:center;justify-content:center}}
.card.mag .thumb img{{width:100%;height:100%;object-fit:contain}}
.card .info{{flex:1}}
.badge{{display:inline-block;background:{BLUE};color:#fff;font-size:9pt;font-weight:700;padding:1mm 3mm;border-radius:2mm;margin-bottom:2mm}}
.cname{{font-size:13pt;font-weight:700;margin-bottom:1.5mm}}
.can{{font-size:10pt;line-height:1.7;color:#333;margin-bottom:2mm}}
.meta{{font-size:9pt;color:#666;margin-bottom:2mm}}
.price{{font-size:10.5pt}}
.price span{{margin-right:6mm;color:#555}}
.price b{{color:{ORANGE};font-size:12pt}}
.secttl{{padding:6mm 12mm 0;font-size:12pt;font-weight:700;color:{TEAL}}}
.foot{{position:absolute;bottom:0;left:0;right:0;height:8mm;background:#f2f2f2;color:#666;font-size:8pt;display:flex;align-items:center;justify-content:center;border-top:1px solid #e0e0e0}}
"""
    toolcards="".join(tool_card(p) for p in tools) or "<div class='can'>（ツール選択なし）</div>"
    magcards="".join(mag_card(p) for p in mags) or "<div class='can'>（教材選択なし）</div>"
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} {html.escape(ver)}</title><style>{css}</style></head><body>
<section class="page">
  {header('ご提案内容のご案内　'+ver)}
  <div class="body">
    <p class="lead">本書は、株式会社スクーミーの教育用ツールおよび教材「月刊みんなのダイブ」に関するご提案です。選定いただいた構成（ツール{len(tools)}点・教材{len(mags)}点）の内容と価格を以下にまとめております。</p>
    <table class="sum"><tr><th>型番</th><th>品名</th><th class="r">税抜</th><th class="r">税込</th></tr>{rows}</table>
    <div class="total"><div class="lab">合計（{len(tools)+len(mags)}点）</div><div><span class="ex">税抜 {yen(ex)}</span><span class="inc">税込 {yen(inc)}</span></div></div>
  </div>
  {foot}
</section>
<section class="page">
  {header('ご提案内容｜ツール')}
  <div class="secttl">オレンジボードと各種コネクター</div>
  <div class="cards">{toolcards}</div>
  {foot}
</section>
<section class="page">
  {header('ご提案内容｜教材（月刊みんなのダイブ）')}
  <div class="secttl">授業でそのまま使える教材誌</div>
  <div class="cards">{magcards}</div>
  {foot}
</section>
</body></html>"""

def render_pdf(html_path, pdf_path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch()
        pg=b.new_page()
        pg.goto("file://"+os.path.abspath(html_path))
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=pdf_path,format="A4",print_background=True,
               margin={"top":"0","bottom":"0","left":"0","right":"0"})
        b.close()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tools",default="")
    ap.add_argument("--magazines",default="")
    ap.add_argument("--ver",default="v1.2")
    ap.add_argument("--title",default="ご提案書")
    ap.add_argument("--catalog",default=os.path.join(ROOT,"catalog.json"))
    ap.add_argument("--imgdir",default="img")
    ap.add_argument("--logo",default=os.path.join(ROOT,"assets","logo.png"))
    ap.add_argument("--pdf",action="store_true")
    a=ap.parse_args()
    cat=load_catalog(a.catalog)
    def pick(csv):
        out=[]
        for tok in [x.strip() for x in csv.split(",") if x.strip()]:
            m=resolve_model(tok,cat)               # 型番 or 製品名(部分一致) → 型番
            p=dict(cat[m]); p["_img"]=img_data_uri(m,a.imgdir); out.append(p)
        return out
    tools=pick(a.tools); mags=pick(a.magazines)
    logo_uri=logo_data_uri(a.logo)
    if a.logo and not logo_uri:
        print(f"⚠ ロゴ画像が見つかりません（{a.logo}）。ロゴ無しで生成します。", file=sys.stderr)
    html_str=build_html(tools,mags,a.ver,a.title,logo_uri)
    os.makedirs(os.path.join(ROOT,"out"),exist_ok=True)
    hp=os.path.join(ROOT,"out",f"proposal_{a.ver}.html")
    open(hp,"w",encoding="utf-8").write(html_str)
    print("HTML:",hp,f"({len(html_str)//1024} KB)")
    if a.pdf:
        pp=os.path.join(ROOT,"out",f"proposal_{a.ver}.pdf")
        render_pdf(hp,pp); print("PDF :",pp)

if __name__=="__main__":
    main()
