# IG投稿用画像（note連動Instagram自動投稿システム）

このディレクトリは **Instagramに画像を配信するための公開ホスティング** です。

- 正本のマニフェスト `ig.json` は非公開リポジトリ `shiojima-test/schoomy-note-queue` の
  `posted/<slug>/ig/ig.json` にあります。ここには**画像ファイルのみ**を置きます。
- Instagram Graph APIは公開URLからしか画像を取得できません。schoomy-note-queue は private のため
  raw URLが404になり、code 9004（Only photo or video can be accepted）で失敗します。
  そのため画像だけをこの公開リポジトリにミラーします。
- 配信URL: `https://raw.githubusercontent.com/shiojima-test/schoomy-assets/main/ig/<slug>/<file>`

## 記事作成セッションの義務
新しいnote記事の `ig/` アセットを作ったら、**画像は必ずここにも push する**こと。
push漏れがあると ig_post.py の起動時チェックで警告され、その記事は投稿対象から外れます。
