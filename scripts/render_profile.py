"""Render the light profile with animated language bars and a static header."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
W = 1120
BG, INK, MUTED, GREEN, BLUE = '#f7f8f4', '#25382f', '#67766d', '#3c806c', '#577eb2'


def font(size, bold=False):
    override = os.environ.get('PROFILE_FONT_BOLD' if bold else 'PROFILE_FONT')
    candidates = [override,
                  'C:/Windows/Fonts/msyhbd.ttc' if bold else 'C:/Windows/Fonts/msyh.ttc',
                  '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc' if bold else
                  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
    for path in candidates:
        if path and Path(path).exists():
            return ImageFont.truetype(path, size)
    raise RuntimeError('A Chinese font is required; set PROFILE_FONT and PROFILE_FONT_BOLD.')


def text(draw, pos, value, size=24, fill=INK, bold=False):
    draw.text(pos, value, font=font(size, bold), fill=fill)


def centered(draw, y, value, size=24, fill=INK, bold=False):
    f = font(size, bold)
    draw.text(((W - draw.textlength(value, font=f)) / 2, y), value, font=f, fill=fill)


def header():
    im = Image.new('RGB', (W, 320), BG)
    d = ImageDraw.Draw(im)
    for x in range(810, 1100, 26):
        for y in range(30, 302, 26):
            d.ellipse((x, y, x+2, y+2), fill='#d9e1d9')
    text(d, (52, 38), '保持好奇，认真创造。', 20, MUTED)
    text(d, (46, 99), 'Nostalgia', 76, INK, True)
    x = 46 + d.textlength('Nostalgia', font=font(76, True))
    text(d, (x, 99), '546', 76, GREEN, True)
    text(d, (52, 218), '把想法写成代码，把细节做到最后。', 25, MUTED)
    d.line((52, 278, 96, 278), fill=GREEN, width=3)
    text(d, (111, 263), '代码  /  设计  /  探索', 17, MUTED)
    dy = 0
    top, left, middle, right, bottom = (955, 52+dy), (849, 108+dy), (955, 170+dy), (1061, 108+dy), (955, 289+dy)
    d.polygon((top, right, middle, left), fill='#edf2ed', outline='#b6cabb', width=2)
    d.polygon((left, middle, bottom, (849, 227+dy)), fill='#f0f3ed', outline='#b6cabb', width=2)
    d.polygon((middle, right, (1061, 227+dy), bottom), fill='#e7eee8', outline='#b6cabb', width=2)
    d.line([(880, 214+dy), (880, 144+dy), (1030, 247+dy), (1030, 171+dy)], fill=GREEN, width=8)
    return im


def language_groups(data):
    # Apply the exclusion here as well, so old snapshots are safe to render.
    items = sorted(((name, size) for name, size in data['languages'].items()
                    if name != 'C++'), key=lambda kv: kv[1], reverse=True)
    total = sum(value for _, value in items)
    groups = items[:7]
    remaining = sum(value for _, value in items[7:])
    if remaining:
        groups.append(('其他', remaining))
    if not total:
        raise ValueError('No language data remains after filtering.')
    return groups, total


def ease(value):
    value = max(0, min(1, value))
    return 1 - (1 - value) ** 3


def activity(data, progress=1):
    im = Image.new('RGB', (W, 1055), BG)
    d = ImageDraw.Draw(im)
    text(d, (48, 35), '持续构建，留下痕迹。', 30, INK, True)
    text(d, (48, 84), '公开与私有贡献汇总', 18, MUTED)
    days = data['days']
    active = sum(day['contributionCount'] > 0 for day in days)
    best, run = 0, 0
    for day in days:
        run = run+1 if day['contributionCount'] else 0
        best = max(best, run)
    for x, number, label in [(48, f"{data['total_contributions']:,}", '近一年贡献'),
                              (403, str(active), '有贡献的天数'), (758, str(best), '最长连续天数')]:
        d.rounded_rectangle((x, 135, x+314, 268), radius=18, fill='#ffffff', outline='#e0e6df')
        text(d, (x+24, 151), number, 43, GREEN, True)
        text(d, (x+25, 220), label, 18, MUTED)
    text(d, (48, 319), '代码里的技术足迹', 26, INK, True)
    text(d, (48, 361), '包含私有仓库 · 已排除 C++ · 按代码字节量统计', 17, MUTED)
    groups, total = language_groups(data)
    colors = ['#4f7f73', '#698ab5', '#98b196', '#8c87aa', '#b99372', '#b8bf86', '#6ea4ae', '#d5dcd4']
    x = 48
    d.rounded_rectangle((48, 410, 1072, 431), radius=5, fill='#e5eae3')
    revealed = 48 + int(1024 * ease(progress))
    for index, (name, value) in enumerate(groups):
        end = 1072 if index == len(groups)-1 else x+int(1024*value/total)
        if revealed > x:
            d.rectangle((x, 410, min(end, revealed), 431), fill=colors[index])
        x = end
        row, col = divmod(index, 2)
        px, py = 48+col*550, 460+row*57
        d.ellipse((px, py+7, px+10, py+17), fill=colors[index])
        text(d, (px+22, py), name, 18)
        opacity = ease((progress-.35-index*.025)/.35)
        background = tuple(int(BG[i:i+2], 16) for i in (1, 3, 5))
        foreground = tuple(int(MUTED[i:i+2], 16) for i in (1, 3, 5))
        percentage_color = tuple(round(a+(b-a)*opacity) for a, b in zip(background, foreground))
        text(d, (px+397, py), f'{value/total:.1%}', 18, percentage_color)
        d.rounded_rectangle((px, py+32, px+474, py+39), radius=3, fill='#e5eae3')
        fill_width = int(474 * value / total * ease((progress-index*.035)/.755))
        if fill_width > 0:
            d.rounded_rectangle((px, py+32, px+fill_width, py+39), radius=3, fill=colors[index])
    text(d, (48, 713), '贡献日历', 26, INK, True)
    start = dt.date.fromisoformat(days[0]['date'])
    offset = (start.weekday()+1)%7
    shades = ['#e6ebe3', '#c1d6bf', '#8cb69b', '#5a977b', '#326e57']
    maxcount = max(day['contributionCount'] for day in days) or 1
    for i, day in enumerate(days):
        column, row = divmod(i+offset, 7)
        x, y = 48+column*19, 770+row*20
        count = day['contributionCount']
        level = 0 if not count else min(4, 1+int(3*count/maxcount))
        d.rounded_rectangle((x, y, x+15, y+15), radius=3, fill=shades[level])
    text(d, (48, 924), f"{days[0]['date']} — {days[-1]['date']}", 16, MUTED)
    text(d, (902, 924), '少', 15, MUTED)
    for i, color in enumerate(shades):
        d.rounded_rectangle((929+i*23, 929, 944+i*23, 944), radius=3, fill=color)
    text(d, (1050, 924), '多', 15, MUTED)
    d.line((48, 982, 1072, 982), fill='#dde4da', width=1)
    text(d, (48, 1001), '仅展示汇总 · 语言占比不代表熟练程度 · 贡献统计未排除旧项目', 16, MUTED)
    return im


def preview_frame(hero, chart):
    canvas = Image.new('RGB', (W, 1590), '#ffffff')
    canvas.paste(hero, (0, 0))
    d = ImageDraw.Draw(canvas)
    centered(d, 355, '喜欢简洁的界面、可控的系统，以及值得反复打磨的小东西。', 23)
    centered(d, 414, '界面与交互   ·   AI 与自动化   ·   系统与部署', 21, MUTED)
    centered(d, 466, 'Vue  /  Rust  /  Kotlin  /  Dart  /  Python  /  TypeScript', 20, GREEN)
    canvas.paste(chart, (0, 535))
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview-dir', type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT/'data/profile.json').read_text(encoding='utf-8'))
    assert data['includes_private'] and data['languages'] and data['days']
    assert sum(d['contributionCount'] for d in data['days']) == data['total_contributions']
    assets = ROOT/'assets'
    assets.mkdir(exist_ok=True)
    chart = activity(data)
    chart.save(assets/'activity.png', optimize=True)
    hero = header()
    hero.save(assets/'header.png', optimize=True)
    frames = [activity(data, i/32) for i in range(33)]
    palette = chart.quantize(colors=256)
    frames = [frame.quantize(palette=palette, dither=Image.Dither.NONE) for frame in frames]
    durations = [60] * 32 + [5600]
    frames[0].save(assets/'activity.gif', save_all=True, append_images=frames[1:],
                   duration=durations, loop=0, optimize=True, disposal=1)
    if args.preview_dir:
        args.preview_dir.mkdir(parents=True, exist_ok=True)
        preview = preview_frame(hero, chart)
        preview.save(args.preview_dir/'profile-preview.png', optimize=True)
        previews = [preview_frame(hero, frame).resize((840, 1192), Image.Resampling.LANCZOS) for frame in frames]
        preview_palette = preview.resize((840, 1192), Image.Resampling.LANCZOS).quantize(colors=256)
        previews = [frame.quantize(palette=preview_palette, dither=Image.Dither.NONE) for frame in previews]
        previews[0].save(args.preview_dir/'profile-preview.gif', save_all=True, append_images=previews[1:],
                         duration=durations, loop=0, optimize=True, disposal=1)
    print('Light profile images generated from aggregate data.')


if __name__ == '__main__':
    main()
