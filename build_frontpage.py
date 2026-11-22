#!/usr/bin/env python3
"""Render the 21 November 2026 front page of THE WORLD as a 1024x1024 PNG.

All headlines and figures come from the story list in README.md, checked
against live news on the morning of 22 November 2026 (Beijing time). The
only picture is the pre-generated hero illustration in assets/; every word
on the page is drawn here with PIL. No network access, no secrets.
"""

import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
HERO = os.path.join(
    BASE,
    "assets",
    "media-generation-hero-gulf-night-strike-2026112-0-ce5385a1-e76b-4daa-8942-c801e129167d.webp",
)
OUT = os.path.join(BASE, "entry.png")

PAGE = 1024
SIDE = 40
SPAN = PAGE - 2 * SIDE
LIMIT = 1_000_000

PAPER = (247, 241, 229)
INK = (17, 17, 17)
MUTED = (68, 60, 52)
RED = (143, 29, 29)
NAVY = (27, 42, 74)

FONTS = "/usr/share/fonts/truetype/liberation/"


def load(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def serif_b(size):
    return load("LiberationSerif-Bold.ttf", size)


def serif(size):
    return load("LiberationSerif-Regular.ttf", size)


def serif_i(size):
    return load("LiberationSerif-Italic.ttf", size)


def sans_b(size):
    return load("LiberationSans-Bold.ttf", size)


def width(draw, text, font):
    return draw.textlength(text, font=font)


def greedy_wrap(draw, text, font, max_w):
    out, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if not cur or width(draw, trial, font) <= max_w:
            cur = trial
        else:
            out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def centered(draw, cx, y, text, font, fill=INK):
    draw.text((cx - width(draw, text, font) / 2, y), text, font=font, fill=fill)


def tracked(draw, cx, y, text, font, gap, fill=INK):
    ws = [draw.textlength(ch, font=font) for ch in text]
    total = sum(ws) + gap * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, ws):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + gap


def rule(draw, y, weight, x0=SIDE, x1=PAGE - SIDE):
    draw.line([(x0, y), (x1, y)], fill=INK, width=weight)


def shrink_to_fit(draw, text, path, start, max_w):
    size = start
    while size > 10:
        fnt = load(path, size)
        if width(draw, text, fnt) <= max_w:
            return fnt
        size -= 2
    return load(path, 10)


