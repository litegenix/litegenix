#!/usr/bin/env python3
"""Avi-style animated profile card workflow, adapted to LiteGenix colours and content."""
import base64
import datetime
import html
import json
import os
import pathlib
import subprocess
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
FONTS = ROOT / "fonts"
W = 880
# LiteGenix colour system: midnight, cyan, teal and violet.
BG = "#080D12"
PANEL = "#0E1720"
INK = "#F1F7FA"
SOFT = "#C7D2DB"
MUTED = "#8494A2"
RULE = "#20323F"
CYAN = "#00E5FF"
TEAL = "#54D6C8"
VIOLET = "#9AABFF"
FONT_URLS = {
    "serif": "https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf",
    "sans": "https://raw.githubusercontent.com/google/fonts/main/ofl/geist/Geist[wght].ttf",
    "mono": "https://raw.githubusercontent.com/google/fonts/main/ofl/geistmono/GeistMono[wght].ttf",
}
FONT_SPECS = {
    "serif": ("Instrument Serif", "InstrumentSerif-Regular.ttf", "serif-400.woff", "normal", 400),
    "sans": ("Geist", "Geist-Regular.ttf", "geist-400.woff", "normal", 400),
    "sans-b": ("Geist", "Geist-SemiBold.ttf", "geist-600.woff", "normal", 600),
    "mono": ("Geist Mono", "GeistMono-Regular.ttf", "geistmono-400.woff", "normal", 400),
}

def esc(value):
    return html.escape(str(value), quote=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "litegenix-profile-art"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(), response.headers.get("Content-Type", "")

def font_face(keys):
    out = []
    for key in keys:
        family, source_name, output_name, style, weight = FONT_SPECS[key]
        source = FONTS / source_name
        target = FONTS / output_name
        try:
            FONTS.mkdir(parents=True, exist_ok=True)
            if not source.exists():
                source.write_bytes(fetch(FONT_URLS["serif" if key == "serif" else ("sans" if key.startswith("sans") else "mono")])[0])
            if not target.exists():
                subprocess.run(["pyftsubset", str(source), "--output-file=" + str(target),
                                "--flavor=woff", "--text=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,·|—-:/@+()'!?&<>",
                                "--layout-features=*"], check=True, capture_output=True)
            b64 = base64.b64encode(target.read_bytes()).decode()
            out.append(f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};src:url(data:font/woff;base64,{b64}) format('woff')}}")
        except Exception as error:
            print(f"Font {family} unavailable, using fallback: {error}")
    return "".join(out)

CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.8s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media(prefers-reduced-motion:reduce){.r,.f,.g,.p,.live,.n,.sh,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""

def svg(width, height, body, fonts, label, extra_css="", left=0, right=0, bottom=12):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    width = width + left + right
    height += bottom
    style = font_face(fonts) + CSS + extra_css
    if os.environ.get("STATIC"):
        style += ".r,.f,.g,.p,.live,.n{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}" height="{height}" viewBox="0 0 {width:.3f} {height}" role="img" aria-label="{esc(label)}">'
            f'<title>{esc(label)}</title><style>{style}</style>{body}</svg>')

def write(filename, content):
    CARDS.mkdir(parents=True, exist_ok=True)
    (CARDS / filename).write_text(content, encoding="utf-8")
    print(f"wrote cards/{filename} ({len(content)//1024} KB)")

def delay(seconds):
    return f'style="animation-delay:{seconds:.2f}s"'

def wrap(text, width):
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and len(candidate) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines

def text_lines(x, y, lines, line_height, attrs):
    return "".join(f'<text x="{x}" y="{y+i*line_height}" {attrs}>{esc(line)}</text>' for i,line in enumerate(lines))

def load_data():
    if DATA.exists():
        return json.loads(DATA.read_text(encoding="utf-8"))
    return {"profile": {}, "total_contributions": 0, "days": []}

def computed(data):
    bydate = {}
    for item in data.get("days", []):
        try:
            bydate[datetime.date.fromisoformat(item["date"])] = int(item.get("contributionCount", 0))
        except (ValueError, KeyError, TypeError):
            pass
    today = datetime.date.today()
    cursor = today if bydate.get(today, 0) else today - datetime.timedelta(days=1)
    streak = 0
    while bydate.get(cursor, 0) > 0:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    active = sum(v > 0 for v in bydate.values())
    busy_date, busy_count = max(bydate.items(), key=lambda kv: kv[1], default=(None, 0))
    monthly = {}
    for day, count in bydate.items():
        key = day.strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0) + count
    total = int(data.get("total_contributions", sum(bydate.values())))
    return bydate, active, streak, busy_date, busy_count, monthly, total

