# -*- coding: utf-8 -*-
"""Генерирует HTML-отчёт из final.json. Далее html2pdf.js -> PDF."""
import json, sys, html, math

data = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = sys.argv[2]
TODAY_RU = data["today_ru"]
SK = data["skus"]
RATES = data["rates"]
ctx = data.get("context") or {}

CAT_TITLES = {"RAM": "Оперативная память DDR4", "SSD": "SSD SATA 2.5\"", "HDD": "Жёсткие диски HDD 3.5\""}
CAT_ORDER = ["RAM", "SSD", "HDD"]
ALT = {"RAM": "SO-DIMM (ноутбук)", "SSD": "M.2 SATA", "HDD": "2.5\"/внешние"}

C_NEW, C_USED = "#2a78d6", "#eb6834"
INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
esc = lambda s: html.escape(str(s if s is not None else ""))

def rub(x):
    if x is None:
        return "—"
    return "{:,}".format(int(round(x))).replace(",", " ") + " ₽"

CONF_RU = {"high": "высокая", "med": "средняя", "low": "низкая"}
def conf_badge(c):
    cls = {"high": "ok", "med": "warn", "low": "none"}.get(c, "none")
    return '<span class="badge ' + cls + '">' + CONF_RU.get(c, c) + '</span>'

# ---- SVG helpers ----
def nice_ticks(vmax, n=5):
    if vmax <= 0:
        return [0, 1]
    raw = vmax / n
    mag = 10 ** math.floor(math.log10(raw))
    step = mag
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if vmax / step <= n:
            break
    return [i * step for i in range(int(math.ceil(vmax / step)) + 1)]

def bar_path(x0, y, x1, h, r=4):
    if x1 - x0 < r:
        r = max(0.5, x1 - x0)
    return "M{:.1f},{:.1f} H{:.1f} Q{:.1f},{:.1f} {:.1f},{:.1f} V{:.1f} Q{:.1f},{:.1f} {:.1f},{:.1f} H{:.1f} Z".format(
        x0, y, x1 - r, x1, y, x1, y + r, y + h - r, x1, y + h, x1 - r, y + h, x0)

def ftick(v):
    if v >= 1000:
        return "{:g} тыс.".format(v / 1000).replace(".", ",")
    return "{:g}".format(v)

def chart_grouped(rows, title, subtitle):
    W, LEFT, RIGHT, TOP = 720, 118, 70, 56
    BAR, GAP, ROW = 15, 2, 46
    H = TOP + ROW * len(rows) + 28
    vals = [v for r in rows for v in (r[1], r[2]) if v]
    tmax = nice_ticks(max(vals) * 1.08 if vals else 1)[-1]
    px = lambda v: LEFT + (W - LEFT - RIGHT) * v / tmax
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}" font-family="Liberation Sans, DejaVu Sans, sans-serif">'.format(W, H, W, H)]
    s.append('<text x="0" y="16" font-size="13" font-weight="700" fill="{}">{}</text>'.format(INK, esc(title)))
    s.append('<text x="0" y="32" font-size="10" fill="{}">{}</text>'.format(INK2, esc(subtitle)))
    lx = W - RIGHT - 250
    s.append('<rect x="{}" y="8" width="10" height="10" rx="2" fill="{}"/><text x="{}" y="17" font-size="10" fill="{}">Новое, минимум</text>'.format(lx, C_NEW, lx + 14, INK2))
    s.append('<rect x="{}" y="8" width="10" height="10" rx="2" fill="{}"/><text x="{}" y="17" font-size="10" fill="{}">Б/у, оценка</text>'.format(lx + 120, C_USED, lx + 134, INK2))
    for t in nice_ticks(tmax):
        x = px(t)
        s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" stroke-width="1"/>'.format(x, TOP - 6, x, H - 22, GRID))
        s.append('<text x="{:.1f}" y="{}" font-size="9" fill="{}" text-anchor="middle">{}</text>'.format(x, H - 8, MUTED, esc(ftick(t))))
    s.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1"/>'.format(LEFT, TOP - 6, LEFT, H - 22, BASE))
    for i, (label, nv, uv) in enumerate(rows):
        y = TOP + i * ROW
        s.append('<text x="{}" y="{:.0f}" font-size="10.5" fill="{}" text-anchor="end">{}</text>'.format(LEFT - 8, y + BAR + GAP / 2 + 4, INK, esc(label)))
        for j, (v, col) in enumerate(((nv, C_NEW), (uv, C_USED))):
            yy = y + j * (BAR + GAP)
            if v:
                s.append('<path d="{}" fill="{}"/>'.format(bar_path(LEFT, yy, px(v), BAR), col))
                s.append('<text x="{:.1f}" y="{:.0f}" font-size="9.5" font-weight="700" fill="{}">{}</text>'.format(px(v) + 5, yy + BAR - 3, INK, esc(rub(v))))
            else:
                s.append('<text x="{}" y="{:.0f}" font-size="9" fill="{}">нет данных</text>'.format(LEFT + 6, yy + BAR - 3, MUTED))
    s.append("</svg>")
    return "".join(s)

