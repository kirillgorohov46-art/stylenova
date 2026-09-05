# -*- coding: utf-8 -*-
"""PDF-отчёт: закупка комплектующих из Китая под перепродажу в РФ. -> china.html"""
import json, html, math, sys

ctx = json.load(open("ctx.json", encoding="utf-8"))
RATES = ctx.get("rates") or {"USD": 86.5857, "CNY": 12.8849, "EUR": 100.5693}
USD = RATES.get("USD", 86.5857)
CNY = RATES.get("CNY", 12.8849)
IMPORT_MULT = 1.30   # белый импорт: НДС 22% (невозвратный на УСН) + логистика ~8%, пошлина 0%
TODAY_RU = "5 сентября 2026"
OUT = sys.argv[1] if len(sys.argv) > 1 else "china.html"

INK, INK2, MUTED, GRID, BASE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
C_COST, C_SELL, C_POS, C_NEG = "#2a78d6", "#eb6834", "#008300", "#d03b3b"
esc = lambda s: html.escape(str(s if s is not None else ""))

def rub(x):
    return "—" if x is None else "{:,}".format(int(round(x))).replace(",", " ") + " ₽"

# ---- данные закупки ----
# fob_usd — ориентир FOB Китай ($/шт); sell_lo/hi — реалистичная продажа в РФ (из отчёта);
# src — тип товара; verdict: good/mid/bad; note
def row(key, cat, short, cap, fob_usd, sell_lo, sell_hi, src, verdict, note):
    fob_rub = fob_usd * USD
    landed = fob_rub * IMPORT_MULT
    sell_mid = (sell_lo + sell_hi) / 2
    markup = (sell_mid / landed - 1) * 100 if landed else 0
    profit = sell_mid - landed
    return dict(key=key, cat=cat, short=short, cap=cap, fob_usd=fob_usd, fob_rub=fob_rub,
                landed=landed, sell_lo=sell_lo, sell_hi=sell_hi, sell_mid=sell_mid,
                markup=markup, profit=profit, src=src, verdict=verdict, note=note)

ROWS = [
    row("RAM-4", "RAM", "DDR4 4 ГБ", 4, 8, 650, 1000, "новый модуль", "bad",
        "Рынок тонкий, модуль почти снят. Новый из Китая дороже, чем продажа. Не возить."),
    row("RAM-8", "RAM", "DDR4 8 ГБ", 8, 40, 4000, 4500, "новый модуль", "bad",
        "Новый: себестоимость ~4 500 ₽ ≥ розница РФ 4 243 ₽ — убыток. Смысл только в pulled-лотах (см. ниже)."),
    row("RAM-16", "RAM", "DDR4 16 ГБ", 16, 130, 10000, 11000, "новый модуль", "bad",
        "Новый: landed ~14 600 ₽ против розницы РФ 10 551 ₽ — глубокий убыток из-за дефицита DRAM."),
    row("RAM-32", "RAM", "DDR4 32 ГБ", 32, 195, 17000, 18000, "новый (часто кит 2×16)", "bad",
        "Новый: landed ~22 000 ₽ против розницы 17 463 ₽ — убыток. Только б/у-скупка внутри РФ."),
    row("SSD-128", "SSD", "SSD 128 ГБ", 128, 8, 1100, 1300, "no-name Shenzhen", "mid",
        "Наценка тонкая, объём уходит с рынка. Брать только если очень дёшево лотом."),
    row("SSD-240", "SSD", "SSD 240 ГБ", 240, 12, 2200, 2800, "no-name Shenzhen", "good",
        "Хорошая наценка. MOQ 50–100 шт. Обязательно тест реальной ёмкости (H2testw)."),
    row("SSD-512", "SSD", "SSD 512 ГБ", 512, 18, 3500, 5900, "no-name / бюджет", "good",
        "Самая выгодная позиция: 1688 от ¥76,9. Продажа 3 500–5 900 ₽. Риск QLC/DRAM-less — тестировать."),
    row("SSD-1000", "SSD", "SSD 1 ТБ", 1000, 27, 4500, 5900, "no-name / бюджет", "good",
        "Shenzhen от $29,88. Отличный оборот. Проверять здоровье и ёмкость каждого."),
    row("SSD-2000", "SSD", "SSD 2 ТБ", 2000, 50, 9000, 13000, "no-name / бюджет", "good",
        "Крупная абсолютная прибыль. Чаще QLC — честно указывайте тип памяти в карточке."),
    row("HDD-1000", "HDD", "HDD 1 ТБ", 1000, 18, 1800, 3000, "recertified (пул с ЦОД)", "mid",
        "На 1 ТБ наценка тонкая: дешевле купить б/у в РФ. Возить только в комплекте с ёмкими."),
    row("HDD-2000", "HDD", "HDD 2 ТБ", 2000, 35, 4500, 6700, "recertified", "good",
        "Рабочая позиция. Проверять SMART (наработка, переназначенные сектора)."),
    row("HDD-3000", "HDD", "HDD 3 ТБ", 3000, 52, 6500, 8000, "recertified", "mid",
        "Переходный объём, спрос средний. Наценка умеренная."),
    row("HDD-4000", "HDD", "HDD 4 ТБ", 4000, 66, 9000, 11000, "recertified", "good",
        "Хороший баланс наценки и оборота. Ровно профиль StyleNova: тест + своя гарантия."),
    row("HDD-6000", "HDD", "HDD 6 ТБ", 6000, 105, 13000, 15000, "recertified", "good",
        "Крупная прибыль с 1 шт. Ёмкие диски дефицитны и на вторичке РФ."),
]
CAT_TITLES = {"RAM": "Оперативная память DDR4", "SSD": "SSD SATA 2.5\"", "HDD": "Жёсткие диски HDD 3.5\""}
CAT_ORDER = ["RAM", "SSD", "HDD"]
V_RU = {"good": ("выгодно", "ok"), "mid": ("на грани", "warn"), "bad": ("убыток", "bad")}