# 1. Hero — editorial typography, embedded portrait and cyan accent.
def hero(data):
    portrait = ""
    try:
        avatar_url = data.get("profile", {}).get("avatar_url")
        if avatar_url:
            raw, mime = fetch(avatar_url)
            mime = (mime or "image/png").split(";")[0]
            encoded = base64.b64encode(raw).decode()
            portrait = (f'<defs><clipPath id="avatar"><circle cx="710" cy="205" r="116"/></clipPath></defs>'
                        f'<image x="594" y="89" width="232" height="232" preserveAspectRatio="xMidYMid slice" '
                        f'href="data:{mime};base64,{encoded}" clip-path="url(#avatar)"/>'
                        f'<circle cx="710" cy="205" r="122" fill="none" stroke="{CYAN}" stroke-width="2"/>'
                        f'<circle cx="710" cy="205" r="135" fill="none" stroke="{CYAN}" opacity=".2"/>')
    except Exception as error:
        print("Avatar unavailable:", error)
    if not portrait:
        portrait = (f'<circle cx="710" cy="205" r="116" fill="{PANEL}" stroke="{CYAN}" stroke-width="2"/>'
                    f'<text x="710" y="225" text-anchor="middle" font-family="Instrument Serif,Georgia,serif" font-size="64" fill="{INK}">QB</text>')
    body = f'''
<rect width="{W}" height="432" rx="14" fill="{BG}" stroke="{RULE}"/>
<g class="f" {delay(0)}><rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{CYAN}"/>
<text x="68" y="57" class="mono" font-size="12" letter-spacing="1.2" fill="{MUTED}">PYTHON DEVELOPER · WEB DEVELOPER · IT STUDENT</text></g>
<text class="r serif" {delay(.15)} x="44" y="184" font-size="84" letter-spacing="-1.5" fill="{INK}">Qadir Bux</text>
<text class="r serif" {delay(.3)} x="44" y="277" font-size="84" font-style="italic" fill="{CYAN}">Shar</text>
<g class="r" {delay(.55)}>{text_lines(48,329,["I build web applications, explore AI,","and learn cybersecurity by building."],27,f'font-family="Geist,system-ui,sans-serif" font-size="18" fill="{SOFT}"')}</g>
<g class="f" {delay(.8)}><text x="48" y="396" class="mono" font-size="13" fill="{INK}">qadirbux.tech</text><text x="178" y="396" class="mono" font-size="13" fill="{CYAN}">↗</text></g>
{portrait}'''
    write("hero.svg", svg(W,432,body,["serif","sans","mono"],"Qadir Bux Shar. Python Developer, Web Developer and IT Student",bottom=12))

# 2. Three Worlds navigation tiles, with individual accents on the same dark canvas.
TILE_W, TILE_H = W/3-8, 210
def tile(name,label,color,on,num,word,blurb,delay_start,pos):
    lines = wrap(blurb,34)
    blurb_svg = "".join(f'<text class="r" style="animation-delay:{delay_start+.75+i*.1:.2f}s" x="24" y="{150+i*20}" font-family="Geist,system-ui,sans-serif" font-size="14" fill="{SOFT}">{esc(line)}</text>' for i,line in enumerate(lines))
    number = f'<text x="22" y="112" class="serif" font-size="47" fill="{on}">{esc(num)} <tspan font-style="italic" font-size="27">{esc(word)}</tspan></text>'
    body=f'''
<defs><clipPath id="tile"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
<linearGradient id="shine" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".25"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g class="ti" style="opacity:0;animation:rise .9s ease-out {delay_start:.2f}s both" clip-path="url(#tile)">
<rect width="{TILE_W}" height="{TILE_H}" rx="14" fill="{PANEL}" stroke="{color}" stroke-width="1.5"/>
<circle class="rg" style="animation-delay:{delay_start+.5:.2f}s" cx="{TILE_W-38}" cy="{TILE_H-35}" r="58" fill="none" stroke="{color}" stroke-width="2"/>
<rect class="sh" x="0" y="-20" width="90" height="{TILE_H+40}" fill="url(#shine)" style="animation-delay:{delay_start+1.2:.2f}s"/>
</g>
<text class="r mono" style="animation-delay:{delay_start+.2:.2f}s" x="24" y="39" font-size="12" letter-spacing="1.2" fill="{color}">{label}</text>
<text class="r n" style="animation-delay:{delay_start+.4:.2f}s" x="{TILE_W-42}" y="39" font-size="16" fill="{color}">↗</text>
<g class="r" style="animation-delay:{delay_start+.45:.2f}s">{number}</g>{blurb_svg}'''
    write(f"{name}.svg",svg(TILE_W,TILE_H,body,["serif","sans","mono"],f"{label}: {num} {word}. {blurb}",left=4*pos,right=8-4*pos,bottom=12))