def chart_single(rows, title, subtitle, color, unit):
    W, LEFT, RIGHT, TOP = 720, 118, 84, 40
    BAR, ROW = 15, 25
    H = TOP + ROW * len(rows) + 28
    vals = [r[1] for r in rows if r[1]]
    tmax = nice_ticks(max(vals) * 1.08 if vals else 1)[-1]
    px = lambda v: LEFT + (W - LEFT - RIGHT) * v / tmax
    ext = {min(vals), max(vals)} if vals else set()
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}" font-family="Liberation Sans, DejaVu Sans, sans-serif">'.format(W, H, W, H)]
    s.append('<text x="0" y="16" font-size="13" font-weight="700" fill="{}">{}</text>'.format(INK, esc(title)))
    s.append('<text x="0" y="31" font-size="10" fill="{}">{}</text>'.format(INK2, esc(subtitle)))
    for t in nice_ticks(tmax):
        x = px(t)
        s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" stroke-width="1"/>'.format(x, TOP - 4, x, H - 22, GRID))
        s.append('<text x="{:.1f}" y="{}" font-size="9" fill="{}" text-anchor="middle">{:g}</text>'.format(x, H - 8, MUTED, t))
    s.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1"/>'.format(LEFT, TOP - 4, LEFT, H - 22, BASE))
    for i, (label, v) in enumerate(rows):
        y = TOP + i * ROW
        s.append('<text x="{}" y="{:.0f}" font-size="10.5" fill="{}" text-anchor="end">{}</text>'.format(LEFT - 8, y + BAR - 3, INK, esc(label)))
        if v:
            s.append('<path d="{}" fill="{}"/>'.format(bar_path(LEFT, y, px(v), BAR), color))
            if v in ext:
                s.append('<text x="{:.1f}" y="{:.0f}" font-size="9.5" font-weight="700" fill="{}">{}</text>'.format(px(v) + 5, y + BAR - 3, INK, esc(unit(v))))
        else:
            s.append('<text x="{}" y="{:.0f}" font-size="9" fill="{}">нет данных</text>'.format(LEFT + 6, y + BAR - 3, MUTED))
    s.append("</svg>")
    return "".join(s)

# ---- derived ----
def mn(sk):
    return sk["new"]["min"]
def mu(sk):
    return sk["used"]["min"]
def sav(sk):
    a, b = mn(sk), mu(sk)
    return (1 - b / a) * 100 if a and b else None