# ---- SVG ----
def nice_ticks(vmax, n=5):
    if vmax <= 0:
        return [0, 1]
    mag = 10 ** math.floor(math.log10(vmax / n))
    step = mag
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if vmax / step <= n:
            break
    return [i * step for i in range(int(math.ceil(vmax / step)) + 1)]

def bar_path(x0, y, x1, h, r=4):
    if abs(x1 - x0) < r:
        r = max(0.5, abs(x1 - x0))
    if x1 >= x0:
        return "M{:.1f},{:.1f} H{:.1f} Q{:.1f},{:.1f} {:.1f},{:.1f} V{:.1f} Q{:.1f},{:.1f} {:.1f},{:.1f} H{:.1f} Z".format(
            x0, y, x1 - r, x1, y, x1, y + r, y + h - r, x1, y + h, x1 - r, y + h, x0)
    return "M{:.1f},{:.1f} H{:.1f} Q{:.1f},{:.1f} {:.1f},{:.1f} V{:.1f} Q{:.1f},{:.1f} {:.1f},{:.1f} H{:.1f} Z".format(
        x0, y, x1 + r, x1, y, x1, y + r, y + h - r, x1, y + h, x1 + r, y + h, x0)

def ftick(v):
    if abs(v) >= 1000:
        return "{:g} тыс.".format(v / 1000).replace(".", ",")
    return "{:g}".format(v)

