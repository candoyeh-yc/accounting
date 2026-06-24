#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
會計師考試教材 → 單檔 HTML 學習網站建置腳本
用法：python3 build_site.py
會掃描本資料夾下的 .md，產出 index.html（左側導覽切換頁面、離線可用）。
改完 md 重跑即可更新。
"""
import os, base64, json, re

ROOT = os.path.dirname(os.path.abspath(__file__))
MARKED_PATH = os.path.join(ROOT, "marked.min.js")  # 內嵌（repo 內，離線可用）；找不到才 fallback CDN

# 導覽列短標題覆寫（不設則自動取 H1「｜」後段）。改這裡即可改側邊欄標題。
NAV_OVERRIDE = {
    "00_審計學_考點地圖": "考點頻率地圖",
    "00a_審計學_查核流程全景圖": "查核流程全景圖",
    "00b_審計學_核心速覽_先讀這張": "核心速覽卡",
    "00c_審計學_記憶口訣卡": "記憶口訣卡",
    "03_三法_深掘_證券交易法": "證券交易法★★★",
    "04_三法_深掘_商業會計法": "商業會計法★★★",
    "10_稅務_現行數字速查表": "現行數字速查表",
    "12_稅務_深掘_所得稅_AMT_CFC": "所得稅法・AMT・CFC★★★",
    "13_稅務_深掘_遺產及贈與稅": "遺產及贈與稅★★★",
    "13b_稅務_深掘_不動產稅": "不動產稅（房地合一・土增・地價）★★★",
    "14_稅務_深掘_營業稅與稽徵程序": "營業稅・稅捐稽徵法・納稅者權利保護法 ★★★",
}

# 科目分組與顯示順序（'' = 根目錄）
GROUPS = [
    ("", "📋 讀書計劃", ""),
    ("審計學", "🔍 審計學", "審計學"),
    ("三法", "⚖️ 三法", "三法"),
    ("稅務法規", "💰 稅務法規", "稅務法規"),
]

def first_h1(text):
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return None

def collect():
    groups = []
    docs = {}
    for folder, label, _ in GROUPS:
        d = os.path.join(ROOT, folder) if folder else ROOT
        if not os.path.isdir(d):
            continue
        files = [f for f in os.listdir(d) if f.endswith(".md")]
        # 根目錄只收頂層 md（不遞迴）
        files.sort()
        items = []
        for f in files:
            path = os.path.join(d, f)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            doc_id = f[:-3]  # 去 .md
            h1 = first_h1(content) or doc_id
            nav = NAV_OVERRIDE.get(doc_id, h1.split("｜")[-1].strip())
            docs[doc_id] = base64.b64encode(content.encode("utf-8")).decode("ascii")
            items.append({"id": doc_id, "nav": nav, "title": h1})
        if items:
            groups.append({"label": label, "items": items})
    return groups, docs

def build_nav(groups):
    out = []
    for g in groups:
        out.append('<div class="nav-group"><div class="nav-group-title">%s</div>' % g["label"])
        for it in g["items"]:
            out.append('<a class="nav-link" data-id="%s" href="#%s">%s</a>' % (it["id"], it["id"], it["nav"]))
        out.append('</div>')
    return "\n".join(out)

def marked_js():
    if os.path.exists(MARKED_PATH):
        with open(MARKED_PATH, "r", encoding="utf-8") as fh:
            return "<script>\n" + fh.read() + "\n</script>"
    return '<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>'

groups, docs = collect()
first_id = groups[0]["items"][0]["id"] if groups and groups[0]["items"] else ""
nav_html = build_nav(groups)
docs_json = json.dumps(docs, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>會計師考試 · 重點教材</title>
__MARKED__
<style>
:root{
  --bg:#f6f7f9; --sidebar:#1e293b; --sidebar2:#0f172a; --accent:#2563eb;
  --text:#1f2937; --muted:#94a3b8; --line:#e5e7eb; --card:#ffffff;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,-apple-system,"Segoe UI",sans-serif;
  color:var(--text); background:var(--bg); line-height:1.85; font-size:16px;
}
/* ===== sidebar ===== */
#sidebar{
  position:fixed; top:0; left:0; width:288px; height:100vh; overflow-y:auto;
  background:linear-gradient(180deg,var(--sidebar),var(--sidebar2)); color:#cbd5e1;
  padding:18px 0 60px; z-index:30;
}
#sidebar .brand{
  padding:6px 22px 16px; color:#fff; font-weight:800; font-size:19px; letter-spacing:.5px;
  border-bottom:1px solid rgba(255,255,255,.08); margin-bottom:10px;
}
#sidebar .brand small{display:block;color:var(--muted);font-weight:500;font-size:12px;margin-top:4px}
#search{
  width:calc(100% - 32px); margin:0 16px 14px; padding:9px 12px; border-radius:9px; border:none;
  background:rgba(255,255,255,.08); color:#fff; font-size:14px; outline:none;
}
#search::placeholder{color:#7c8aa0}
.nav-group{margin:6px 0 12px}
.nav-group-title{
  padding:8px 22px 5px; font-size:12px; font-weight:800; color:#7c8aa0;
  text-transform:uppercase; letter-spacing:1px;
}
.nav-link{
  display:block; padding:7px 22px 7px 26px; color:#cbd5e1; text-decoration:none;
  font-size:13.5px; border-left:3px solid transparent; transition:.12s;
}
.nav-link:hover{background:rgba(255,255,255,.06); color:#fff}
.nav-link.active{background:rgba(37,99,235,.22); color:#fff; border-left-color:var(--accent); font-weight:600}
.nav-link.hidden{display:none}
/* ===== content ===== */
#main{margin-left:288px; padding:34px 48px 120px; min-height:100vh}
#content{max-width:880px; margin:0 auto; background:var(--card); padding:40px 52px 60px;
  border-radius:16px; box-shadow:0 1px 3px rgba(0,0,0,.05),0 8px 30px rgba(0,0,0,.04)}
#content h1{font-size:27px; font-weight:800; margin:.2em 0 .7em; padding-bottom:.4em; border-bottom:3px solid var(--accent); line-height:1.4}
#content h2{font-size:21px; font-weight:800; margin:1.6em 0 .6em; color:#0f172a; border-left:5px solid var(--accent); padding-left:12px}
#content h3{font-size:17px; font-weight:700; margin:1.3em 0 .5em; color:#1e293b}
#content p{margin:.6em 0}
#content ul,#content ol{margin:.5em 0; padding-left:1.5em}
#content li{margin:.28em 0}
#content a{color:var(--accent); text-decoration:none; border-bottom:1px solid rgba(37,99,235,.35)}
#content a:hover{background:rgba(37,99,235,.08)}
#content strong{color:#b91c1c; font-weight:700}
#content blockquote{
  margin:1em 0; padding:.7em 1.1em; background:#f1f5f9; border-left:4px solid #64748b;
  border-radius:0 8px 8px 0; color:#334155; font-size:14.5px;
}
#content blockquote p{margin:.3em 0}
#content code{background:#eef2ff; color:#3730a3; padding:.1em .4em; border-radius:5px; font-size:.88em;
  font-family:"SF Mono",Menlo,Consolas,monospace}
#content pre{background:#0f172a; color:#e2e8f0; padding:16px 18px; border-radius:10px; overflow-x:auto; font-size:13px}
#content pre code{background:none; color:inherit; padding:0}
#content table{border-collapse:collapse; width:100%; margin:1.1em 0; font-size:14px; display:block; overflow-x:auto}
#content thead th{background:#1e293b; color:#fff; font-weight:700}
#content th,#content td{border:1px solid var(--line); padding:9px 12px; text-align:left; vertical-align:top}
#content tbody tr:nth-child(even){background:#f8fafc}
#content hr{border:none; border-top:1px dashed #cbd5e1; margin:1.8em 0}
/* mobile */
#menu-btn{display:none; position:fixed; top:14px; left:14px; z-index:40; background:var(--sidebar2); color:#fff;
  border:none; width:44px; height:44px; border-radius:10px; font-size:20px; cursor:pointer}
#overlay{display:none; position:fixed; inset:0; background:rgba(0,0,0,.4); z-index:25}
@media(max-width:860px){
  #sidebar{transform:translateX(-100%); transition:.25s; width:280px}
  #sidebar.open{transform:translateX(0)}
  #menu-btn{display:block}
  #overlay.show{display:block}
  #main{margin-left:0; padding:70px 16px 80px}
  #content{padding:26px 20px 40px}
}
#totop{position:fixed;right:26px;bottom:26px;z-index:50;width:48px;height:48px;border-radius:50%;
  border:none;background:var(--accent);color:#fff;font-size:19px;cursor:pointer;opacity:0;visibility:hidden;
  transition:.2s;box-shadow:0 4px 16px rgba(37,99,235,.45)}
#totop.show{opacity:.92;visibility:visible}
#totop:hover{opacity:1;transform:translateY(-2px)}
@media(max-width:860px){#totop{right:16px;bottom:16px;width:44px;height:44px;font-size:17px}}
</style>
</head>
<body>
<button id="menu-btn">☰</button>
<div id="overlay"></div>
<nav id="sidebar">
  <div class="brand">會計師考試<small>重點整理 · 點左側切換</small></div>
  <input id="search" placeholder="🔎 篩選頁面…" autocomplete="off">
  __NAV__
</nav>
<div id="main"><div id="content"></div></div>
<button id="totop" aria-label="回頂端" title="回頂端">▲</button>

<script>
var DOCS = __DOCS__;
function b64utf8(b){return new TextDecoder().decode(Uint8Array.from(atob(b),function(c){return c.charCodeAt(0)}))}
if(window.marked && marked.setOptions){marked.setOptions({gfm:true,breaks:false});}
var contentEl=document.getElementById('content');
var links=Array.prototype.slice.call(document.querySelectorAll('.nav-link'));
var ids={}; links.forEach(function(a){ids[a.dataset.id]=true});

function render(id,push){
  var b=DOCS[id]; if(!b)return;
  var md=b64utf8(b);
  contentEl.innerHTML=
    (window.marked?(marked.parse?marked.parse(md):marked(md)):('<pre>'+md.replace(/</g,'&lt;')+'</pre>'));
  // 內部 .md 連結 → 切換頁面
  contentEl.querySelectorAll('a').forEach(function(a){
    var href=a.getAttribute('href')||'';
    var m=href.replace(/^.*\//,'').replace(/#.*$/,'');
    try{m=decodeURIComponent(m);}catch(e){}
    if(m.slice(-3)==='.md'){
      var tid=m.slice(0,-3);
      if(ids[tid]){
        a.setAttribute('href','#'+tid);
        a.addEventListener('click',function(e){e.preventDefault();go(tid);});
      }
    }
  });
  links.forEach(function(a){a.classList.toggle('active',a.dataset.id===id)});
  window.scrollTo(0,0);
  try{localStorage.setItem('exam_last',id)}catch(e){}
  if(push){location.hash=id}
  closeSide();
}
function go(id){render(id,true)}
links.forEach(function(a){a.addEventListener('click',function(e){e.preventDefault();go(a.dataset.id)})});

// 搜尋篩選
document.getElementById('search').addEventListener('input',function(e){
  var q=e.target.value.trim().toLowerCase();
  links.forEach(function(a){
    var hit=a.textContent.toLowerCase().indexOf(q)>=0;
    a.classList.toggle('hidden',q&&!hit);
  });
  document.querySelectorAll('.nav-group').forEach(function(g){
    var any=g.querySelectorAll('.nav-link:not(.hidden)').length>0;
    g.style.display=any?'':'none';
  });
});

// mobile
var sb=document.getElementById('sidebar'),ov=document.getElementById('overlay');
function closeSide(){sb.classList.remove('open');ov.classList.remove('show')}
document.getElementById('menu-btn').onclick=function(){sb.classList.toggle('open');ov.classList.toggle('show')};
ov.onclick=closeSide;

// 浮動回頂端按鈕
var totop=document.getElementById('totop');
function onScroll(){ (window.scrollY>300) ? totop.classList.add('show') : totop.classList.remove('show'); }
window.addEventListener('scroll',onScroll,{passive:true});
totop.addEventListener('click',function(){window.scrollTo({top:0,behavior:'smooth'})});

// 起始頁：hash → localStorage → 第一頁
var start=(location.hash||'').replace('#','');
try{start=decodeURIComponent(start);}catch(e){}
if(!ids[start]){try{start=localStorage.getItem('exam_last')}catch(e){}}
if(!ids[start])start='__FIRST__';
render(start,false);
window.addEventListener('hashchange',function(){var h=location.hash.replace('#','');try{h=decodeURIComponent(h);}catch(e){}if(ids[h])render(h,false)});
</script>
</body>
</html>"""

HTML = (HTML
        .replace("__MARKED__", marked_js())
        .replace("__NAV__", nav_html)
        .replace("__DOCS__", docs_json)
        .replace("__FIRST__", first_id))

out = os.path.join(ROOT, "index.html")
with open(out, "w", encoding="utf-8") as fh:
    fh.write(HTML)
print("OK  ->", out)
print("頁數:", sum(len(g["items"]) for g in groups), " 大小:", round(len(HTML)/1024), "KB")
