// コード検索: assets/search-index.js の一覧から、入力した文字を含むものを探す。
(function () {
  var root = document.body.getAttribute('data-root') || '';
  var input = document.getElementById('q');
  var box = document.getElementById('results');
  if (!input || !box || !window.CODE_INDEX) return;

  // 全角/半角・大文字小文字・カタカナ/ひらがなの違いを無視して比べる
  function norm(s) {
    return String(s).normalize('NFKC').toLowerCase().replace(/[ァ-ヶ]/g, function (c) {
      return String.fromCharCode(c.charCodeAt(0) - 0x60);
    });
  }
  var items = window.CODE_INDEX.map(function (e) {
    return {
      e: e,
      slug: norm(e.slug),
      tag: norm(e.tag.replace(/[<>]/g, '')),
      title: norm(e.title),
      all: norm([e.slug, e.tag, e.title, e.group, e.summary, e.keywords].join(' '))
    };
  });

  function search(text) {
    var tokens = norm(text).split(/\s+/).filter(Boolean);
    if (!tokens.length) return [];
    var out = [];
    items.forEach(function (it) {
      var score = 0;
      for (var i = 0; i < tokens.length; i++) {
        var t = tokens[i];
        if (it.all.indexOf(t) < 0) return;
        if (it.slug === t || it.tag === t) score += 100;
        else if (it.title.indexOf(t) >= 0) score += 30;
        else if (it.slug.indexOf(t) >= 0) score += 20;
        else score += 5;
      }
      out.push({ it: it, score: score });
    });
    out.sort(function (a, b) { return b.score - a.score; });
    return out.slice(0, 30).map(function (x) { return x.it.e; });
  }

  function show(list, text) {
    box.textContent = '';
    if (!text.trim()) { box.hidden = true; return; }
    if (!list.length) {
      var none = document.createElement('li');
      none.className = 'r-none';
      none.textContent = '見つかりませんでした';
      box.appendChild(none);
    }
    list.forEach(function (e) {
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = root + e.slug + '/';
      var name = document.createElement('span');
      name.textContent = e.title + '  ' + e.tag;
      var sum = document.createElement('span');
      sum.className = 'r-sum';
      sum.textContent = e.summary;
      a.appendChild(name);
      a.appendChild(sum);
      li.appendChild(a);
      box.appendChild(li);
    });
    box.hidden = false;
  }

  input.addEventListener('input', function () { show(search(input.value), input.value); });
  input.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape') { input.value = ''; show([], ''); }
    if (ev.key === 'Enter') {
      var first = box.querySelector('a');
      if (first) { location.href = first.href; }
    }
  });
  document.addEventListener('click', function (ev) {
    if (!box.contains(ev.target) && ev.target !== input) box.hidden = true;
  });
  input.addEventListener('focus', function () { if (input.value.trim()) show(search(input.value), input.value); });

  // ?q=ことば でも検索できる
  var m = /[?&]q=([^&]*)/.exec(location.search);
  if (m) { input.value = decodeURIComponent(m[1].replace(/\+/g, ' ')); show(search(input.value), input.value); }
})();
