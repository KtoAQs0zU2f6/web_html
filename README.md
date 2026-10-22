# HTML・CSS コード図鑑

公開URL: https://KtoAQs0zU2f6.github.io/web_html/

## 更新のしかた
1. `content/*.txt` に、コードのブロックを足す・直す(書式は `content/01-structure-sectioning.txt` の先頭を参照)
2. `python3 build.py` を実行する(Python 3 だけで動きます)
3. 変更したファイルを GitHub にプッシュする(`index.html` と各 `コード名/` フォルダは生成物ですが、GitHub Pages で公開するためリポジトリに含めます)

## 解説の確認
- 各ブロックに `reviewed: yes` を書くと、そのページの「確認前」の表示が消えます。
- 表示を全体でオフにするには、`build.py` の `SHOW_UNREVIEWED_BADGE = False` にします。

## 設定
サイト名・URL・グループの並び順は `build.py` の先頭にあります。

## GitHub Pages
リポジトリの Settings → Pages で、公開元を `main` ブランチのルートにします。