CSS = """
* { box-sizing: border-box; }
body { font-family: "Liberation Sans","DejaVu Sans",Arial,sans-serif; font-size:10pt; color:#0b0b0b; margin:0; line-height:1.42; }
h1 { font-size:23pt; margin:0 0 6px; line-height:1.15; }
h2 { font-size:15pt; margin:0 0 10px; padding-bottom:4px; border-bottom:1px solid #c3c2b7; }
h3 { font-size:12pt; margin:16px 0 6px; }
h4 { font-size:10pt; margin:11px 0 4px; color:#52514e; }
p { margin:0 0 8px; }
.muted{color:#898781;} .sec{color:#52514e;} .small{font-size:8.5pt;}
.cover{padding-top:56px;}
.cover .kicker{text-transform:uppercase;letter-spacing:.08em;font-size:9pt;color:#52514e;margin-bottom:14px;}
.cover .sub{font-size:12.5pt;color:#52514e;margin:10px 0 26px;}
.cover .meta{border-top:1px solid #e1e0d9;padding-top:12px;font-size:9.5pt;color:#52514e;}
.cover .meta div{margin-bottom:5px;}
.page{break-before:page;}
.avoid{break-inside:avoid;}
table{width:100%;border-collapse:collapse;font-size:8.8pt;margin:6px 0 12px;}
th,td{border-bottom:1px solid #e1e0d9;padding:4px 6px;text-align:left;vertical-align:top;}
th{background:#f4f4f1;color:#52514e;font-weight:700;font-size:8.3pt;border-bottom:1px solid #c3c2b7;}
tr{break-inside:avoid;}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
td.min{font-weight:700;}
tr.hl td{background:#eaf2fc;}
.badge{display:inline-block;font-size:7.6pt;padding:1px 6px;border-radius:9px;white-space:nowrap;}
.badge.ok{background:#e3f3e3;color:#0a5a0a;} .badge.warn{background:#fff1dc;color:#7a4b00;} .badge.none{background:#eee;color:#52514e;}
a{color:#1c5cab;text-decoration:none;}
.dom{color:#898781;font-size:7.6pt;}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:10px 0 14px;}
.tile{border:1px solid #e1e0d9;border-radius:8px;padding:9px 11px;break-inside:avoid;}
.tile .lbl{font-size:8.3pt;color:#52514e;}
.tile .val{font-size:16pt;font-weight:700;margin:1px 0;}
.tile .val.u{font-size:12pt;font-weight:600;color:#7a3d1a;}
.tile .src{font-size:7.8pt;color:#898781;}
.callout{border-left:3px solid #2a78d6;background:#f6f9fd;padding:8px 12px;margin:10px 0 14px;}
.callout.warn{border-left-color:#eda100;background:#fffaf0;}
.chart{margin:6px 0 14px;break-inside:avoid;}
ul,ol{margin:4px 0 10px 18px;padding:0;} li{margin-bottom:4px;}
.sources li{font-size:8pt;word-break:break-all;}
.cols2{columns:2;column-gap:22px;}
.note{font-size:8.6pt;color:#52514e;background:#f8f8f6;padding:6px 10px;border-radius:6px;margin:4px 0 10px;}
"""

H = []
H.append("<!doctype html><html lang='ru'><head><meta charset='utf-8'><title>Аналитика цен на комплектующие — StyleNova</title><style>" + CSS + "</style></head><body>")

# ---- Cover ----
markets = sorted(set(of["market"] for sk in SK for of in sk["new"]["offers"] if of["market"] not in ("Российские площадки", "другое")))
H.append('<section class="cover">')
H.append('<div class="kicker">StyleNova · аналитика рынка комплектующих</div>')
H.append('<h1>Цены на DDR4, SSD SATA и HDD: новое и б/у</h1>')
H.append('<div class="sub">Срез по рынкам России на ' + TODAY_RU + '. Минимальные цены новой розницы и вторичного рынка, типичные диапазоны, удельная стоимость и ориентиры для закупки и продажи.</div>')
H.append('<div class="meta">')
H.append('<div><b>Позиции (14):</b> DDR4 4 / 8 / 16 / 32 ГБ · SSD SATA 128 / 240 / 512 ГБ, 1 / 2 ТБ · HDD 3.5" 1 / 2 / 3 / 4 / 6 ТБ — каждая в состоянии «новое» и «б/у».</div>')
H.append('<div><b>Площадки:</b> ' + esc(", ".join(markets)) + '.</div>')
H.append('<div><b>Курс для пересчёта:</b> USD ' + str(RATES.get("USD")) + ' ₽, EUR ' + str(RATES.get("EUR")) + ' ₽ (Банк России, ' + esc(ctx.get("rate_date", TODAY_RU)) + ').</div>')
H.append('<div><b>Метод:</b> сбор цен из открытых поисковых сниппетов и карточек площадок, сведение по позициям, оценка минимумов и диапазонов. Прямой доступ к сайтам площадок из среды закрыт сетевой политикой, поэтому цена бралась только там, где явно указана в выдаче.</div>')
H.append('</div>')
H.append('<div class="callout warn" style="margin-top:24px"><b>Главное про рынок сейчас.</b> 2026 год — «memory supercycle»: из-за бума ИИ дефицитны и дорожают DRAM, NAND и HDD одновременно. За год память подорожала в разы, HDD 1–8 ТБ — на десятки процентов. Поэтому цены крайне волатильны: снипеты и карточки меняются еженедельно, часть предложений идёт «с картой» площадки или это киты из нескольких модулей. Перед закупкой партии сверяйте с живой карточкой по ссылке.</div>')
H.append('</section>')

