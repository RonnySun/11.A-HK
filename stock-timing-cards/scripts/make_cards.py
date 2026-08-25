#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把股票分析结论生成三张卡图 + 一张合并长图。
用法：改下面 DATA 后运行 /tmp/smoore_venv/bin/python make_cards.py
依赖：Pillow
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1700
M = 64
FP = "/System/Library/Fonts/Hiragino Sans GB.ttc"
FB = "/System/Library/Fonts/STHeiti Medium.ttc"

def F(path, size):
    return ImageFont.truetype(path, size, index=0)

def rr(d, box, rad, fill):
    d.rounded_rectangle(box, radius=rad, fill=fill)

def wrap(text, font, maxw):
    lines, cur = [], ""
    for ch in text:
        if font.getlength(cur + ch) <= maxw:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def bar(d, x, y, w, h, frac, accent):
    rr(d, [x, y, x + w, y + h], h // 2, "#E5E7EB")
    if frac > 0:
        rr(d, [x, y, x + max(int(w * frac), h), y + h], h // 2, accent)

def render_card(path, accent, title, subtitle, keyline, big, big_sub, big_note, rows, extra_title, extra_items, footer):
    img = Image.new("RGB", (W, H), "#F7F8FA")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 240], fill=accent)
    d.text((M, 62), title, font=F(FB, 60), fill="#FFFFFF")
    d.text((M, 142), subtitle, font=F(FP, 34), fill="#E8EEFF")
    d.text((M, 270), keyline, font=F(FP, 28), fill="#6B7280")
    d.text((M, 320), big, font=F(FB, 132), fill=accent)
    bw = F(FB, 132).getlength(big)
    d.text((M + bw + 12, 398), big_sub, font=F(FP, 40), fill="#6B7280")
    if big_note:
        d.text((M, 470), big_note, font=F(FP, 26), fill="#9CA3AF")
    try:
        bar(d, M, 505, W - 2 * M, 18, float(big), accent)
    except ValueError:
        pass
    y = 565
    for label, sc, mx, note in rows:
        d.text((M, y), label, font=F(FB, 36), fill="#111827")
        t = f"{sc} / {mx}"
        sw = F(FB, 34).getlength(t)
        d.text((W - M - sw, y), t, font=F(FB, 34), fill=accent)
        for i, ln in enumerate(wrap(note, F(FP, 27), W - 2 * M)[:2]):
            d.text((M, y + 48 + i * 36), ln, font=F(FP, 27), fill="#4B5563")
        bar(d, M, y + 125, W - 2 * M, 10, sc / mx, accent)
        y += 158
    if extra_title:
        y += 6
        d.text((M, y), extra_title, font=F(FB, 38), fill="#111827")
        y += 60
        for lead, txt in extra_items:
            d.text((M, y), lead, font=F(FB, 30), fill=accent)
            lw = F(FB, 30).getlength(lead)
            lines = wrap(txt, F(FP, 27), W - 2 * M - lw - 8)
            for i, ln in enumerate(lines):
                d.text((M + lw + 8, y + i * 38), ln, font=F(FP, 27), fill="#374151")
            y += 38 * max(1, len(lines)) + 16
    d.text((M, H - 96), footer, font=F(FP, 24), fill="#9CA3AF")
    img.save(path, "PNG")
    return img

