#!/usr/bin/env python3
"""Render animated, GitHub-README-safe SVG profile cards from data/contributions.json."""
import base64, json, os, pathlib, subprocess, urllib.request, html, datetime, calendar

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
STATIC = os.getenv("STATIC", "0") == "1"
ACCENT = "#00eeff"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf"
FONT_FILE = ROOT / "fonts" / "serif-400.woff"
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,·|—-:/@+()'!?&"

def esc(s): return html.escape(str(s), quote=True)
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"litegenix-profile-card-builder"})
    with urllib.request.urlopen(req, timeout=30) as r: return r.read()

def font_css():
    try:
        FONT_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not FONT_FILE.exists():
            source = ROOT / "fonts" / "InstrumentSerif-Regular.ttf"
            source.write_bytes(fetch(FONT_URL))
            subprocess.run([
                "pyftsubset", str(source), "--output-file=" + str(FONT_FILE),
                "--flavor=woff", "--text=" + CHARS, "--layout-features=*"
            ], check=True, capture_output=True)
            source.unlink(missing_ok=True)
        b64 = base64.b64encode(open(FONT_FILE, "rb").read()).decode()
        return f"@font-face{{font-family:'Instrument Serif';src:url(data:font/woff;base64,{b64}) format('woff');font-weight:400}}"
    except Exception as exc:
        print(f"Instrument Serif embedding failed; using serif fallback: {exc}")
        return "text{font-family:Georgia,serif}"

def load():
    if DATA.exists(): return json.loads(DATA.read_text(encoding="utf-8"))
    return {"profile":{"name":"Qadir Bux","avatar_url":"https://github.com/litegenix.png?size=256"},
            "total_contributions":0,"days":[],"weeks":[]}

def avatar_data(data):
    try:
        url=data.get("profile",{}).get("avatar_url") or "https://github.com/litegenix.png?size=256"
        raw=fetch(url)
        return "data:image/png;base64,"+base64.b64encode(raw).decode()
    except Exception: return ""

FONT_CSS = font_css()

def style(delay=0):
    if STATIC: return ""
    return f"""<style>
@keyframes rise{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
.card{{animation:rise .75s ease-out {delay}s both}}
.pulse{{animation:pulse 2.8s ease-in-out infinite}}
@media(prefers-reduced-motion:reduce){{.card,.pulse{{animation:none!important}}animate,animateTransform{{display:none!important}}}}
{FONT_CSS}
</style>"""

def svg(w,h,body,delay=0):
    return f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{style(delay)}<rect width="{w}" height="{h}" rx="18" fill="#0a0a0a" stroke="#333"/><g class="card">{body}</g></svg>'

def save(name, content): (CARDS/name).write_text(content,encoding="utf-8")

def calc(data):
    days=data.get("days",[])
    counts=[int(x.get("contributionCount",0)) for x in days]
    active=sum(x>0 for x in counts)
    busiest=max(days,key=lambda x:int(x.get("contributionCount",0)),default={})
    today=datetime.date.today()
    bydate={}
    for x in days:
        try: bydate[datetime.date.fromisoformat(x["date"])]=int(x.get("contributionCount",0))
        except Exception: pass
    cursor=today if bydate.get(today,0)>0 else today-datetime.timedelta(days=1)
    streak=0
    while bydate.get(cursor,0)>0:
        streak+=1; cursor-=datetime.timedelta(days=1)
    monthly={}
    for d,n in bydate.items(): monthly[d.strftime("%Y-%m")]=monthly.get(d.strftime("%Y-%m"),0)+n
    return days,active,busiest,streak,monthly