# 3. Activity card with animated monthly bars and a compact stats column.
def activity(total,active,streak,busy_date,busy_count,monthly):
    months=sorted(monthly.items())[-12:]
    best=max([value for _,value in months[:-1]] or [value for _,value in months] or [1])
    x0,x1,base,maxh,gap=42,610,292,138,10
    bw=(x1-x0-gap*(len(months)-1))/max(1,len(months))
    bars=[]
    for i,(month,value) in enumerate(months):
        x=x0+i*(bw+gap); height=max(4,round(value/best*maxh))
        color=CYAN if value==best else (TEAL if i==len(months)-1 else "#29404D")
        label=datetime.date.fromisoformat(month+"-01").strftime("%b")
        bars.append(f'<rect class="g" style="animation-delay:{2.1+i*.07:.2f}s" x="{x:.1f}" y="{base-height}" width="{bw:.1f}" height="{height}" rx="4" fill="{color}"><title>{label}: {value:,}</title></rect>'
                    f'<text class="f" style="animation-delay:{2.1+i*.07:.2f}s" x="{x+bw/2:.1f}" y="{base+22}" text-anchor="middle" class="mono" font-size="11" fill="{MUTED}">{label}</text>')
    busy=busy_date.isoformat() if busy_date else "—"
    metrics=[(f"{streak} day" if streak==1 else f"{streak} days","CURRENT STREAK"),
             (str(active),"ACTIVE DAYS"),(f"{busy} · {busy_count}","BUSIEST DAY"),(f"{total:,}","TOTAL CONTRIBUTIONS")]
    side=[]
    for i,(value,label) in enumerate(metrics):
        y=103+i*59
        side.append(f'<g class="r" style="animation-delay:{2.5+i*.12:.2f}s"><text x="650" y="{y}" class="serif" font-size="34" fill="{CYAN}">{esc(value)}</text><text x="650" y="{y+21}" class="mono" font-size="11" letter-spacing=".3" fill="{MUTED}">{label}</text></g>')
        if i<3: side.append(f'<line x1="650" y1="{y+35}" x2="842" y2="{y+35}" stroke="{RULE}"/>')
    body=f'''<rect width="{W}" height="352" rx="14" fill="{BG}" stroke="{RULE}"/>
<text class="r serif" x="40" y="58" font-size="38" fill="{INK}">The last 12 months</text>
<text class="f" x="42" y="87" font-size="13" fill="{MUTED}">A snapshot of my GitHub activity</text>
{''.join(bars)}{''.join(side)}'''
    write("activity.svg",svg(W,352,body,["serif","sans","mono"],f"{total:,} contributions in the last year, {streak}-day streak",bottom=0))

# 4. Project cards: one third each, transparent canvas with baked row spacing.
REPO_W,REPO_H=W/3-8,176
PROJECTS=[
    ("WhatsX","Messaging and scheduling web application","Python · Web · Automation",CYAN,"https://github.com/litegenix/WhatsX"),
    ("Handwritten Digit Recognition","Digit classification with TensorFlow and OpenCV","Python · TensorFlow · OpenCV",TEAL,"https://github.com/litegenix/Handwritten-Digit-Recognition"),
    ("Pipeline Defect Detection","Computer-vision based surface inspection","Python · Computer Vision",VIOLET,"https://github.com/litegenix/Pipeline-Surface-Defect-Detection-System"),
]
def project_cards():
    for i,(name,description,stack,color,url) in enumerate(PROJECTS):
        lines=wrap(description,35)
        body=f'''<rect width="{REPO_W}" height="{REPO_H}" rx="14" fill="{PANEL}" stroke="{RULE}"/>
<g class="r" style="animation-delay:{3.8+i*.12:.2f}s"><rect x="24" y="27" width="8" height="8" rx="2" fill="{color}"/>
<text x="42" y="38" font-family="Geist,system-ui,sans-serif" font-size="17" font-weight="600" fill="{INK}">{esc(name)}</text>
{text_lines(24,72,lines,21,f'font-family="Geist,system-ui,sans-serif" font-size="13" fill="{SOFT}"')}
<text x="24" y="146" class="mono" font-size="10" fill="{MUTED}">{esc(stack.upper())}</text>
<text x="24" y="164" class="mono" font-size="10" fill="{color}">VIEW REPOSITORY ↗</text></g>'''
        write(f"repo-{i+1}.svg",svg(REPO_W,REPO_H,body,["sans","mono"],f"{name}: {description}",left=4*i,right=8-4*i,bottom=12))

