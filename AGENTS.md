# AGENTS.md — schoomy-assets（AIエージェント向け必読）

## このリポジトリの役割
**SchooMy製品データの唯一のマスター（single source of truth）= `catalog.json`**

製品の価格・型番・アイコン・画像・説明に関する作業（見積もり、価格表、提案書、資料作成など）では、
**推測やユーザーへの聞き返しをする前に、必ず `catalog.json` を読むこと。**

## catalog.json（v1.4〜）の内容
- 全58製品：`model`（型番）/ `name` / `type` / `category` / `priceExTax`（税別）/ `priceIncTax`（税込）/ `jan` / `can`（説明）/ `image`（`img/<model>.png`）
- 40コネクターには `guide` オブジェクト：`iconUrl`（アイコン）/ `iconBgUrl`（アイコン背景）/ `photoUrl`（製品写真）/ `subtitle`・`highlight1`・`highlight2`（解説文）/ `guideUrl`（コネクターガイドページ）
- 元データ：価格系シート（meta.sourceSheet）＋コネクターガイドシート（meta.guideSheet = 1GNtC9TVw9NrYIDE4geTGlbUY-BGSP-RBEPo9TwD2RfM）

## 製品アイコン（icons/）
- コネクター：`icons/S-CN-*.svg`
- オレンジボード：`icons/S-BD-AA1.svg`（背景なし。納品アイコン Scoomy_nouhin_01_OB_nobg.svg と同じもの。周りが黒い icon-orangeboard.png は使わない）
- 書き込み機（オレンジボード専用・S-UT-AA1）：`icons/S-UT-AA1.svg`（= `icons/board_o_usb_flasher.svg`・黒い基板）
- ブルーボード用の書き込み機：`icons/board_blue_usb_flasher.svg`（青い基板）
- 資料・図版で製品を描くときは、写真（img/）より先にこのアイコンを使う（2026-10-28 塩島さん）

## 禁止事項
1. **価格・単価を推測で置かない。**「参考値」「概算」も禁止。catalog.jsonの `priceExTax` / `priceIncTax` のみを使う。
2. 存在しない型番を作らない。書き込み機は **S-UT-AA1**（S-WR-AA1という型番は存在しない）。
3. catalog.jsonに該当製品がない場合のみ、ユーザー（塩島）に確認する。

## 取得方法
```
GET https://api.github.com/repos/shiojima-test/schoomy-assets/contents/catalog.json
→ content を base64 デコード
```

## 更新ルール
- catalog.jsonを更新したら meta.version を必ず上げる（v1.4 → v1.5）
- 更新後はAPIで再取得してバージョン反映を確認してから完了報告
