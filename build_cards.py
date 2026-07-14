#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三法法條字卡建置腳本：解析 三法/10_三法_法條速記表.md 的表格 → cards.html
SSOT＝速記表 md；改 md 後重跑本腳本（build_site.py 會自動呼叫）。
卡片方向固定：正面＝主題（如「庫藏股買回」）→ 背面＝條號＋規則＋關鍵數字。
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "三法", "10_三法_法條速記表.md")
OUT = os.path.join(ROOT, "cards.html")

def md_inline(s):
    s = html.escape(s.strip())
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s

def parse():
    text = open(SRC, encoding="utf-8").read()
    cards = []
    section = None
    SECTIONS = {
        "數字陷阱總表": "數字陷阱",
        "一、公司法": "公司法",
        "二、證券交易法": "證交法",
        "三、商業會計法": "商會法",
    }
    for line in text.splitlines():
        if line.startswith("#"):
            section = None
            for key, name in SECTIONS.items():
                if key in line:
                    section = name
            continue
        if section is None or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= {"-", " ", ":"}:
            continue
        if cells[0] in ("數字", "條"):  # 表頭
            continue
        if section == "數字陷阱":
            num, what, law = cells[0], cells[1], cells[2]
            # 正面遮數字（避免題面漏答案）：所有阿拉伯數字改成「？」
            masked = re.sub(r"[0-9０-９][0-9０-９,，\.]*", "？", re.sub(r"\*\*", "", what))
            cards.append({
                "deck": section,
                "front": md_inline(masked),
                "law": md_inline(law),
                "back": md_inline(num) + "<br><span style='color:#94a3b8;font-size:14px'>" + md_inline(re.sub(r"\*\*", "", what)) + "</span>",
            })
        else:
            cond, rule, detail = cells[0], cells[1], cells[2]
            cards.append({
                "deck": section,
                "front": md_inline(re.sub(r"\*\*", "", rule)),
                "law": md_inline(cond),
                "back": md_inline(detail),
            })
    for i, c in enumerate(cards):
        c["id"] = f'{c["deck"]}|{re.sub(r"<[^>]+>", "", c["front"])[:30]}'
    return cards

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>三法法條字卡</title>
<style>
:root{--bg:#0f172a;--card:#1e293b;--card2:#243449;--accent:#2563eb;--ok:#16a34a;--no:#dc2626;
--text:#e2e8f0;--muted:#94a3b8;--gold:#fbbf24}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0;background:var(--bg);color:var(--text);
font-family:"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif}
#app{max-width:560px;margin:0 auto;padding:14px 16px 40px}
header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
header h1{font-size:17px;margin:0;font-weight:800}
header a{color:var(--muted);text-decoration:none;font-size:13px}
#decks{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.chip{border:1px solid #334155;background:none;color:var(--muted);border-radius:999px;
padding:5px 12px;font-size:13px;cursor:pointer}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:700}
#bar{height:6px;background:#1e293b;border-radius:3px;overflow:hidden;margin-bottom:6px}
#bar>div{height:100%;background:var(--accent);width:0%;transition:.3s}
#stats{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:12px}
#card{min-height:200px;background:var(--card);border-radius:18px;padding:44px 20px 34px;
display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;
cursor:pointer;box-shadow:0 8px 30px rgba(0,0,0,.35);position:relative;user-select:none}
#card .deck-badge{position:absolute;top:12px;left:14px;font-size:11px;color:var(--muted);
border:1px solid #334155;border-radius:999px;padding:2px 9px}
#card .hint{position:absolute;bottom:10px;font-size:11px;color:#475569}
#front-text{font-size:22px;font-weight:800;line-height:1.5}
#front-text.small{font-size:15px;color:var(--muted);font-weight:700;margin-bottom:14px;
padding-bottom:12px;border-bottom:1px dashed #334155;width:100%}
#back{display:none;width:100%}
#back .law{font-size:20px;font-weight:800;color:var(--gold);margin-bottom:10px;text-align:center}
#back .detail{font-size:15.5px;line-height:1.8;text-align:left;color:var(--text)}
#back .detail b{color:#f87171;font-weight:800}
#actions{display:flex;gap:10px;margin-top:14px}
#actions button{flex:1;padding:15px 0;border:none;border-radius:14px;font-size:16px;font-weight:800;
cursor:pointer;color:#fff}
#btn-no{background:var(--no)} #btn-ok{background:var(--ok)}
#actions.hidden,#back.hidden{display:none}
#done{display:none;text-align:center;padding:40px 0}
#done h2{font-size:22px}
#done button,#reset{margin-top:10px;background:var(--accent);color:#fff;border:none;
border-radius:12px;padding:12px 22px;font-size:15px;font-weight:700;cursor:pointer}
#reset{background:none;border:1px solid #334155;color:var(--muted);font-size:12px;padding:6px 12px}
footer{margin-top:14px;text-align:center}
@media(min-width:600px){#front-text{font-size:24px}#card{min-height:230px}}
</style>
</head>
<body>
<div id="app">
<header><h1>🃏 三法法條字卡</h1><a href="index.html">← 回教材</a></header>
<div id="decks"></div>
<div id="bar"><div id="barfill"></div></div>
<div id="stats"><span id="s-left"></span><span id="s-master"></span></div>

<div id="card">
  <span class="deck-badge" id="badge"></span>
  <div id="front-text"></div>
  <div id="back"><div class="law" id="back-law"></div><div class="detail" id="back-detail"></div></div>
  <span class="hint" id="hint">點卡片翻面（空白鍵）</span>
</div>
<div id="actions" class="hidden">
  <button id="btn-no">✗ 還不熟（1）</button>
  <button id="btn-ok">✓ 記住了（2）</button>
</div>
<div id="done">
  <h2>🎉 本輪完成</h2><p id="done-sub"></p>
  <button onclick="startSession()">再來一輪（不熟的優先）</button>
</div>
<footer><button id="reset">清除記憶進度</button></footer>
</div>

<script>
const CARDS = __CARDS__;
const LS_KEY = "law_cards_box_v1";
let box = JSON.parse(localStorage.getItem(LS_KEY) || "{}");
let deckFilter = localStorage.getItem("law_cards_deck") || "全部";
let queue = [], idx = 0, flipped = false, sessionTotal = 0;

const $ = id => document.getElementById(id);
const decks = ["全部", ...new Set(CARDS.map(c => c.deck))];

function renderDecks(){
  $("decks").innerHTML = decks.map(d =>
    `<button class="chip ${d===deckFilter?'on':''}" data-d="${d}">${d}</button>`).join("");
  document.querySelectorAll(".chip").forEach(b => b.onclick = () => {
    deckFilter = b.dataset.d; localStorage.setItem("law_cards_deck", deckFilter);
    renderDecks(); startSession();
  });
}
function pool(){ return CARDS.filter(c => deckFilter==="全部" || c.deck===deckFilter); }
function shuffle(a){ for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

function startSession(){
  const p = pool();
  // Leitner：box 低（不熟）優先；同 box 內洗牌
  queue = shuffle([...p]).sort((a,b) => (box[a.id]||0) - (box[b.id]||0));
  idx = 0; sessionTotal = queue.length;
  $("done").style.display = "none"; $("card").style.display = "flex";
  show();
}
function show(){
  if(idx >= queue.length){ finish(); return; }
  const c = queue[idx]; flipped = false;
  $("badge").textContent = c.deck;
  $("front-text").innerHTML = c.front;
  $("front-text").style.display = "block";
  $("front-text").classList.remove("small");
  $("back").style.display = "none";
  $("back-law").innerHTML = c.law;
  $("back-detail").innerHTML = c.back;
  $("actions").classList.add("hidden");
  $("hint").style.display = "block";
  updateStats();
}
function flip(){
  if(idx >= queue.length) return;
  flipped = !flipped;
  $("front-text").classList.toggle("small", flipped);   // 正面保留、縮小置頂
  $("back").style.display = flipped ? "block" : "none";
  $("actions").classList.toggle("hidden", !flipped);
  $("hint").style.display = flipped ? "none" : "block";
}
function grade(ok){
  if(!flipped) return;
  const c = queue[idx];
  if(ok){ box[c.id] = Math.min((box[c.id]||0)+1, 3); }
  else { box[c.id] = 0; const later = Math.min(idx+4, queue.length); queue.splice(later, 0, c); }
  localStorage.setItem(LS_KEY, JSON.stringify(box));
  idx++; show();
}
function updateStats(){
  const p = pool();
  const mastered = p.filter(c => (box[c.id]||0) >= 2).length;
  $("s-left").textContent = `本輪 ${Math.min(idx+1, queue.length)} / ${queue.length}`;
  $("s-master").textContent = `已掌握 ${mastered} / ${p.length}`;
  $("barfill").style.width = (queue.length ? (idx/queue.length*100) : 0) + "%";
}
function finish(){
  $("card").style.display = "none"; $("actions").classList.add("hidden");
  const p = pool();
  const mastered = p.filter(c => (box[c.id]||0) >= 2).length;
  $("done-sub").textContent = `這個牌組已掌握 ${mastered}/${p.length} 張`;
  $("done").style.display = "block";
  $("barfill").style.width = "100%";
}
$("card").onclick = flip;
$("btn-ok").onclick = () => grade(true);
$("btn-no").onclick = () => grade(false);
$("reset").onclick = () => { if(confirm("清除所有記憶進度？")){ box={}; localStorage.removeItem(LS_KEY); startSession(); } };
document.addEventListener("keydown", e => {
  if(e.code === "Space"){ e.preventDefault(); flip(); }
  if(e.key === "1") grade(false);
  if(e.key === "2") grade(true);
});
renderDecks(); startSession();
</script>
</body>
</html>"""

cards = parse()
html_out = TEMPLATE.replace("__CARDS__", json.dumps(cards, ensure_ascii=False))
open(OUT, "w", encoding="utf-8").write(html_out)
by = {}
for c in cards:
    by[c["deck"]] = by.get(c["deck"], 0) + 1
print("OK ->", OUT)
print("卡片數:", len(cards), by)
