// 解説ページ用: コードのコピーボタンと「試してみる」欄の動き。
(function () {
  var root = document.body.getAttribute('data-root') || '';

  // コピーボタン
  var buttons = document.querySelectorAll('.copy');
  Array.prototype.forEach.call(buttons, function (btn) {
    btn.addEventListener('click', function () {
      var pre = document.getElementById(btn.getAttribute('data-target'));
      if (!pre) return;
      var text = pre.textContent;
      function done(ok) {
        var old = btn.textContent;
        btn.textContent = ok ? 'コピーしました' : 'コピーできませんでした';
        setTimeout(function () { btn.textContent = old; }, 1500);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      } else {
        var ta = document.createElement('textarea');
        ta.value = text; document.body.appendChild(ta); ta.select();
        var ok = false;
        try { ok = document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
        done(ok);
      }
    });
  });

  // 試してみる欄(build.py の preview_doc と同じ規則で文書を作る)
  var h = document.getElementById('pg-html');
  var c = document.getElementById('pg-css');
  var f = document.getElementById('pg-frame');
  var reset = document.getElementById('pg-reset');
  if (!h || !c || !f) return;

  function buildDoc() {
    var html = h.value.split('sample.svg').join(root + 'assets/sample.svg');
    if (/<html/i.test(html)) return html;
    return '<!doctype html><html lang="ja"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<style>body{font-family:sans-serif;margin:12px;line-height:1.6}</style>' +
      '<style>' + c.value + '</style></head><body>' + html + '</body></html>';
  }
  var timer;
  function update() { clearTimeout(timer); timer = setTimeout(function () { f.srcdoc = buildDoc(); }, 250); }
  h.addEventListener('input', update);
  c.addEventListener('input', update);
  if (reset) reset.addEventListener('click', function () {
    h.value = h.defaultValue; c.value = c.defaultValue; f.srcdoc = buildDoc();
  });
})();