# ---- Section 1: итоги ----
H.append('<section class="page"><h2>1. Итог: самые низкие цены по каждой позиции</h2>')
H.append('<p class="sec">Минимальная цена за 1 шт. в целевом форм-факторе (DIMM для памяти, 2.5" SATA для SSD, 3.5" для HDD). Уверенность отражает, насколько цена подтверждена конкретной карточкой (высокая/средняя) или является оценкой по рынку (низкая). Экономия — насколько минимум б/у ниже минимума новой розницы.</p>')
H.append('<table><thead><tr><th>Позиция</th><th class="num">Мин. новое</th><th>Где</th><th>Уверен.</th><th class="num">Мин. б/у</th><th>Где</th><th>Уверен.</th><th class="num">Экономия</th></tr></thead><tbody>')
last = None
for sk in SK:
    if sk["cat"] != last:
        H.append('<tr><td colspan="8" style="background:#f4f4f1;font-weight:700;color:#52514e">' + esc(CAT_TITLES[sk["cat"]]) + '</td></tr>')
        last = sk["cat"]
    sv = sav(sk)
    H.append('<tr><td><b>' + esc(sk["short"]) + '</b></td>'
             '<td class="num min">' + rub(mn(sk)) + '</td><td>' + esc(sk["new"]["where"]) + '</td><td>' + conf_badge(sk["new"]["conf"]) + '</td>'
             '<td class="num min">' + rub(mu(sk)) + '</td><td>' + esc(sk["used"]["where"]) + '</td><td>' + conf_badge(sk["used"]["conf"]) + '</td>'
             '<td class="num">' + ("−{:.0f} %".format(sv) if sv is not None else "—") + '</td></tr>')
H.append('</tbody></table>')

# absolute minima
bn = min(SK, key=lambda s: mn(s) if mn(s) else 9e9)
bu = min(SK, key=lambda s: mu(s) if mu(s) else 9e9)
ppg = min((s for s in SK if mn(s)), key=lambda s: mn(s) / s["cap_gb"])
H.append('<div class="callout"><b>Самая низкая цена по всем параметрам.</b> Новое: <b>' + esc(bn["short"]) + ' — ' + rub(mn(bn)) + '</b> (' + esc(bn["new"]["where"]) + '). '
         'Б/у: <b>' + esc(bu["short"]) + ' — ' + rub(mu(bu)) + '</b> (оценка вторичного рынка). '
         'Самая выгодная ёмкость среди нового — <b>' + esc(ppg["short"]) + ': ' + "{:.1f}".format(mn(ppg) / ppg["cap_gb"]) + ' ₽ за ГБ</b>.</div>')

# clear retail result tiles
H.append('<h3>Чёткий результат по рознице: где дешевле всего купить</h3>')
H.append('<div class="tiles">')
for sk in SK:
    on = next((x for x in sk["new"]["offers"] if x["price_rub"] == mn(sk)), None)
    H.append('<div class="tile">')
    H.append('<div class="lbl">' + esc(sk["short"]) + ' — новое, минимум</div>')
    H.append('<div class="val">' + rub(mn(sk)) + '</div>')
    H.append('<div class="src">' + esc(sk["new"]["where"]) + (' · ' + esc((on["title"] or "")[:42]) if on else "") + '</div>')
    H.append('<div class="lbl" style="margin-top:5px">б/у, оценка минимума</div><div class="val u">' + rub(mu(sk)) + '</div>')
    H.append('</div>')
H.append('</div></section>')