def chart_grouped(rows, title, subtitle):
    """rows: (label, cost, sell)"""
    W, LEFT, RIGHT, TOP = 720, 118, 66, 56
    BAR, GAP, ROW = 14, 2, 44
    H = TOP + ROW * len(rows) + 28
    vals = [v for r in rows for v in (r[1], r[2]) if v]
    tmax = nice_ticks(max(vals) * 1.08 if vals else 1)[-1]
    px = lambda v: LEFT + (W - LEFT - RIGHT) * v / tmax
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}" font-family="Liberation Sans, DejaVu Sans, sans-serif">'.format(W, H, W, H)]
    s.append('<text x="0" y="16" font-size="13" font-weight="700" fill="{}">{}</text>'.format(INK, esc(title)))
    s.append('<text x="0" y="32" font-size="10" fill="{}">{}</text>'.format(INK2, esc(subtitle)))
    lx = W - RIGHT - 300
    s.append('<rect x="{}" y="8" width="10" height="10" rx="2" fill="{}"/><text x="{}" y="17" font-size="10" fill="{}">Себестоимость (Китай+ввоз)</text>'.format(lx, C_COST, lx + 14, INK2))
    s.append('<rect x="{}" y="8" width="10" height="10" rx="2" fill="{}"/><text x="{}" y="17" font-size="10" fill="{}">Продажа в РФ</text>'.format(lx + 180, C_SELL, lx + 194, INK2))
    for t in nice_ticks(tmax):
        x = px(t)
        s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" stroke-width="1"/>'.format(x, TOP - 6, x, H - 22, GRID))
        s.append('<text x="{:.1f}" y="{}" font-size="9" fill="{}" text-anchor="middle">{}</text>'.format(x, H - 8, MUTED, esc(ftick(t))))
    s.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="1"/>'.format(LEFT, TOP - 6, LEFT, H - 22, BASE))
    for i, (label, cost, sell) in enumerate(rows):
        y = TOP + i * ROW
        s.append('<text x="{}" y="{:.0f}" font-size="10.5" fill="{}" text-anchor="end">{}</text>'.format(LEFT - 8, y + BAR + GAP / 2 + 4, INK, esc(label)))
        for j, (v, col) in enumerate(((cost, C_COST), (sell, C_SELL))):
            yy = y + j * (BAR + GAP)
            if v:
                s.append('<path d="{}" fill="{}"/>'.format(bar_path(LEFT, yy, px(v), BAR), col))
                s.append('<text x="{:.1f}" y="{:.0f}" font-size="9" font-weight="700" fill="{}">{}</text>'.format(px(v) + 4, yy + BAR - 3, INK, esc(rub(v))))
    s.append("</svg>")
    return "".join(s)

def chart_diverging(rows, title, subtitle):
    """rows: (label, value%) — value может быть отрицательным (убыток)."""
    W, LEFT, RIGHT, TOP = 720, 118, 60, 54
    BAR, ROW = 15, 25
    H = TOP + ROW * len(rows) + 26
    vals = [r[1] for r in rows]
    vmax = max(vals) if vals else 1
    vmin = min(vals + [0])
    span = max(abs(vmin), vmax) * 1.12 or 1
    zero = LEFT + (W - LEFT - RIGHT) * (0 - (-span)) / (2 * span)
    px = lambda v: LEFT + (W - LEFT - RIGHT) * (v - (-span)) / (2 * span)
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {} {}" width="{}" height="{}" font-family="Liberation Sans, DejaVu Sans, sans-serif">'.format(W, H, W, H)]
    s.append('<text x="0" y="16" font-size="13" font-weight="700" fill="{}">{}</text>'.format(INK, esc(title)))
    s.append('<text x="0" y="31" font-size="10" fill="{}">{}</text>'.format(INK2, esc(subtitle)))
    s.append('<line x1="{:.1f}" y1="{}" x2="{:.1f}" y2="{}" stroke="{}" stroke-width="1"/>'.format(zero, TOP - 4, zero, H - 18, BASE))
    for i, (label, v) in enumerate(rows):
        y = TOP + i * ROW
        s.append('<text x="{}" y="{:.0f}" font-size="10.5" fill="{}" text-anchor="end">{}</text>'.format(LEFT - 8, y + BAR - 3, INK, esc(label)))
        col = C_POS if v >= 0 else C_NEG
        s.append('<path d="{}" fill="{}"/>'.format(bar_path(zero, y, px(v), BAR), col))
        anc = "start" if v >= 0 else "end"
        off = 5 if v >= 0 else -5
        s.append('<text x="{:.1f}" y="{:.0f}" font-size="9.5" font-weight="700" fill="{}" text-anchor="{}">{:+.0f} %</text>'.format(px(v) + off, y + BAR - 3, INK, anc, v))
    s.append("</svg>")
    return "".join(s)

