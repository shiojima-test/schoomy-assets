# schoomy-assets

SchooMy 提案資料の「写真入りHTML自動生成」基盤。型番を渡すだけで、写真・型番・税抜/税込が入ったA4×3ページの提案HTMLを生成する。

## 構成
- `catalog.json` … 全62品目のマスター（型番・区分・正式名称・税抜/税込・JAN・できること・画像パス・photoFileId）
- `img/<型番>.png` … 製品写真（長辺1200px）
- `fonts/` … M PLUS 1p（Regular/Bold、サブセット元）
- `build_proposal.py` … 提案HTML生成エンジン
- `harvest_images.py` … Driveから全画像を一括取得（Mac等、Driveに到達できる環境で1回実行）
- `build_catalog.py` … catalog.json の再生成
- `assets/logo.png` … SchooMyロゴ（各ページ右上に base64 埋め込み）

## 画像の取得（初回のみ）
```
pip install requests pillow fonttools playwright pypdf
python harvest_images.py        # img/ に全画像を取得（公開URL）
```
※ Driveが「リンクを知っている全員」公開である前提。非公開なら harvest_images.py の fetch() を rclone 等の認証に差し替える。

## 提案書を作る
```
python build_proposal.py --tools S-BD-AA1,S-CN-A10,S-UT-AA1 --magazines S-MZ-A16 --ver v1.1 --pdf
```
- `--tools` … ツール（カンマ区切り）。**製品名で指定可**（catalog.json の `name` → `model`、部分一致。型番完全一致を優先し、無ければ名前で解決。複数一致は型番指定を促してエラー）。
- `--magazines` … 教材（カンマ区切り）。同上で製品名指定可。
- `--ver` … バージョン（ファイル名・`<title>`・画面表示に反映）
- `--logo` … ロゴ画像パス（既定 `assets/logo.png`）。**各ページ右上にSchooMyロゴ**を base64 で埋め込み。無ければロゴ無しで生成（フォールバック）。
- `--pdf` … PDFも出力（A4・3ページ）
- 出力: `out/proposal_<ver>.html` / `out/proposal_<ver>.pdf`
- **画像が無ければ先に `python harvest_images.py` を実行**（未取得だとプレースホルダ画像になる）。

## 写真未登録の型番
`S-MZ-A01 / S-MZ-A07 / S-MZ-A08 / S-MZ-A10`（教材4点）。提案に含めるとブランド準拠のプレースホルダ画像になる。

## ブランド
teal #3AABA8 / cream #F5E4C4 / orange #E88A0A / blue #2E8EC4。黒ヘッダーバンド（右上にSchooMyロゴ）＋オレンジサブバー＋カード＋フッター。絵文字なし。英語表記は "SchooMy"。フォントは M PLUS 1p（埋め込み）/ メイリオ（フォールバック）。