# ---- Section 2: ranges ----
H.append('<section class="page"><h2>2. Диапазоны, удельная цена и ориентиры</h2>')
H.append('<p class="sec">Типичный диапазон — рабочая вилка розницы/вторички по позиции на сентябрь 2026 (без единичных выбросов). ₽/ГБ считается по минимуму. Для магазина StyleNova ориентир закупки — минимум б/у, ориентир цены продажи — верх диапазона б/у или низ новой розницы.</p>')
H.append('<table><thead><tr><th>Позиция</th><th>Диапазон, новое</th><th>Диапазон, б/у</th><th class="num">Новое, ₽/ГБ</th><th class="num">Б/у, ₽/ГБ</th></tr></thead><tbody>')
last = None
for sk in SK:
    if sk["cat"] != last:
        H.append('<tr><td colspan="5" style="background:#f4f4f1;font-weight:700;color:#52514e">' + esc(CAT_TITLES[sk["cat"]]) + '</td></tr>')
        last = sk["cat"]
    tn, tu = sk["new"]["typ"], sk["used"]["typ"]
    H.append('<tr><td><b>' + esc(sk["short"]) + '</b></td>'
             '<td>' + rub(tn[0]) + ' – ' + rub(tn[1]) + '</td><td>' + rub(tu[0]) + ' – ' + rub(tu[1]) + '</td>'
             '<td class="num">' + "{:.1f}".format(mn(sk) / sk["cap_gb"]) + '</td>'
             '<td class="num">' + "{:.1f}".format(mu(sk) / sk["cap_gb"]) + '</td></tr>')
H.append('</tbody></table>')

# charts
for cat in CAT_ORDER:
    rows = [(sk["short"], mn(sk), mu(sk)) for sk in SK if sk["cat"] == cat]
    H.append('<div class="chart">' + chart_grouped(rows, CAT_TITLES[cat] + ": минимальная цена за 1 шт., ₽", "Синие — новая розница; оранжевые — оценка вторичного рынка") + '</div>')
H.append('</section>')

H.append('<section class="page"><h2>3. Удельная цена и выгода вторички</h2>')
rows = [(sk["short"], mn(sk) / sk["cap_gb"]) for sk in SK]
H.append('<div class="chart">' + chart_single(rows, "Удельная цена нового, ₽ за 1 ГБ (по минимуму)", "Чем ниже столбик, тем дешевле обходится ёмкость", C_NEW, lambda v: "{:.1f} ₽/ГБ".format(v)) + '</div>')
rows = [(sk["short"], sav(sk)) for sk in SK]
H.append('<div class="chart">' + chart_single(rows, "Дисконт б/у к новому, %", "На сколько минимум вторичного рынка ниже минимума новой розницы", C_USED, lambda v: "{:.0f} %".format(v)) + '</div>')
H.append('<div class="note"><b>Как читать удельную цену.</b> Память дороже накопителей на порядок за гигабайт: DDR4 обходится в сотни рублей за ГБ, а HDD и ёмкие SSD — в единицы рублей за ГБ. Для наращивания объёма хранения выгоднее всего ёмкие HDD; для скорости системного диска — SSD SATA среднего объёма.</div>')
H.append('</section>')

# ---- Section 4: detail ----
secno = 4
for cat in CAT_ORDER:
    H.append('<section class="page"><h2>' + str(secno) + '. ' + esc(CAT_TITLES[cat]) + ': детализация по позициям</h2>')
    secno += 1
    for sk in [s for s in SK if s["cat"] == cat]:
        H.append('<h3>' + esc(sk["label"]) + '</h3>')
        for cond, cname in (("new", "Новое (розница)"), ("used", "Б/у (вторичный рынок)")):
            blk = sk[cond]
            H.append('<h4>' + cname + ' — минимум ' + rub(blk["min"]) + ' · типичный диапазон ' + rub(blk["typ"][0]) + ' – ' + rub(blk["typ"][1]) + ' · уверенность ' + CONF_RU.get(blk["conf"], blk["conf"]) + '</h4>')
            offs = sorted(blk["offers"], key=lambda x: x["price_rub"])
            H.append('<table><thead><tr><th style="width:17%">Площадка</th><th>Товар / позиция</th><th class="num" style="width:12%">Цена</th><th style="width:26%">Примечание</th><th style="width:10%">Уверен.</th></tr></thead><tbody>')
            for of in offs:
                hl = ' class="hl"' if of["price_rub"] == blk["min"] else ""
                dom = ' <span class="dom">' + esc(of["url"]) + '</span>' if of.get("url") else ""
                H.append('<tr' + hl + '><td>' + esc(of["market"]) + '</td><td>' + esc(of["title"]) + dom + '</td>'
                         '<td class="num">' + rub(of["price_rub"]) + '</td><td class="small">' + esc(of.get("note", "")) + '</td><td>' + conf_badge(of["conf"]) + '</td></tr>')
            H.append('</tbody></table>')
            if blk.get("note"):
                H.append('<div class="note">' + esc(blk["note"]) + '</div>')
    H.append('</section>')