CSS = """
* { box-sizing:border-box; }
body{font-family:"Liberation Sans","DejaVu Sans",Arial,sans-serif;font-size:10pt;color:#0b0b0b;margin:0;line-height:1.42;}
h1{font-size:23pt;margin:0 0 6px;line-height:1.15;} h2{font-size:15pt;margin:0 0 10px;padding-bottom:4px;border-bottom:1px solid #c3c2b7;}
h3{font-size:12pt;margin:16px 0 6px;} h4{font-size:10pt;margin:11px 0 4px;color:#52514e;}
p{margin:0 0 8px;} .muted{color:#898781;} .sec{color:#52514e;} .small{font-size:8.5pt;}
.cover{padding-top:52px;} .cover .kicker{text-transform:uppercase;letter-spacing:.08em;font-size:9pt;color:#52514e;margin-bottom:14px;}
.cover .sub{font-size:12.5pt;color:#52514e;margin:10px 0 24px;}
.cover .meta{border-top:1px solid #e1e0d9;padding-top:12px;font-size:9.5pt;color:#52514e;} .cover .meta div{margin-bottom:5px;}
.page{break-before:page;} table{width:100%;border-collapse:collapse;font-size:8.7pt;margin:6px 0 12px;}
th,td{border-bottom:1px solid #e1e0d9;padding:4px 6px;text-align:left;vertical-align:top;}
th{background:#f4f4f1;color:#52514e;font-weight:700;font-size:8.2pt;border-bottom:1px solid #c3c2b7;}
tr{break-inside:avoid;} td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
td.min{font-weight:700;}
.badge{display:inline-block;font-size:7.6pt;padding:1px 6px;border-radius:9px;white-space:nowrap;}
.badge.ok{background:#e3f3e3;color:#0a5a0a;} .badge.warn{background:#fff1dc;color:#7a4b00;} .badge.bad{background:#fbe3e3;color:#8a1f1f;}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:10px 0 14px;}
.tile{border:1px solid #e1e0d9;border-radius:8px;padding:9px 11px;break-inside:avoid;}
.tile .lbl{font-size:8.3pt;color:#52514e;} .tile .val{font-size:15pt;font-weight:700;margin:1px 0;} .tile .src{font-size:7.8pt;color:#898781;}
.callout{border-left:3px solid #2a78d6;background:#f6f9fd;padding:8px 12px;margin:10px 0 14px;}
.callout.warn{border-left-color:#eda100;background:#fffaf0;} .callout.bad{border-left-color:#d03b3b;background:#fdf3f3;}
.chart{margin:6px 0 14px;break-inside:avoid;}
ul,ol{margin:4px 0 10px 18px;padding:0;} li{margin-bottom:4px;}
.note{font-size:8.6pt;color:#52514e;background:#f8f8f6;padding:6px 10px;border-radius:6px;margin:4px 0 10px;}
.sources li{font-size:8pt;word-break:break-all;} .cols2{columns:2;column-gap:22px;}
"""

H = []
H.append("<!doctype html><html lang='ru'><head><meta charset='utf-8'><title>Закупка из Китая — StyleNova</title><style>" + CSS + "</style></head><body>")

# Cover
H.append('<section class="cover">')
H.append('<div class="kicker">StyleNova · закупка и перепродажа</div>')
H.append('<h1>Закупка комплектующих из Китая: расчёт маржи</h1>')
H.append('<div class="sub">DDR4, SSD SATA и HDD — оптовые цены Alibaba/1688, себестоимость с ввозом в РФ и наценка при перепродаже. Срез на ' + TODAY_RU + '.</div>')
H.append('<div class="meta">')
H.append('<div><b>Курс:</b> $1 = ' + str(USD) + ' ₽, ¥1 = ' + str(CNY) + ' ₽ (ЦБ РФ, ' + esc(ctx.get("rate_date", TODAY_RU)) + ').</div>')
H.append('<div><b>Себестоимость (landed)</b> = FOB Китай × 1,30: НДС при ввозе 22 % (для УСН невозвратный) + логистика ~8 %; пошлина на комплектующие — 0 %.</div>')
H.append('<div><b>«Продажа в РФ»</b> — реалистичные цены из вашего отчёта по рынку от ' + TODAY_RU + '.</div>')
H.append('</div>')
H.append('<div class="callout bad" style="margin-top:22px"><b>Вывод в двух строках.</b> В 2026-м из-за дефицита DRAM новую память из Китая возить НЕЛЬЗЯ — себестоимость с ввозом выше розницы РФ (убыток). Деньги там, где Китай реально дешевле рынка РФ: <b>бюджетные SATA SSD 512 ГБ – 1 ТБ (наценка 50–150 %)</b> и <b>recertified-HDD 4–6 ТБ (20–45 %)</b>. На памяти зарабатывайте скупкой б/у внутри РФ, а не импортом.</div>')
H.append('</section>')