def render_all(data, prefix="card"):
    name = data["name"]
    b = data["buy"]; s = data["sell"]; sm = data["summary"]
    c1 = render_card(prefix + "1_buy.png", "#0E9F6E", name, "买入信号评分（这个票值不值得买）",
                     b["keyline"], str(b["score"]), "/ 10", "满分 10 分，分数越高越值得买",
                     b["rows"], "近期新闻 · 政策 · 行业", b["news"], "数据日期 · 仅供研究，不构成投资建议")
    c2 = render_card(prefix + "2_sell.png", "#E5484D", name, "卖出信号评分（要不要卖 / 减仓）",
                     s["keyline"], str(s["score"]), "/ 10", "满分 10 分，分数越高越该卖",
                     s["rows"], "谁在买、谁在卖", s["who"], "一句话资金面判断")
    c3 = render_card(prefix + "3_summary.png", "#2563EB", name, "综合总结（到底该怎么办）",
                     sm["keyline"], sm["conclusion"], "", sm["note"],
                     sm["rows"], "关键价位 + 接下来盯", sm["watch"], "数据来源 · 不构成投资建议")
    h1, h2, h3 = c1.height, c2.height, c3.height
    DS = 470
    total = Image.new("RGB", (W, h1 + h2 + h3 + DS), "#FFFFFF")
    total.paste(c1, (0, 0)); total.paste(c2, (0, h1)); total.paste(c3, (0, h1 + h2))
    d = ImageDraw.Draw(total)
    y0 = h1 + h2 + h3
    d.rectangle([0, y0, W, y0 + DS], fill="#0F172A")
    d.text((64, y0 + 42), "数据来源（截至日期）", font=F(FB, 42), fill="#FFFFFF")
    yy = y0 + 112
    for sline in data["sources"]:
        for ln in wrap(sline, F(FP, 29), W - 2 * M):
            d.text((64, yy), "· " + ln, font=F(FP, 29), fill="#CBD5E1")
            yy += 42
    total.save(prefix + "_cards.png", "PNG")
    print("saved", prefix + "1_buy.png / 2_sell.png / 3_summary.png / _cards.png")

DATA = {
    "name": "格式模板 · 0000.HK",
    "buy": {
        "keyline": "现价 — · 市值 — · 市盈率 — · 股息率 —",
        "score": 5.0,
        "rows": [
            ("公司赚钱变好了吗", 1.5, 3, "示例：利润转正 / 加速，毛利率是否企稳"),
            ("这个价格贵不贵", 1.0, 2, "示例：市盈率处历史低位 / PEG<1"),
            ("股价是不是在涨", 2.0, 3, "示例：站上 20/60 日线，放量突破"),
            ("大资金在买吗", 1.0, 2, "示例：减持落地、资金由流出转流入"),
        ],
        "news": [
            ("5月", "示例事件（利好 / 利空）"),
            ("4月", "示例政策（利好 / 利空）"),
            ("8月", "示例中报（利好）"),
            ("行业", "示例：龙头 / 竞争格局"),
        ],
    },
    "sell": {
        "keyline": "现价 — · 市盈率 — · 最近一年：最低 — / 最高 —",
        "score": 4.0,
        "rows": [
            ("公司赚钱变差了吗", 1.0, 3, "示例：毛利率持续走低"),
            ("价格是不是太贵", 1.0, 2, "示例：市盈率远超历史"),
            ("股价跌破位了吗", 0.5, 3, "示例：跌破均线"),
            ("有大股东在卖吗", 1.5, 2, "示例：大股东减持中"),
        ],
        "who": [
            ("谁在买", "示例：大股东增持 / 南向加仓"),
            ("谁在卖", "示例：机构减持"),
            ("南向资金", "示例：持股比例 / 净买卖"),
            ("国际机构", "示例：持仓比例变化"),
        ],
    },
    "summary": {
        "keyline": "现价 — · 分析师目标均价 —",
        "conclusion": "观察 / 持有",
        "note": "买入 X 分 vs 卖出 Y 分，净多空判断",
        "rows": [
            ("买入分数", 5.0, 10, "示例：亮点 + 短板"),
            ("卖出分数", 4.0, 10, "示例：主要压制"),
        ],
        "watch": [
            ("下方防线", "支撑 —（20日线）/ —（60日线）"),
            ("上方阻力", "压力 —（前高）→ —"),
            ("止损", "跌破支撑减仓、失守再大幅减仓"),
            ("盯①", "示例：减持进度"),
            ("盯②", "示例：能否放量站稳前高"),
        ],
    },
    "sources": [
        "行情/估值/均线：Yahoo Finance（yfinance）",
        "财务：公司财报、东方财富、财联社",
        "股东/减持/南向：公司公告、港交所披露易",
        "免责：仅供个人研究学习，不构成投资建议",
    ],
}

if __name__ == "__main__":
    render_all(DATA)