# ---- Section: context ----
H.append('<section class="page"><h2>' + str(secno) + '. Контекст рынка: почему цены такие</h2>')
secno += 1
if ctx:
    H.append('<p><b>Курс ЦБ РФ:</b> USD ' + str(ctx.get("usd_rub")) + ' ₽, EUR ' + str(ctx.get("eur_rub")) + ' ₽, CNY ' + str(ctx.get("cny_rub")) + ' ₽ (' + esc(ctx.get("rate_date", "")) + ').</p>')
    for t, k in (("Оперативная память (DRAM / DDR4)", "dram_trend"), ("SSD (NAND)", "nand_trend"), ("Жёсткие диски (HDD)", "hdd_trend"), ("Вторичный рынок (Авито)", "used_market_notes")):
        if ctx.get(k):
            H.append('<h3>' + t + '</h3><p>' + esc(ctx[k]) + '</p>')
H.append('</section>')

# ---- Section: warnings + methodology + sources ----
H.append('<section class="page"><h2>' + str(secno) + '. Оговорки, методика и источники</h2>')
secno += 1
H.append('<h3>На что обратить внимание в данных</h3><ol>')
for w in data.get("warnings", []):
    H.append('<li>' + esc(w) + '</li>')
H.append('</ol>')
H.append('<h3>Методика</h3><ul>')
H.append('<li><b>Срез:</b> ' + TODAY_RU + '. Источник цен — открытые поисковые сниппеты и заголовки карточек площадок (Яндекс Маркет, DNS, Ситилинк, Ozon, Wildberries, Регард, Никс, E-katalog, Price.ru, Hardprice и др.). Цена фиксировалась только там, где явно указана для подходящего товара.</li>')
H.append('<li><b>Форм-факторы:</b> в расчёт минимумов вошли DIMM (память), 2.5" SATA (SSD) и 3.5" (HDD). SO-DIMM, M.2 SATA, 2.5"/внешние диски — не в основном расчёте.</li>')
H.append('<li><b>Цены б/у</b> — оценка по документированному дисконту к рознице (SSD ~45–55 % от новой цены, HDD ~40–55 %, модули ОЗУ ~55–65 %) и агрегированной статистике Авито (средняя цена б/у SSD ~3 000 ₽, HDD ~4 000 ₽, модуль ОЗУ ~5 000 ₽; б/у в среднем в ~2,5 раза дешевле нового). Прямые листинги Авито из среды исследования недоступны.</li>')
H.append('<li><b>Пересчёт валют</b> (eBay, международный референс) — по курсу ЦБ; в минимумах по РФ такие цены не участвуют.</li>')
H.append('<li><b>Ограничения:</b> из-за дефицита DRAM/NAND/HDD 2026 цены волатильны и могут отличаться от указанных на дни; акции «с картой» занижают розницу; на Авито цена зависит от города, состояния и торга. Для закупки партии обязательна сверка по ссылке и проверка SMART/ресурса у б/у.</li>')
H.append('</ul>')
# sources
H.append('<h3>Источники по контексту рынка</h3><ol class="sources cols2">')
for s in (ctx.get("sources") or [])[:26]:
    H.append('<li>' + esc(s.get("title", "")) + ' — <a href="' + esc(s.get("url", "")) + '">' + esc((s.get("url") or "")[:80]) + '</a></li>')
H.append('</ol>')
H.append('<p class="small muted">Отчёт подготовлен для магазина StyleNova (б/у компьютерная техника). Цены ориентировочные, не являются публичной офертой.</p>')
H.append('</section></body></html>')

open(OUT, "w", encoding="utf-8").write("\n".join(H))
print("HTML written:", OUT)