# Section 1: где деньги
good = [r for r in ROWS if r["verdict"] == "good"]
H.append('<section class="page"><h2>1. Где реально деньги</h2>')
H.append('<div class="tiles">')
for r in sorted(good, key=lambda r: -r["markup"])[:6]:
    H.append('<div class="tile">')
    H.append('<div class="lbl">' + esc(r["short"]) + ' · ' + esc(r["src"]) + '</div>')
    H.append('<div class="val" style="color:#0a5a0a">+{:.0f} %</div>'.format(r["markup"]))
    H.append('<div class="src">закупка ~' + rub(r["landed"]) + ' → продажа ' + rub(r["sell_lo"]) + '–' + rub(r["sell_hi"]) + '<br>прибыль ~' + rub(r["profit"]) + ' с 1 шт.</div>')
    H.append('</div>')
H.append('</div>')
H.append('<div class="callout"><b>Три приоритета закупки.</b> 1) <b>SSD 512 ГБ – 1 ТБ</b> (бюджет/no-name) — максимальная наценка и быстрый оборот. 2) <b>Recertified HDD 4–6 ТБ</b> — крупная прибыль с 1 шт., идеально ложится в профиль магазина б/у техники (тест + своя гарантия). 3) <b>SSD 2 ТБ и HDD 2 ТБ</b> — хороший объём прибыли на партии.</div>')
H.append('<div class="callout bad"><b>Что не возить.</b> Новую DDR4 (4/8/16/32 ГБ): себестоимость с ввозом равна или выше розницы РФ — это гарантированный минус. Исключение — б/у «pulled»-лоты памяти с 1688 (разбор), но их выгоднее и безопаснее набирать скупкой на Авито.</div>')
H.append('</section>')

# Section 2: full table
H.append('<section class="page"><h2>2. Таблица закупки: Китай → себестоимость в РФ → продажа → наценка</h2>')
H.append('<p class="sec">FOB — цена за 1 шт. на Alibaba/1688 (ориентир для качественного/рабочего товара; рок-боттом no-name бывает ниже). Себестоимость — с учётом ввоза (×1,30). Наценка считается от продажи по середине диапазона.</p>')
H.append('<table><thead><tr><th>Позиция</th><th>Тип товара</th><th class="num">FOB Китай</th><th class="num">Себест. в РФ</th><th class="num">Продажа в РФ</th><th class="num">Наценка</th><th class="num">Прибыль/шт</th><th>Итог</th></tr></thead><tbody>')
last = None
for r in ROWS:
    if r["cat"] != last:
        H.append('<tr><td colspan="8" style="background:#f4f4f1;font-weight:700;color:#52514e">' + esc(CAT_TITLES[r["cat"]]) + '</td></tr>')
        last = r["cat"]
    vru, vcls = V_RU[r["verdict"]]
    H.append('<tr><td><b>' + esc(r["short"]) + '</b></td><td class="small">' + esc(r["src"]) + '</td>'
             '<td class="num">${:.0f}<br><span class="muted">'.format(r["fob_usd"]) + rub(r["fob_rub"]) + '</span></td>'
             '<td class="num min">' + rub(r["landed"]) + '</td>'
             '<td class="num">' + rub(r["sell_lo"]) + '–' + rub(r["sell_hi"]) + '</td>'
             '<td class="num" style="color:' + (C_POS if r["markup"] >= 0 else C_NEG) + ';font-weight:700">{:+.0f} %</td>'.format(r["markup"]) +
             '<td class="num" style="color:' + (C_POS if r["profit"] >= 0 else C_NEG) + '">' + rub(r["profit"]) + '</td>'
             '<td><span class="badge ' + vcls + '">' + vru + '</span></td></tr>')
H.append('</tbody></table>')
H.append('<div class="note"><b>Пример на партию.</b> 100× SSD 512 ГБ: закупка ~' + rub(100 * ROWS[6]["landed"]) + ', выручка при продаже по 4 500 ₽ = 450 000 ₽, валовая прибыль ~' + rub(100 * (4500 - ROWS[6]["landed"])) + ' (до расходов на рекламу, возвраты и комиссию площадок).</div>')
H.append('</section>')