def main():
    sheet = Image.new("RGB", (PAGE, PAGE), PAPER)
    d = ImageDraw.Draw(sheet)
    y = 22

    # Masthead
    tracked(d, PAGE // 2, y, "ONE DAY · ONE PAGE", sans_b(15), 6, MUTED)
    y += 30
    name = shrink_to_fit(d, "THE WORLD", "LiberationSerif-Bold.ttf", 118, SPAN)
    centered(d, PAGE // 2, y - 14, "THE WORLD", name)
    y += 98
    rule(d, y, 3)
    y += 5
    rule(d, y, 1)
    y += 12
    centered(d, PAGE // 2, y, "SATURDAY,  21 NOVEMBER 2026", serif_b(30), RED)
    y += 42
    rule(d, y, 1)
    y += 14

    # Lead story
    head = shrink_to_fit(d, "IRAN STRIKES AT US BASES IN BAHRAIN",
                         "LiberationSerif-Bold.ttf", 56, SPAN)
    centered(d, PAGE // 2, y, "IRAN STRIKES AT US BASES IN BAHRAIN", head)
    y += 56
    deck = ("Tehran says it hit American positions at al-Riffa and Awali; "
            "Bahrain says a civilian plant was hit and set ablaze — the "
            "fourth attack in nine days")
    for line in greedy_wrap(d, deck, serif(22), SPAN - 40):
        centered(d, PAGE // 2, y, line, serif(22))
        y += 26
    y += 8

    # Hero illustration, cropped to the banner's aspect
    photo = Image.open(HERO).convert("RGB")
    ratio = SPAN / 224
    sw, sh = photo.size
    if sw / sh > ratio:
        nw = int(sh * ratio)
        left = (sw - nw) // 2
        photo = photo.crop((left, 0, left + nw, sh))
    else:
        nh = int(sw / ratio)
        top = (sh - nh) // 2
        photo = photo.crop((0, top, sw, top + nh))
    photo = photo.resize((SPAN, 224), Image.LANCZOS)
    sheet.paste(photo, (SIDE, y))
    d.rectangle([SIDE, y, PAGE - SIDE, y + 224], outline=INK, width=1)
    y += 224 + 8
    d.text((SIDE, y),
           "Missiles and drones over the Gulf: the US Fifth Fleet's home "
           "waters, Saturday night. (Illustration)",
           font=serif_i(16), fill=MUTED)
    y += 14

    # Markets ticker
    bar = 36
    d.rectangle([SIDE, y, PAGE - SIDE, y + bar], fill=NAVY)
    tick = ("S&P 500 −3.7%  ·  NASDAQ erases 2026 gains  ·  "
            "ANTHROPIC −9% on day two  ·  NVIDIA −14% to $125.53")
    tick_font = shrink_to_fit(d, tick, "LiberationSans-Bold.ttf", 19, SPAN - 16)
    centered(d, PAGE // 2, y + 8, tick, tick_font, (255, 255, 255))
    y += bar + 6

    # Story grid: two columns, three stories each
    gutter = 30
    col = (SPAN - gutter) // 2
    left_x = SIDE
    right_x = SIDE + col + gutter
    grid_top = y

    def story(x, top, kicker, headline, body):
        yy = top
        d.text((x, yy), kicker, font=sans_b(15), fill=RED)
        yy += 22
        for line in greedy_wrap(d, headline, serif_b(25), col):
            d.text((x, yy), line, font=serif_b(25), fill=INK)
            yy += 28
        yy += 2
        for line in greedy_wrap(d, body, serif(17), col):
            d.text((x, yy), line, font=serif(17), fill=INK)
            yy += 21
        return yy + 10

    left_stories = [
        ("MEXICO",
         "FBI most-wanted cartel boss seized",
         "\u201cChapo Isidro\u201d taken in a Sinaloa raid; at least 11 killed "
         "in the backlash, eight detained."),
        ("UKRAINE",
         "Missile hits Zelenskyy's hometown",
         "Kryvyi Rih: a boy of 7 and a paramedic killed, 60 wounded; "
         "Russian missiles also land in Poland."),
        ("CLIMATE · COP31",
         "Talks run past deadline",
         "Antalya summit in overtime with no deal; fossil-fuel language "
         "the sticking point."),
    ]
    right_stories = [
        ("WASHINGTON",
         "Trump defends Putin ties",
         "After the Shenzhen summit, Zelenskyy calls Putin a killer; "
         "Trump tells Europe to defund Ukraine."),
        ("SCIENCE",
         "AI claims Riemann proof",
         "Anthropic mathematician says Claude proved the 167-year-old "
         "hypothesis in six weeks; checks under way."),
        ("HEALTH",
         "Dengue cut 69% by altered mosquitoes",
         "Wolbachia-carrying mosquitoes slash cases among children in a "
         "Brazil trial."),
    ]
    cy = grid_top
    for s in left_stories:
        cy = story(left_x, cy, *s)
    left_end = cy
    cy = grid_top
    for s in right_stories:
        cy = story(right_x, cy, *s)
    right_end = cy
    mid = SIDE + col + gutter // 2
    d.line([(mid, grid_top), (mid, max(left_end, right_end) - 12)],
           fill=INK, width=1)
    y = max(left_end, right_end) + 2

    # Footer
    rule(d, y, 1)
    y += 10
    also = ("ALSO:   UK and EU sign three post-Brexit deals  ·  EU–Indonesia "
            "trade pact  ·  Gaza strike kills 3 in food truck  ·  Ship ablaze "
            "in Gulf of Finland")
    for line in greedy_wrap(d, also, sans_b(16), SPAN):
        centered(d, PAGE // 2, y, line, sans_b(16))
        y += 22
    y += 2
    centered(d, PAGE // 2, y,
             "Every story above happened or was first reported on "
             "Saturday 21 November 2026.",
             serif_i(15), MUTED)
    y += 24

    assert y <= PAGE, f"page overflowed: cursor at {y}"
    sheet.save(OUT, format="PNG", optimize=True)
    size = os.path.getsize(OUT)
    print(f"wrote {OUT}: {PAGE}x{PAGE}, {size} bytes, cursor ended at y={y}")
    if size >= LIMIT:
        raise SystemExit(f"entry.png is {size} bytes, over the 1 MiB limit")


if __name__ == "__main__":
    main()