def section_title():
    body=f'''<text class="r serif" style="animation-delay:3.5s" x="2" y="46" font-size="36" fill="{INK}">What I'm <tspan font-style="italic" fill="{CYAN}">building</tspan></text>'''
    write("title-coding-dark.svg",svg(W,64,body,["serif"],"What I'm building",bottom=0))
    body_light=body.replace(INK,"#111111").replace(CYAN,"#007E91")
    write("title-coding-light.svg",svg(W,64,body_light,["serif"],"What I'm building",bottom=0))

# 5. Animated contribution heatmap; actual calendar days and count-based colours.
def heatmap(bydate,total):
    dates=sorted(bydate)
    if not dates: return
    first=dates[0]; lead=(first.weekday()+1)%7
    cell,step,gx,gy=12,15,42,102
    cells=[]; months=[]; seen=set()
    for index,day in enumerate(dates):
        k=index+lead; col,row=divmod(k,7); count=bydate[day]
        if day.day<=7 and (day.year,day.month) not in seen and row==0:
            seen.add((day.year,day.month))
            months.append(f'<text x="{gx+col*step}" y="90" class="mono" font-size="10" fill="{MUTED}">{day.strftime("%b")}</text>')
        level=0 if count==0 else 1 if count<=2 else 2 if count<=5 else 3 if count<=9 else 4
        cells.append(f'<rect class="p" style="animation-delay:{1+col*.025:.2f}s" x="{gx+col*step}" y="{gy+row*step}" width="{cell}" height="{cell}" rx="3" fill="{BLUE[level]}"><title>{day.isoformat()}: {count} contributions</title></rect>')
    ncols=(len(dates)+lead+6)//7; right=gx+ncols*step-2
    lx=right-len(BLUE)*15
    legend="".join(f'<rect x="{lx+i*15}" y="222" width="11" height="11" rx="2" fill="{c}"/>' for i,c in enumerate(BLUE))
    body=f'''<rect width="{W}" height="260" rx="14" fill="{BG}" stroke="{RULE}"/>
<text class="r serif" x="42" y="55" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{CYAN}">in code</tspan></text>
<text class="f mono" x="42" y="77" font-size="10" letter-spacing=".8" fill="{MUTED}">{total:,} CONTRIBUTIONS · REFRESHED DAILY</text>
{''.join(months)}{''.join(cells)}
<text x="{lx-13}" y="232" text-anchor="end" class="mono" font-size="10" fill="{MUTED}">LESS</text>{legend}<text x="{right+4}" y="232" class="mono" font-size="10" fill="{MUTED}">MORE</text>'''
    write("heatmap.svg",svg(W,260,body,["serif","mono"],f"Contribution graph: {total:,} contributions in the last year",bottom=0))

def main():
    data=load_data(); bydate,active,streak,busy,busy_count,monthly,total=computed(data)
    hero(data)
    heatmap(bydate,total)
    activity(total,active,streak,busy,busy_count,monthly)
    # Three Worlds cards use three distinct LiteGenix accent colours.
    tile("build","BUILD",CYAN,"#F1F7FA","Projects","& experiments","Building websites, automation tools and practical software.",3.0,0)
    tile("brand","BRAND",TEAL,"#F1F7FA","Digital","products","Developing ideas, useful tools and independent projects.",3.25,1)
    tile("learn","LEARN",VIOLET,"#F1F7FA","IT","& security","Learning AI, cybersecurity and software engineering.",3.5,2)
    section_title()
    project_cards()
    print("All reference-layout profile SVG cards rendered.")

if __name__=="__main__":
    main()