def main():
    CARDS.mkdir(exist_ok=True)
    data=load(); days,active,busiest,streak,monthly=calc(data)
    total=int(data.get("total_contributions",sum(int(x.get("contributionCount",0)) for x in days)))
    avatar=avatar_data(data)
    # Hero with the current GitHub profile avatar embedded in the SVG.
    pic=(f'<defs><clipPath id="avatarClip"><circle cx="860" cy="112" r="66"/></clipPath></defs><image x="794" y="46" width="132" height="132" preserveAspectRatio="xMidYMid slice" xlink:href="{avatar}" clip-path="url(#avatarClip)"/><circle cx="860" cy="112" r="69" fill="none" stroke="{ACCENT}" stroke-width="3"/>' if avatar else f'<circle cx="860" cy="112" r="66" fill="#063b3f"/><text x="860" y="125" fill="#fff" text-anchor="middle" font-size="38">QB</text>')
    save("hero.svg",svg(1000,230,f'<text x="52" y="85" fill="#8b949e" font-size="17" letter-spacing="4">HELLO, I'M</text><text x="50" y="145" fill="#fff" font-size="48" font-weight="700">Qadir Bux</text><text x="53" y="184" fill="{ACCENT}" font-size="20">Python Developer · Web Developer · Cybersecurity Enthusiast</text>{pic}',0))
    tiles=[("build.svg","BUILD","qadirbux.tech/projects","⌘","#00eeff"),("brand.svg","BRANDS","qadirbux.tech/brands","✦","#00ff66"),("learn.svg","LEARN","qadirbux.tech/blog","↗","#ff00aa")]
    for i,(fn,label,sub,icon,color) in enumerate(tiles):
        save(fn,svg(320,112,f'<rect x="1" y="1" width="318" height="110" rx="16" fill="#101010" stroke="{color}" stroke-opacity=".65"/><text x="24" y="48" fill="{color}" font-size="25" font-weight="700">{icon}</text><text x="70" y="42" fill="#fff" font-size="17" font-weight="700">{label}</text><text x="70" y="68" fill="#8b949e" font-size="11">{sub}</text><path d="M278 55h18m-7-7 7 7-7 7" stroke="{color}" stroke-width="2" fill="none"/>',.2+i*.15))
    bdate=busiest.get("date","—")
    bcount=int(busiest.get("contributionCount",0))
    recent=sorted(monthly.items())[-12:]
    maxm=max([n for _,n in recent] or [1])
    bars=""
    for i,(month,n) in enumerate(recent):
        x=38+i*77; bh=72*n/maxm if maxm else 0
        bars+=f'<rect x="{x}" y="{166-bh:.1f}" width="42" height="{bh:.1f}" rx="5" fill="{ACCENT}" opacity=".85"/><text x="{x+21}" y="188" fill="#8b949e" text-anchor="middle" font-size="10">{esc(month[5:])}</text>'
    activity=f'<text x="35" y="40" fill="#fff" font-size="23" font-weight="700">GitHub Activity</text><text x="35" y="64" fill="#8b949e" font-size="12">{total:,} contributions in the last year · updated daily</text>'
    metrics=[("CURRENT STREAK",f"{streak} days",ACCENT),("ACTIVE DAYS",str(active), "#00ff66"),("BUSIEST DAY",f"{bdate} · {bcount}", "#ff00aa"),("TOTAL CONTRIBUTIONS",f"{total:,}","#fff")]
    for i,(label,value,color) in enumerate(metrics):
        x=35+i*240
        activity+=f'<rect x="{x}" y="83" width="220" height="78" rx="11" fill="#101010" stroke="#333"/><text x="{x+15}" y="108" fill="#8b949e" font-size="11">{label}</text><text x="{x+15}" y="143" fill="{color}" font-size="{19 if len(value)>15 else 27}" font-weight="700">{esc(value)}</text>'
    activity+=f'<text x="35" y="207" fill="#8b949e" font-size="11">MONTHLY CONTRIBUTIONS (last 12 months)</text>{bars}'
    save("activity.svg",svg(1000,230,activity,.65))
    repos=[
      ("repo-whatsx.svg","WhatsX Web Application","Messaging and scheduling web application","Python · Web · Automation","https://github.com/litegenix/WhatsX"),
      ("repo-handwritten-digits.svg","Handwritten Digit Recognition","Digit classification with TensorFlow and OpenCV","Python · TensorFlow · OpenCV","https://github.com/litegenix/Handwritten-Digit-Recognition"),
      ("repo-pipeline-defects.svg","Pipeline Surface Defect Detection","Computer-vision based surface defect detection","Python · Computer Vision","https://github.com/litegenix/Pipeline-Surface-Defect-Detection-System"),
      ("repo-portfolio.svg","Portfolio Website","Responsive personal portfolio website","HTML · CSS · JavaScript","https://github.com/litegenix/portfolio")]
    for i,(fn,title,desc,tech,url) in enumerate(repos):
        save(fn,svg(1000,145,f'<rect x="1" y="1" width="998" height="143" rx="16" fill="#101010" stroke="#333"/><rect x="24" y="25" width="5" height="94" rx="3" fill="{ACCENT}"/><text x="52" y="55" fill="#fff" font-size="22" font-weight="700">{esc(title)}</text><text x="52" y="83" fill="#8b949e" font-size="15">{esc(desc)}</text><text x="52" y="111" fill="{ACCENT}" font-size="13">{esc(tech)}</text><text x="945" y="78" text-anchor="end" fill="#8b949e" font-size="13">VIEW REPO ↗</text>',1+i*.15))
    # Render the real contribution days, oldest to newest, into 53 x 7 calendar cells.
    weekmap={}
    for d in days:
        try:
            dt=datetime.date.fromisoformat(d["date"]); week=(dt-datetime.timedelta(days=dt.weekday())).isocalendar().week
            key=(dt.year,week); weekmap[(key,dt.weekday())]=int(d.get("contributionCount",0))
        except Exception: pass
    maxc=max(weekmap.values() or [1]); graph=""
    dates=sorted([datetime.date.fromisoformat(d["date"]) for d in days if d.get("date")])
    if dates:
        start=dates[0]-datetime.timedelta(days=dates[0].weekday())
        for d,n in ((datetime.date.fromisoformat(x["date"]),int(x.get("contributionCount",0))) for x in days if x.get("date")):
            col=(d-start).days//7; row=d.weekday()
            level=0 if n==0 else 1 if n<=max(1,maxc*.25) else 2 if n<=max(1,maxc*.5) else 3 if n<=max(1,maxc*.75) else 4
            colors=["#161b22","#063b3f","#087b80","#00a8b2",ACCENT]
            graph+=f'<rect x="{35+col*17}" y="{55+row*18}" width="12" height="12" rx="3" fill="{colors[level]}"><title>{d.isoformat()}: {n} contributions</title></rect>'
    save("contributions.svg",svg(1000,220,f'<text x="35" y="32" fill="#fff" font-size="22" font-weight="700">Contribution Graph</text><text x="35" y="46" fill="#8b949e" font-size="10">Last 12 months · {total:,} contributions · brand colour {ACCENT}</text>{graph}<text x="35" y="207" fill="#8b949e" font-size="11">Less</text><rect x="70" y="197" width="12" height="12" rx="3" fill="#161b22"/><rect x="89" y="197" width="12" height="12" rx="3" fill="#063b3f"/><rect x="108" y="197" width="12" height="12" rx="3" fill="#087b80"/><rect x="127" y="197" width="12" height="12" rx="3" fill="#00a8b2"/><rect x="146" y="197" width="12" height="12" rx="3" fill="{ACCENT}"/><text x="168" y="207" fill="#8b949e" font-size="11">More</text>',1.8))
    print("Rendered SVG cards in",CARDS)

if __name__=="__main__": main()
