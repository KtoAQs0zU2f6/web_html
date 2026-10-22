#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML・CSS コード図鑑 サイト生成スクリプト

使い方:  python3 build.py

content/*.txt に書いた内容と templates/ のテンプレートから、次のファイルを作ります。
  index.html                    トップ(検索・一覧)
  404.html                      存在しないURLのページ
  <コード名>/index.html         各解説ページ  → サイトURL/<コード名>/
  assets/search-index.js        検索用データ
  sitemap.xml                   サイトマップ
Python 3 の標準ライブラリだけで動きます(追加インストール不要)。
"""
import html as H
import json
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent

# ───────── 設定 ─────────
SITE_NAME = "HTML・CSS コード図鑑"
SITE_DESC = "目的からHTMLとCSSのコードを探し、解説を読み、その場で試せるコード集。"
BASE_URL = "https://KtoAQs0zU2f6.github.io/web_html"
# True の間は、reviewed: yes が付いていない解説ページに「確認前」の表示を出す
SHOW_UNREVIEWED_BADGE = True
MDN_ELEMENT_URL = "https://developer.mozilla.org/ja/docs/Web/HTML/Reference/Elements/{tag}"

# 表示順とグループ名。(id, 表示名, 種類)  種類: element=HTML要素 / part=部品 / layout=CSSレイアウト
GROUPS = [
    ("structure", "文書の基本構造", "element"),
    ("metadata", "文書メタデータ", "element"),
    ("sectioning", "セクション(ページの区分け)", "element"),
    ("textblock", "テキストのブロック", "element"),
    ("inline", "文中のテキスト", "element"),
    ("media", "画像・音声・動画", "element"),
    ("embed", "埋め込み・図形", "element"),
    ("scripting", "スクリプト・描画", "element"),
    ("edits", "変更の表示", "element"),
    ("table", "表", "element"),
    ("form", "フォーム", "element"),
    ("interactive", "操作できる要素", "element"),
    ("components", "Web Components", "element"),
    ("parts", "よく使う部品", "part"),
    ("layout", "CSSレイアウト", "layout"),
]
KIND_LABEL = {"element": "HTML要素", "part": "部品", "layout": "CSSレイアウト"}

BASE_PATH = urlparse(BASE_URL).path.rstrip("/")  # 例: /web_html
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REQUIRED = ["tag", "title", "group", "summary", "keywords"]


def fail(msg):
    print("エラー: " + msg, file=sys.stderr)
    sys.exit(1)


# ───────── content/*.txt の読み込み ─────────
def parse_file(path):
    entries, cur, sec = [], None, None
    for ln, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if raw.startswith("@@ "):
            cur = {"slug": raw[3:].strip(), "_src": f"{path.name}:{ln}", "sections": {}}
            entries.append(cur)
            sec = None
            continue
        if cur is None:
            if raw.strip() and not raw.startswith("#"):
                fail(f"{path.name}:{ln} 最初の '@@ コード名' より前に文字があります")
            continue
        if raw.startswith(">> "):
            sec = raw[3:].strip()
            cur["sections"][sec] = []
            continue
        if sec is None:
            if not raw.strip() or raw.startswith("#"):
                continue
            k, _, v = raw.partition(":")
            cur[k.strip()] = v.strip()
        else:
            cur["sections"][sec].append(raw)
    for e in entries:
        for k, lines in e["sections"].items():
            e["sections"][k] = "\n".join(lines).strip("\n")
    return entries


def load_entries():
    files = sorted((ROOT / "content").glob("*.txt"))
    if not files:
        fail("content/ に .txt がありません")
    entries, seen = [], {}
    for f in files:
        for e in parse_file(f):
            s = e["slug"]
            if not SLUG_RE.match(s):
                fail(f"{e['_src']} コード名 '{s}' は小文字英数字とハイフンだけにしてください")
            if s in seen:
                fail(f"{e['_src']} コード名 '{s}' が重複しています(もう一方: {seen[s]})")
            seen[s] = e["_src"]
            for k in REQUIRED:
                if not e.get(k):
                    fail(f"{e['_src']} '{s}' に '{k}:' がありません")
            for k in e["sections"]:
                if k not in ("explain", "html", "css", "notes"):
                    fail(f"{e['_src']} '{s}' 不明なセクション '>> {k}'")
            if not e["sections"].get("explain") or not e["sections"].get("html"):
                fail(f"{e['_src']} '{s}' には '>> explain' と '>> html' が必要です")
            gid = e["group"]
            if gid not in {g[0] for g in GROUPS}:
                fail(f"{e['_src']} '{s}' 不明なグループ '{gid}'")
            e["summary"] = e["summary"].replace("`", "")
            e["related_list"] = [x.strip() for x in e.get("related", "").split(",") if x.strip()]
            entries.append(e)
    for e in entries:
        for r in e["related_list"]:
            if r not in seen:
                fail(f"{e['_src']} '{e['slug']}' の related '{r}' が存在しません")
    order = {g[0]: i for i, g in enumerate(GROUPS)}
    idx = {e["slug"]: i for i, e in enumerate(entries)}
    entries.sort(key=lambda e: (order[e["group"]], idx[e["slug"]]))
    return entries


# ───────── HTML 組み立て ─────────
def esc(s):
    return H.escape(s, quote=True)


def inline_code(s):
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", esc(s))


def paragraphs(text):
    out = []
    for block in re.split(r"\n\s*\n", text.strip()):
        out.append("<p>" + inline_code(" ".join(block.split("\n"))) + "</p>")
    return "\n".join(out)


def bullets(text):
    items = [ln[2:].strip() for ln in text.splitlines() if ln.startswith("- ")]
    return "<ul>" + "".join(f"<li>{inline_code(i)}</li>" for i in items) + "</ul>"


def preview_doc(html_src, css_src, root):
    """試す場所と同じ規則で、プレビュー用の完全なHTML文書を作る(assets/playground.js と同じ)。"""
    h = html_src.replace("sample.svg", root + "assets/sample.svg")
    if "<html" in h.lower():
        return h
    return (
        '<!doctype html><html lang="ja"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<style>body{font-family:sans-serif;margin:12px;line-height:1.6}</style>"
        "<style>" + css_src + "</style></head><body>" + h + "</body></html>"
    )


def render(template, mapping):
    out = template
    for k, v in mapping.items():
        out = out.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{[a-z_]+\}\}", out)
    if left:
        fail("テンプレートに未置換の項目があります: " + ", ".join(sorted(set(left))))
    return out


def build_page(e, by_slug, tpl):
    s = e["slug"]
    root = "../"
    sec = e["sections"]
    html_src, css_src = sec["html"], sec.get("css", "")
    kind = next(g[2] for g in GROUPS if g[0] == e["group"])
    group_label = next(g[1] for g in GROUPS if g[0] == e["group"])

    css_block = ""
    if css_src:
        css_block = (
            '<div class="codeblock"><div class="bar"><span>CSS</span>'
            '<button type="button" class="copy" data-target="code-css">コピー</button></div>'
            f'<pre id="code-css"><code>{esc(css_src)}</code></pre></div>'
        )
    notes_block = ""
    if sec.get("notes"):
        notes_block = '<section><h2>注意点</h2>' + bullets(sec["notes"]) + "</section>"
    related_block = ""
    if e["related_list"]:
        lis = "".join(
            f'<li><a href="../{r}/"><code>{esc(by_slug[r]["tag"])}</code> {esc(by_slug[r]["title"])}</a></li>'
            for r in e["related_list"]
        )
        related_block = f'<section><h2>関連コード</h2><ul class="related">{lis}</ul></section>'
    mdn_block = ""
    mdn = e.get("mdn", e["tag"].strip("<>") if kind == "element" else "none")
    if mdn != "none":
        url = MDN_ELEMENT_URL.format(tag=mdn)
        mdn_block = f'<p class="mdn">さらに詳しい仕様: <a href="{esc(url)}" rel="noopener">MDN Web Docs</a></p>'
    badge = ""
    if SHOW_UNREVIEWED_BADGE and e.get("reviewed", "no") != "yes":
        badge = '<p class="badge-unreviewed">この解説は確認前です。内容に誤りがある可能性があります。</p>'

    if "nopreview" in e:
        preview_block = f'<section><h2>実行結果</h2><p class="nopreview">{esc(e["nopreview"])}</p></section>'
        try_block = ""
    else:
        srcdoc = esc(preview_doc(html_src, css_src, root))
        preview_block = (
            '<section><h2>実行結果</h2>'
            f'<iframe class="preview" title="実行結果" sandbox="allow-scripts" srcdoc="{srcdoc}"></iframe></section>'
        )
        try_block = (
            '<section id="playground" class="playground"><h2>試してみる</h2>'
            "<p>左の欄を書き換えると、右の結果がすぐ変わります。</p>"
            '<div class="pg-grid"><div class="pg-edit">'
            '<label for="pg-html">HTML</label>'
            f'<textarea id="pg-html" spellcheck="false" autocomplete="off">{esc(html_src)}</textarea>'
            '<label for="pg-css">CSS</label>'
            f'<textarea id="pg-css" spellcheck="false" autocomplete="off">{esc(css_src)}</textarea>'
            '<button type="button" id="pg-reset">元に戻す</button></div>'
            '<div class="pg-out"><iframe id="pg-frame" class="preview" title="試す場所の結果" '
            f'sandbox="allow-scripts" srcdoc="{srcdoc}"></iframe></div></div></section>'
        )

    return render(tpl, {
        "site_name": esc(SITE_NAME),
        "title": esc(e["title"]),
        "slug": esc(s),
        "tag": esc(e["tag"]),
        "kind": esc(KIND_LABEL[kind]),
        "group": esc(group_label),
        "summary": esc(e["summary"]),
        "root": root,
        "canonical": esc(f"{BASE_URL}/{s}/"),
        "badge": badge,
        "explain_html": paragraphs(sec["explain"]),
        "html_code": esc(html_src),
        "css_block": css_block,
        "preview_block": preview_block,
        "try_block": try_block,
        "notes_block": notes_block,
        "related_block": related_block,
        "mdn_block": mdn_block,
    })


def build_index(entries, tpl):
    parts = []
    for gid, label, kind in GROUPS:
        items = [e for e in entries if e["group"] == gid]
        if not items:
            continue
        lis = "".join(
            f'<li><a href="{e["slug"]}/"><code>{esc(e["tag"])}</code> {esc(e["title"])}</a>'
            f'<span class="sum">{esc(e["summary"])}</span></li>'
            for e in items
        )
        parts.append(
            f'<section class="group" id="g-{gid}"><h2>{esc(label)}<small>{esc(KIND_LABEL[kind])}・{len(items)}件</small></h2>'
            f'<ul class="list">{lis}</ul></section>'
        )
    toc = "".join(
        f'<a href="#g-{gid}">{esc(label)}</a>'
        for gid, label, _ in GROUPS
        if any(e["group"] == gid for e in entries)
    )
    return render(tpl, {
        "site_name": esc(SITE_NAME),
        "site_desc": esc(SITE_DESC),
        "root": "",
        "canonical": esc(BASE_URL + "/"),
        "count": str(len(entries)),
        "toc": toc,
        "groups_html": "\n".join(parts),
    })


def build_404(tpl):
    return render(tpl, {
        "site_name": esc(SITE_NAME),
        "root": BASE_PATH + "/",
    })


def main():
    entries = load_entries()
    by_slug = {e["slug"]: e for e in entries}
    tpl_page = (ROOT / "templates" / "page.html").read_text(encoding="utf-8")
    tpl_index = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    tpl_404 = (ROOT / "templates" / "404.html").read_text(encoding="utf-8")

    # 前回作ったフォルダのうち、いまは無いコード名のものを消す
    manifest = ROOT / ".build-manifest.json"
    old = json.loads(manifest.read_text(encoding="utf-8")) if manifest.exists() else []
    for s in old:
        if s not in by_slug and SLUG_RE.match(s):
            shutil.rmtree(ROOT / s, ignore_errors=True)

    reserved = {"assets", "content", "templates"}
    for e in entries:
        s = e["slug"]
        if s in reserved:
            fail(f"コード名 '{s}' は使えません(予約済み)")
        d = ROOT / s
        d.mkdir(exist_ok=True)
        (d / "index.html").write_text(build_page(e, by_slug, tpl_page), encoding="utf-8")
    manifest.write_text(json.dumps(sorted(by_slug), ensure_ascii=False), encoding="utf-8")

    (ROOT / "index.html").write_text(build_index(entries, tpl_index), encoding="utf-8")
    (ROOT / "404.html").write_text(build_404(tpl_404), encoding="utf-8")

    gl = {g[0]: g[1] for g in GROUPS}
    index = [
        {
            "slug": e["slug"], "tag": e["tag"], "title": e["title"],
            "group": gl[e["group"]], "summary": e["summary"], "keywords": e["keywords"],
        }
        for e in entries
    ]
    (ROOT / "assets" / "search-index.js").write_text(
        "window.CODE_INDEX = " + json.dumps(index, ensure_ascii=False, indent=0) + ";\n", encoding="utf-8"
    )
    urls = [BASE_URL + "/"] + [f"{BASE_URL}/{e['slug']}/" for e in entries]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{u}</loc></url>\n" for u in urls) + "</urlset>\n",
        encoding="utf-8",
    )
    unrev = sum(1 for e in entries if e.get("reviewed", "no") != "yes")
    print(f"完了: {len(entries)} ページを作成しました(確認前の解説: {unrev} 件)")


if __name__ == "__main__":
    main()
