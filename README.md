# schoomy-assets

SchooMy 提案資料の「写真入りHTML自動生成」基盤。型番でも製品名でも渡すだけで、写真・型番・名前・金額が必ず入った
self-contained な提案HTML（写真/フォント/ロゴを base64 埋め込み）を生成する。
出力は**1枚物の縦長Webページ**（A4・改ページ非依存、ヘッダー/フッターは各1回、max-width 980px 中央寄せ・レスポンシブ）。

## 構成
- `catalog.json` … 全58品目のマスター（型番・区分・正式名称・税抜/税込・JAN・できること・画像パス・photoFileId）。
  教材（月刊みんなのダイブ）は各 `dive` に全項目（大見出しキャッチ/監修/ピックアップセンサー/対応教科/対象学年/コマ数/
  機材/外部接続/特徴/説明/身につく力1-3/おすすめ 等）を保持。
- `dive_master.json` … ダイブ全項目スナップショット（Google Sheet「月刊みんなのダイブ_デザインリスト」
  ID `13yXVppzgcE0NyY0ATZ7JdiCaYtNzBJ4wMVH_1HBEopk` を持続化したもの）。build_catalog.py がこれを catalog.json に統合。
- `img/<型番>.png` … 製品写真（長辺1200px）
- `fonts/` … M PLUS 1p（Regular/Bold、サブセット元）
- `build_proposal.py` … 提案HTML生成エンジン
- `harvest_images.py` … Driveから全画像を一括取得（Mac等、Driveに到達できる環境で1回実行）
- `build_catalog.py` … catalog.json の再生成（dive_master.json を統合。実行時にシートは読まない）
- `assets/logo.png` … SchooMyロゴ（ヘッダー右上に base64 埋め込み）

## 画像の取得（初回のみ）
```
pip install requests pillow fonttools playwright pypdf
python harvest_images.py        # img/ に全画像を取得（公開URL）
```
※ Driveが「リンクを知っている全員」公開である前提。非公開なら harvest_images.py の fetch() を rclone 等の認証に差し替える。
※ 透過PNG（多くのセンサー写真は角丸の透明背景）は**必ず白でフラット化**して保存する（`convert('RGB')` だけだと
　 透明部分のRGB=0がそのまま黒帯になるため）。Exif回転も反映。これらは `harvest_images.py` の `to_rgb_on_white()` で処理。

## 提案書を作る（既定はHTMLのみ）
```
# 型番でも製品名/通称/キーワードでもOK。数量や号の通称も指定できる
python build_proposal.py \
  --tools "オレンジボード2個,加速度センサー,スイッチ,湿度センサー,OLED,延長ケーブル,書き込み機2個" \
  --magazines "冷蔵庫,通学路" --ver v1.4
```
- **柔軟な名前解決**: `--tools` / `--magazines` は型番でも製品名でも、表記ゆれ・部分一致で型番に解決。
  - 通称・略称も可（例「スイッチ」→S-CN-A02、「湿度センサー」→S-CN-B04、「OLED」→S-CN-B19、「延長ケーブル」→S-CB-A02）。
  - ダイブ号は号名・通称・キーワードで特定（例「冷蔵庫」→S-MZ-A05、「通学路」→S-MZ-A13、「p5.js」→S-MZ-A19）。
  - 判定順: 型番完全一致 → 通称完全一致 → 製品名完全一致 → 名称部分一致 → can/ダイブ詳細のキーワード一致。
  - **一意に決まらない場合は候補一覧を提示して安全に停止**（誤った型番を勝手に確定しない）。
- **数量指定**: `名前:2` / `名前×2` / `S-UT-AA1*2` / `オレンジボード2個` / `オレンジボード2`。未指定は1個（後方互換）。
  カードに数量を表示し、合計は (単価×数量) で税抜/税込を再計算。
- **必ず入る4点**: どんな指示でも各カードに「名前・型番・金額（数量反映）・画像」が入る。画像が無ければプレースホルダ。
- **写真の扱い**: ツールは正方形（センタークロップ・サムネは黒枠/影なし・背景white）、教材表紙は元比率のまま（トリミングなし）。
- **出力形態**: 1枚物の縦長Webページ（A4/改ページ非依存）。ヘッダーは最上部に1回・フッターは最下部に1回、max-width 980px 中央寄せ・レスポンシブ。
- `--ver` … バージョン（ファイル名・`<title>`・画面ヘッダー/サブバー/フッターすべてに反映）
- `--logo` … ロゴ画像パス（既定 `assets/logo.png`）。**ヘッダー右上にSchooMyロゴ**（px指定で大きめ）を base64 で埋め込み。無ければロゴ無しで生成。
- **既定はHTMLのみ出力（PDFは作らない）。** `--pdf` を明示したときだけ PDF を生成し、未指定では Chromium 等の重い処理も走らせない。
- `--pdf` … このフラグを付けたときだけ `out/proposal_<ver>.pdf` も生成（PDF生成コードは温存）。
- 出力: `out/proposal_<ver>.html`（`--pdf` 指定時のみ `out/proposal_<ver>.pdf` も）
- **画像が無ければ先に `python harvest_images.py` を実行**（未取得だとプレースホルダ画像になる）。

## ダイブのデータ更新
ダイブ号の全項目は `dive_master.json`（Sheet スナップショット）に保持し、`python build_catalog.py` で `catalog.json` に統合する。
提案生成（build_proposal.py）は `catalog.json` のみ参照し、実行時に Google Sheet を読まない。表示する項目は絞ってよい
（毎回の指示でデザイン/掲載情報が変わる前提）。

## 写真未登録の型番
現行カタログ（58点）は全点に写真登録済み。未登録の型番を含めた場合はブランド準拠のプレースホルダ画像になる。

## ブランド
navy #1F2A30 / teal #3AABA8 / cream #F5E4C4 / orange #E88A0A / blue #2E8EC4。
「開発事業紹介」PDFに準拠：濃紺ヘッダー帯（白タイトル＋右上ロゴ＋直下のオレンジ細ライン）、濃紺フッター帯
（オレンジ「お問い合わせ」ラベル＋担当/TEL/Email、最下部に「© SchooMy, Inc. 株式会社スクーミー」と「fox.schoomy.com」）。
既定の問い合わせ先は髙坂さん（`DEFAULT_CONTACT` 定数、`--contact-person/--contact-tel/--contact-email` で上書き可）。
絵文字なし。英語表記は "SchooMy"。フォントは M PLUS 1p（埋め込み）/ メイリオ（フォールバック）。