# Section 3: charts
H.append('<section class="page"><h2>3. Графики: себестоимость против продажи</h2>')
for cat in CAT_ORDER:
    rows = [(r["short"], round(r["landed"]), round(r["sell_mid"])) for r in ROWS if r["cat"] == cat]
    H.append('<div class="chart">' + chart_grouped(rows, CAT_TITLES[cat] + ": себестоимость (Китай+ввоз) и продажа в РФ, ₽", "Где синий столбик выше оранжевого — импорт убыточен") + '</div>')
H.append('</section>')

H.append('<section class="page"><h2>4. Наценка по позициям</h2>')
rows = [(r["short"], r["markup"]) for r in ROWS]
H.append('<div class="chart">' + chart_diverging(rows, "Наценка при перепродаже, % к себестоимости", "Зелёное — выгодно; красное — импорт убыточен (себестоимость выше цены продажи)") + '</div>')
H.append('<div class="note">Наценка = (цена продажи ÷ себестоимость − 1). Отрицательные значения по памяти означают, что новый модуль из Китая с ввозом обходится дороже, чем его можно продать в России.</div>')
H.append('</section>')

# Section 5: import mechanics
H.append('<section class="page"><h2>5. Как считать себестоимость и ввозить</h2>')
H.append('<h3>Из чего складывается цена «на полке»</h3><ul>')
H.append('<li><b>FOB Китай</b> — цена за 1 шт. у поставщика (Alibaba в $, 1688 в ¥). Считайте всегда за 1 штуку: киты 2×8/2×16 маскируют под «16/32 ГБ».</li>')
H.append('<li><b>Логистика до РФ</b> — товар лёгкий; авиа/карго ~$3–8 за кг, в пересчёте на модуль/диск это +6–10 %.</li>')
H.append('<li><b>Пошлина — 0 %</b> для памяти, SSD и HDD (ТН ВЭД 8471/8473) в ЕАЭС.</li>')
H.append('<li><b>НДС при ввозе — 22 %</b> (ставка 2026). На ОСНО его можно принять к вычету, на УСН — это чистый расход. В расчёте заложен невозвратный НДС.</li>')
H.append('<li><b>Курс и комиссия за оплату/агента</b> — закладывайте +2–4 % на конвертацию и услуги байера.</li>')
H.append('</ul>')
H.append('<div class="callout warn"><b>Белый импорт против карго.</b> Карго (серая схема) дешевле примерно на 15 %, но БЕЗ документов: товар нельзя легально продавать на Ozon/Яндекс Маркете, нельзя оформить гарантию и принять НДС к вычету. Для магазина берите белый параллельный импорт через агента — товар растаможен, с документами, его можно ставить на витрину и в маркетплейсы.</div>')
H.append('<h3>Практика закупки</h3><ul>')
H.append('<li><b>MOQ:</b> заводские цены обычно от 50–100 шт. на SSD, от 10–50 на HDD. Начинайте с пробной мелкой партии одного проверенного поставщика.</li>')
H.append('<li><b>Котировки живут 72 часа</b> в текущий дефицит — фиксируйте цену инвойсом и оплачивайте быстро.</li>')
H.append('<li><b>Проверяйте продавца:</b> Trade Assurance на Alibaba, рейтинг и «златопоставщик» на 1688, отзывы, годы на площадке.</li>')
H.append('</ul></section>')

