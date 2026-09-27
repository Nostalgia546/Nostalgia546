"""Original white statistics-card layout, backed by the same private aggregates."""
import datetime as dt
import json
from pathlib import Path
from PIL import Image, ImageDraw
from render_profile import font, language_groups, ease

ROOT = Path(__file__).resolve().parents[1]
INK, GREEN, GRAY = '#24292e', '#2f855a', '#586069'


def base(width, height):
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, width-1, height-1), radius=12, outline='#e1e4e8', width=2)
    return image, draw


def label(draw, x, y, value, size=20, color=INK, bold=False):
    draw.text((x, y), str(value), font=font(size, bold), fill=color)


def languages(data, progress=1):
    image, draw = base(700, 350)
    label(draw, 26, 20, '常用语言', 27, GREEN, True)
    label(draw, 26, 65, '包含私有仓库 · 已排除 C++', 16, GRAY)
    groups, total = language_groups(data)
    x, edge = 26, 26+int(648*ease(progress))
    draw.rounded_rectangle((26, 108, 674, 127), radius=3, fill='#f0f2f4')
    for index, (name, count) in enumerate(groups):
        color = data['language_colors'].get(name, '#777777')
        end = 674 if index == len(groups)-1 else x+int(648*count/total)
        if edge>x:draw.rectangle((x,108,min(edge,end),127), fill=color)
        x=end
        row,col=divmod(index,2);px,py=26+col*340,151+row*40
        draw.ellipse((px,py+7,px+12,py+19),fill=color)
        label(draw,px+22,py,f'{name}  {count/total:.1%}',18)
    label(draw,26,315,'按代码字节量统计，不代表熟练程度',15,GRAY)
    return image


def main():
    data=json.loads((ROOT/'data/profile.json').read_text(encoding='utf-8'))
    assets=ROOT/'assets';days=data['days'];best=run=0
    for day in days:
        run=run+1 if day['contributionCount'] else 0;best=max(best,run)
    image,draw=base(1000,218)
    for index,(value,title) in enumerate([(data['total_contributions'],'近一年贡献'),(sum(d['contributionCount']>0 for d in days),'有贡献的天数'),(best,'年内最长连续天数')]):
        x=25+index*333
        label(draw,x+70,34,f'{value:,}',45,GREEN,True)
        label(draw,x+48,108,title,21)
        if index<2:draw.line((x+300,30,x+300,170),fill='#e1e4e8',width=2)
    label(draw,25,178,f"{days[0]['date']} — {days[-1]['date']} · 含私有贡献",15,GRAY)
    image.save(assets/'classic-contributions.png',optimize=True)
    final=languages(data);final.save(assets/'classic-languages.png',optimize=True)
    palette=final.quantize(colors=256)
    frames=[languages(data,i/32).quantize(palette=palette,dither=Image.Dither.NONE) for i in range(33)]
    frames[0].save(assets/'classic-languages.gif',save_all=True,append_images=frames[1:],duration=[60]*32+[5600],loop=0,disposal=1,optimize=True)
    image,draw=base(1100,320)
    label(draw,28,18,'最近 30 天的贡献活动',25,GREEN,True)
    recent=days[-30:];maximum=max(d['contributionCount'] for d in recent) or 1
    for i in range(4):
        y=80+i*55;draw.line((64,y,1068,y),fill='#eaecef');label(draw,12,y-10,str(round(maximum*(3-i)/3)),13,GRAY)
    points=[(64+i*1004/29,245-day['contributionCount']/maximum*165) for i,day in enumerate(recent)]
    draw.polygon([(64,245),*points,(1068,245)],fill='#e6f2e8');draw.line(points,fill=GREEN,width=3)
    for x,y in points:draw.ellipse((x-3,y-3,x+3,y+3),fill=GREEN)
    for i in [0,7,14,21,29]:label(draw,45+i*1004/29,265,recent[i]['date'][5:],14,GRAY)
    image.save(assets/'classic-activity.png',optimize=True)
    print('Original-style contribution, language and activity cards updated.')


if __name__=='__main__':main()
