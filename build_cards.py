#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考試記憶字卡建置腳本 → cards.html
來源（SSOT，改 md 重跑即同步）：
  三法：三法/10_三法_法條速記表.md（含助記欄）
  稅務：稅務法規/10_稅務_現行數字速查表.md（自動克漏字：粗體數字遮成？）
  審計：審計學/00c_審計學_記憶口訣卡.md（清單默寫：口訣名→碼＋內容）
"""
import os, re, json, html

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "cards.html")

def md_inline(s):
    s = html.escape(s.strip())
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return s

def has_digit(s):
    return re.search(r"[0-9０-９]", s) is not None

# ---------- 三法 ----------
def parse_sanfa():
    text = open(os.path.join(ROOT, "三法", "10_三法_法條速記表.md"), encoding="utf-8").read()
    cards, section = [], None
    SECTIONS = {"數字陷阱總表": "數字陷阱", "一、公司法": "公司法",
                "二、證券交易法": "證交法", "三、商業會計法": "商會法"}
    for line in text.splitlines():
        if line.startswith("#"):
            section = None
            for key, name in SECTIONS.items():
                if key in line: section = name
            continue
        if section is None or not line.strip().startswith("|"): continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= {"-", " ", ":"}: continue
        if cells[0] in ("數字", "條") or cells[0].startswith("條件"): continue
        mnemo = cells[3] if len(cells) > 3 and cells[3] else ""
        if section == "數字陷阱":
            num, what, law = cells[0], cells[1], cells[2]
            # 去重：與法條卡重複的陷阱列不出卡（法條卡背面已含該數字）；只留無對應法條列的
            KEEP = ("提撥 10%", "1 千萬且 1%", "3 個月")
            if not any(num.strip("*").strip().startswith(k) for k in KEEP):
                continue
            plain = re.sub(r"\*\*", "", what)
            masked = re.sub(r"[0-9０-９][0-9０-９,，\.]*", "？", plain)
            back = md_inline(num)
            if masked != plain:
                back += "<br><span style='color:#94a3b8;font-size:14px'>" + md_inline(plain) + "</span>"
            cards.append(dict(deck="三法", sub=section, front=md_inline(masked),
                              law=md_inline(law), back=back,
                              mnemo=md_inline(mnemo) if mnemo else ""))
        else:
            cond, rule, detail = cells[0], cells[1], cells[2]
            cards.append(dict(deck="三法", sub=section,
                              front=md_inline(re.sub(r"\*\*", "", rule)),
                              law=md_inline(cond), back=md_inline(detail),
                              mnemo=md_inline(mnemo) if mnemo else ""))
    return cards

# ---------- 稅務（自動克漏字）----------
TAX_SKIP_HEAD = ("八、用法",)
def parse_tax():
    text = open(os.path.join(ROOT, "稅務法規", "10_稅務_現行數字速查表.md"), encoding="utf-8").read()
    cards, head, subhead = [], "", ""
    skip = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("## "):
            head = re.sub(r"^[〇一二三四五六七八九十、\s#★]*", "", s.lstrip("#").strip())
            head = re.sub(r"（.*?）", "", head).strip()
            skip = any(k in s for k in TAX_SKIP_HEAD)
            subhead = ""
            continue
        if s.startswith("### "):
            subhead = re.sub(r"[⚠✅★].*$", "", s.lstrip("#").strip()).strip()
            subhead = re.sub(r"（.*?）", "", subhead).strip()
            continue
        if skip or s.startswith(">"): continue
        ctx = subhead or head
        # 表格列
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            cells = [c for c in cells]
            if len(cells) < 2 or set(cells[0]) <= {"-", " ", ":"}: continue
            if cells[0] in ("項目", "稅目", "類型", "分類軸", "課稅遺產淨額", "課稅贈與淨額",
                            "綜合所得淨額", "課稅淨額", "所得類型", "級距", "持有期間",
                            "漲價倍數", "用地", "條件", "數字"):
                # 級距類表頭跳過，但「級距列」本身（首欄含數字）仍出卡
                pass
            answer = " ｜ ".join(cells[1:]).strip()
            if not (has_digit(answer) or "**" in answer): continue
            if len(re.sub(r"\*\*", "", cells[0])) > 40: continue
            front = f"<span class='ctx'>{md_inline(ctx)}</span>{md_inline(re.sub(r'\*\*','',cells[0]))} ＝ ？"
            cards.append(dict(deck="稅務", sub=ctx[:6], front=front, law=md_inline(ctx),
                              back=md_inline(re.sub(r"\*\*", "", answer)), mnemo=""))
            continue
        # 條列（克漏字：粗體含數字 → 遮）
        if s.startswith("- "):
            body = s[2:].strip()
            bolds = re.findall(r"\*\*(.+?)\*\*", body)
            num_bolds = [b for b in bolds if has_digit(b)]
            if not num_bolds: continue
            plain = re.sub(r"\*\*", "", body)
            if len(plain) > 110: continue
            masked = body
            for b in num_bolds:
                masked = masked.replace(f"**{b}**", "❓")
            masked = re.sub(r"\*\*", "", masked)
            front = f"<span class='ctx'>{md_inline(ctx)}</span>{md_inline(masked)}"
            back = "、".join(f"<b>{html.escape(b)}</b>" for b in num_bolds)
            back += "<br><span style='color:#94a3b8;font-size:14px'>" + md_inline(plain) + "</span>"
            cards.append(dict(deck="稅務", sub=ctx[:6], front=front, law=md_inline(ctx),
                              back=back, mnemo=""))
    return cards

# ---------- 審計（口訣卡）----------
def parse_audit():
    text = open(os.path.join(ROOT, "審計學", "00c_審計學_記憶口訣卡.md"), encoding="utf-8").read()
    cards = []
    section_title, code, body = None, "", []
    def flush():
        if not section_title or not body: return
        detail = []
        mnemo = ""
        for b in body:
            bs = b.strip()
            if not bs or bs == "---": continue
            m = re.match(r"\*\*(邏輯鉤|中文鉤|鉤|方向鉤.*?|口訣)\*\*[:：]?(.*)", bs)
            if m and not mnemo:
                mnemo = m.group(2).strip() or bs
                continue
            detail.append(md_inline(re.sub(r"^- ", "• ", bs)))
        cards.append(dict(deck="審計", sub="口訣", front=md_inline(section_title) + "？",
                          law=md_inline(code) if code else "口訣",
                          back="<br>".join(detail), mnemo=md_inline(mnemo) if mnemo else ""))
    for line in text.splitlines():
        if line.startswith("## "):
            flush()
            t = line.lstrip("#").strip()
            if "默寫順序" in t:
                section_title, body = None, []
                continue
            code = ""
            m = re.search(r"[｜|]\s*(碼|口訣)[:：]\s*\**([^*]+)\**", t)
            if m:
                code = m.group(2).strip()
                t = t[:m.start()].strip()
            t = re.sub(r"^[①-⑳⑴-⒇]+[\s-]*", "", t).strip()
            t = re.sub(r"^[④②③①⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯]-?\d*\s*", "", t).strip()
            section_title, body = t, []
        elif section_title is not None:
            body.append(line)
    flush()
    return cards

# ---------- 模板 ----------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>考試記憶字卡</title>
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
#front-text{font-size:20px;font-weight:800;line-height:1.55}
#front-text .ctx{display:block;font-size:12.5px;color:var(--muted);font-weight:600;margin-bottom:8px}
#front-text.small{font-size:14.5px;color:var(--muted);font-weight:700;margin-bottom:14px;
padding-bottom:12px;border-bottom:1px dashed #334155;width:100%}
#front-text.small .ctx{display:inline;margin-right:6px}
#back{display:none;width:100%}
#back .law{font-size:19px;font-weight:800;color:var(--gold);margin-bottom:6px;text-align:center}
#back .mnemo{font-size:13.5px;color:#e9c46a;background:rgba(251,191,36,.08);border:1px dashed rgba(251,191,36,.35);
border-radius:8px;padding:6px 10px;margin:0 auto 12px;max-width:92%;text-align:center}
#back .mnemo:empty{display:none}
#back .detail{font-size:15px;line-height:1.75;text-align:left;color:var(--text)}
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
@media(min-width:600px){#front-text{font-size:23px}#card{min-height:230px}}
</style>
</head>
<body>
<div id="app">
<header><h1>🃏 考試記憶字卡</h1><a href="index.html">← 回教材</a></header>
<div id="decks"></div>
<div id="bar"><div id="barfill"></div></div>
<div id="stats"><span id="s-left"></span><span id="s-master"></span></div>

<div id="card">
  <span class="deck-badge" id="badge"></span>
  <div id="front-text"></div>
  <div id="back"><div class="law" id="back-law"></div><div class="mnemo" id="back-mnemo"></div><div class="detail" id="back-detail"></div></div>
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
if(!decks.includes(deckFilter)) deckFilter = "全部";

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
  queue = shuffle([...p]).sort((a,b) => (box[a.id]||0) - (box[b.id]||0));
  idx = 0; sessionTotal = queue.length;
  $("done").style.display = "none"; $("card").style.display = "flex";
  show();
}
function show(){
  if(idx >= queue.length){ finish(); return; }
  const c = queue[idx]; flipped = false;
  $("badge").textContent = c.sub && c.sub !== c.deck ? c.deck + "·" + c.sub : c.deck;
  $("front-text").innerHTML = c.front;
  $("front-text").style.display = "block";
  $("front-text").classList.remove("small");
  $("back").style.display = "none";
  $("back-law").innerHTML = c.law;
  $("back-mnemo").innerHTML = c.mnemo ? "💡 " + c.mnemo : "";
  $("back-detail").innerHTML = c.back;
  $("actions").classList.add("hidden");
  $("hint").style.display = "block";
  updateStats();
}
function flip(){
  if(idx >= queue.length) return;
  flipped = !flipped;
  $("front-text").classList.toggle("small", flipped);
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

cards = parse_sanfa() + parse_tax() + parse_audit()
for c in cards:
    c["id"] = f'{c["deck"]}|{re.sub(r"<[^>]+>", "", c["front"])[:30]}'
html_out = TEMPLATE.replace("__CARDS__", json.dumps(cards, ensure_ascii=False))
open(OUT, "w", encoding="utf-8").write(html_out)
by = {}
for c in cards:
    by[c["deck"]] = by.get(c["deck"], 0) + 1
print("OK ->", OUT)
print("卡片數:", len(cards), by)