# Section 6: risks
H.append('<section class="page"><h2>6. Риски и контроль качества</h2>')
H.append('<div class="callout bad"><b>Дешёвые SSD за $6–18 — это no-name Shenzhen.</b> Часто DRAM-less QLC, иногда поддельная ёмкость и перемаркированные чипы. Продавать их «как новые брендовые» — удар по репутации магазина, который держится на доверии.</div>')
H.append('<h3>Обязательный входной контроль</h3><ul>')
H.append('<li><b>SSD:</b> CrystalDiskInfo (здоровье, атрибуты), H2testw или FakeFlashTest (реальная ёмкость), контрольная запись/чтение. Указывайте тип памяти (TLC/QLC) и наличие DRAM честно в карточке.</li>')
H.append('<li><b>HDD (recertified):</b> SMART — наработка часов (Power-On Hours), Reallocated/Pending Sectors, тест поверхности (Victoria/HD Tune). Это б/у с датацентра — так и продавайте, с прозрачным отчётом SMART в объявлении.</li>')
H.append('<li><b>Память:</b> MemTest86 на несколько проходов; проверка, что модуль одиночный и заявленного объёма/частоты.</li>')
H.append('</ul>')
H.append('<h3>Как это ложится в StyleNova</h3>')
H.append('<p>Ваш магазин — про б/у технику с проверкой и гарантией. Recertified-HDD и протестированные SSD/память с честным описанием состояния и своей гарантией магазина — это ровно ваш формат: покупатель платит за проверку и спокойствие, а вы держите наценку. No-name SSD «как новые» без тестов — не ваш путь: вернётся возвратами и отзывами.</p>')
H.append('<div class="note"><b>Отбраковка и возвраты.</b> Закладывайте 3–8 % брака на no-name SSD и 5–10 % на recertified HDD в себестоимость партии — это уже учтено, если продавать по верхней части диапазона.</div>')
H.append('</section>')

# Section 7: sources
H.append('<section class="page"><h2>7. Источники и оговорки</h2>')
H.append('<h3>Оговорки</h3><ul>')
H.append('<li>Цены FOB — ориентиры из оптовых листингов Alibaba/1688 и рыночных сводок на ' + TODAY_RU + '; конкретная цена зависит от поставщика, партии и дня (в дефицит меняется еженедельно).</li>')
H.append('<li>Продажные цены РФ взяты из сопутствующего отчёта по рынку от той же даты.</li>')
H.append('<li>Себестоимость — модельная оценка (×1,30). Точные цифры зависят от вашей схемы ввоза, режима налогообложения и логиста.</li>')
H.append('<li>Материал носит справочный характер и не является налоговой/таможенной консультацией и публичной офертой.</li>')
H.append('</ul>')
H.append('<h3>Источники</h3><ol class="sources cols2">')
SRC = [
    ("Alibaba — 8GB/16GB DDR4 wholesale price guide 2026", "https://electronics.alibaba.com/product/8gb-ram-price"),
    ("Alibaba — 256GB/512GB/1TB SATA SSD wholesale 2026", "https://electronics.alibaba.com/product/sata-ssd"),
    ("Alibaba — 1TB SSD price guide 2026 (from $29.88)", "https://electronics.alibaba.com/product/ssd-1tb-price"),
    ("Alibaba — recertified HDD $15–22/TB, new 2TB $75–100", "https://electronics.alibaba.com/product/refurbished-hard-disk"),
    ("1688 — 512G SSD от ¥76,9 (MOQ 50)", "https://www.1688.com/market/-35313267B9CCCCACD3B2C5CC.html"),
    ("1688 — DDR4 8G/16G оптом", "https://s.1688.com/kq/-CCA8CABDC4DAB4E6CCF5.html"),
    ("memoryindex.io — DDR4 8Gb спот $44,5 (сен. 2026)", "https://memoryindex.io/ddr4-price"),
    ("TNL Group — пошлины и НДС 22% на товары из Китая 2026", "https://tnlgroup.ru/blog/poshliny-i-nalogi-iz-kitaya/"),
    ("whiteroute.ru — НДС при импорте электроники из Китая 2026", "https://whiteroute.ru/blog/nds-pri-importe-elektroniki/"),
    ("vc.ru — импорт из Китая: расчёт себестоимости 2026", "https://vc.ru/marketplace/2945838"),
]
for t, u in SRC:
    H.append('<li>' + esc(t) + ' — <a href="' + esc(u) + '">' + esc(u[:70]) + '</a></li>')
H.append('</ol>')
H.append('<p class="small muted">Подготовлено для магазина StyleNova (б/у компьютерная техника). Дополняет отчёт по ценам на комплектующие от ' + TODAY_RU + '.</p>')
H.append('</section></body></html>')

open(OUT, "w", encoding="utf-8").write("\n".join(H))
print("HTML written:", OUT)
