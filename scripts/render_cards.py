#!/usr/bin/env python3
"""Generate dark, animated profile cards for the litegenix GitHub profile."""
import base64, calendar, datetime, html, json, os, pathlib, subprocess, urllib.request
import cairosvg

ROOT = pathlib.Path(__file__).resolve().parents[1]
CARDS = ROOT / "cards"
DATA = ROOT / "data" / "contributions.json"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif/InstrumentSerif-Regular.ttf"
FONT_FILE = ROOT / "fonts" / "serif-400.woff"
ACCENT = "#00E5FF"
BG = "#080D12"
PANEL = "#0E1720"
MUTED = "#8B9AA8"
WHITE = "#F4FAFF"
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,·|—-:/@+()'!?&"

def esc(value):
    return html.escape(str(value), quote=True)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "litegenix-profile-card-builder"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read(), response.headers.get("Content-Type", "")

def font_css():
    try:
        FONT_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not FONT_FILE.exists():
            source = ROOT / "fonts" / "InstrumentSerif-Regular.ttf"
            raw, _ = fetch(FONT_URL)
            source.write_bytes(raw)
            subprocess.run(["pyftsubset", str(source), "--output-file=" + str(FONT_FILE),
                            "--flavor=woff", "--text=" + CHARS, "--layout-features=*"],
                           check=True, capture_output=True)
            source.unlink(missing_ok=True)
        encoded = base64.b64encode(FONT_FILE.read_bytes()).decode()
        return f"@font-face{{font-family:'Instrument Serif';src:url(data:font/woff;base64,{encoded}) format('woff');font-weight:400}}"
    except Exception as exc:
        print("Font embedding fallback:", exc)
        return ""

FONT = font_css()

def style(delay=0):
    return f"""<style>
@keyframes rise{{from{{opacity:0;transform:translateY(18px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes pulse{{0%,100%{{opacity:.55}}50%{{opacity:1}}}}
@keyframes glow{{0%,100%{{opacity:.45}}50%{{opacity:1}}}}
.card{{animation:rise .8s cubic-bezier(.2,.7,.2,1) {delay}s both}}
.live{{animation:pulse 2.5s ease-in-out infinite}}
.glow{{animation:glow 3s ease-in-out infinite}}
{FONT}
text{{font-family:'Instrument Serif',Georgia,serif}}
@media(prefers-reduced-motion:reduce){{.card,.live,.glow{{animation:none!important}}}}
</style>"""

def svg(width, height, body, delay=0):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">{style(delay)}'
            f'<rect width="{width}" height="{height}" rx="20" fill="{BG}" stroke="#1B2A36"/>'
            f'<g class="card">{body}</g></svg>')

def save(filename, content):
    (CARDS / filename).write_text(content, encoding="utf-8")

def save_png(filename, content, width=1200):
    # PNG fallbacks avoid SVG rendering failures in GitHub mobile clients.
    cairosvg.svg2png(bytestring=content.encode("utf-8"),
                     write_to=str(CARDS / filename), output_width=width)

def load_data():
    if DATA.exists():
        return json.loads(DATA.read_text(encoding="utf-8"))
    return {"profile": {"name": "Qadir Bux", "avatar_url": "https://github.com/litegenix.png?size=256"},
            "total_contributions": 0, "days": []}

def avatar_data(data):
    try:
        url = data.get("profile", {}).get("avatar_url") or "https://github.com/litegenix.png?size=256"
        raw, mime = fetch(url)
        mime = mime.split(";")[0] if mime else "image/png"
        return f"data:{mime};base64," + base64.b64encode(raw).decode()
    except Exception:
        return ""

def stats(data):
    days = data.get("days", [])
    by_date = {}
    for item in days:
        try:
            by_date[datetime.date.fromisoformat(item["date"])] = int(item.get("contributionCount", 0))
        except Exception:
            pass
    active = sum(count > 0 for count in by_date.values())
    busiest_date, busiest_count = max(by_date.items(), key=lambda pair: pair[1], default=(None, 0))
    today = datetime.date.today()
    cursor = today if by_date.get(today, 0) else today - datetime.timedelta(days=1)
    streak = 0
    while by_date.get(cursor, 0) > 0:
        streak += 1
        cursor -= datetime.timedelta(days=1)
    monthly = {}
    for day, count in by_date.items():
        key = day.strftime("%b")
        month_key = day.strftime("%Y-%m")
        monthly[month_key] = monthly.get(month_key, 0) + count
    total = int(data.get("total_contributions", sum(by_date.values())))
    return by_date, active, busiest_date, busiest_count, streak, monthly, total

def main():
    CARDS.mkdir(exist_ok=True)
    data = load_data()
    by_date, active, busiest_date, busiest_count, streak, monthly, total = stats(data)
    avatar = avatar_data(data)
    # Wide hero: editorial serif typography, cyan detail, and profile portrait.
    portrait = (f'<defs><clipPath id="portrait"><circle cx="735" cy="150" r="91"/></clipPath></defs>'
                f'<image x="644" y="59" width="182" height="182" preserveAspectRatio="xMidYMid slice" '
                f'xlink:href="{avatar}" clip-path="url(#portrait)"/>'
                f'<circle cx="735" cy="150" r="96" fill="none" stroke="{ACCENT}" stroke-width="2" opacity=".8"/>'
                f'<circle cx="735" cy="150" r="105" fill="none" stroke="{ACCENT}" stroke-width="1" opacity=".18"/>'
                if avatar else f'<circle cx="735" cy="150" r="91" fill="{PANEL}" stroke="{ACCENT}"/><text x="735" y="165" fill="{WHITE}" text-anchor="middle" font-size="48">QB</text>')
    hero = (f'<text x="54" y="62" fill="{ACCENT}" font-size="13" letter-spacing="4">HELLO, I&#39;M QADIR</text>'
            f'<text x="50" y="137" fill="{WHITE}" font-size="66">Qadir Bux Shar</text>'
            f'<text x="55" y="180" fill="#C4D0D9" font-size="20">Python Developer  ·  Web Developer</text>'
            f'<text x="55" y="211" fill="#C4D0D9" font-size="20">Cybersecurity Enthusiast  ·  IT Student</text>'
            f'<path d="M55 244H440" stroke="{ACCENT}" opacity=".55"/>'
            f'<text x="55" y="274" fill="{MUTED}" font-size="13" letter-spacing="2">BUILDING SOFTWARE, EXPLORING AI &amp; SECURITY</text>'
            f'<circle cx="920" cy="38" r="4" fill="{ACCENT}" class="live"/>{portrait}')
    save("hero.svg", svg(1000, 320, hero, 0))

    # Contribution heatmap with month labels and GitHub-like intensity levels.
    dates = sorted(by_date)
    heat = '<text x="34" y="37" fill="' + WHITE + '" font-size="25">Contribution activity</text>'
    heat += f'<text x="34" y="61" fill="{MUTED}" font-size="12">{total:,} contributions in the last year</text>'
    if dates:
        start = dates[0] - datetime.timedelta(days=dates[0].weekday())
        colors = ["#14212B", "#06434D", "#087A89", "#00A9BA", ACCENT]
        last_month = None
        for day in dates:
            col = (day - start).days // 7
            row = day.weekday()
            count = by_date[day]
            level = 0 if count == 0 else 1 if count <= 2 else 2 if count <= 5 else 3 if count <= 9 else 4
            x, y = 34 + col * 17, 88 + row * 19
            heat += f'<rect x="{x}" y="{y}" width="12" height="12" rx="3" fill="{colors[level]}"><title>{day.isoformat()}: {count} contributions</title></rect>'
            if day.day <= 7 and day.strftime("%b") != last_month:
                heat += f'<text x="{x}" y="80" fill="{MUTED}" font-size="10">{day.strftime("%b")}</text>'
                last_month = day.strftime("%b")
    heat += f'<text x="34" y="237" fill="{MUTED}" font-size="11">Less</text>'
    for i, color in enumerate(["#14212B", "#06434D", "#087A89", "#00A9BA", ACCENT]):
        heat += f'<rect x="{70+i*18}" y="227" width="12" height="12" rx="3" fill="{color}"/>'
    heat += f'<text x="166" y="237" fill="{MUTED}" font-size="11">More</text>'
    heatmap_svg = svg(1000, 260, heat, .25)
    save("heatmap.svg", heatmap_svg)
    save_png("heatmap.png", heatmap_svg)
    # Retain legacy filename so existing external references continue to work.
    save("contributions.svg", heatmap_svg)

    # Activity metrics and monthly bars.
    recent = sorted(monthly.items())[-12:]
    max_month = max([value for _, value in recent] or [1])
    bars = ""
    for index, (month, value) in enumerate(recent):
        x = 42 + index * 77
        bar_height = 76 * value / max_month if max_month else 0
        bars += (f'<rect x="{x}" y="{180-bar_height:.1f}" width="42" height="{bar_height:.1f}" rx="5" '
                 f'fill="{ACCENT}" opacity=".85"><title>{month}: {value}</title></rect>'
                 f'<text x="{x+21}" y="201" fill="{MUTED}" text-anchor="middle" font-size="10">{month[5:]}</text>')
    busy = busiest_date.isoformat() if busiest_date else "—"
    activity = (f'<text x="35" y="39" fill="{WHITE}" font-size="26">The last 12 months</text>'
                f'<text x="35" y="62" fill="{MUTED}" font-size="12">A snapshot of my GitHub activity</text>')
    metrics = [("TOTAL CONTRIBUTIONS", f"{total:,}"), ("ACTIVE DAYS", str(active)),
               ("CURRENT STREAK", f"{streak} days"), ("BUSIEST DAY", busy)]
    for i, (label, value) in enumerate(metrics):
        x = 35 + i * 240
        activity += (f'<rect x="{x}" y="82" width="220" height="66" rx="12" fill="{PANEL}" stroke="#20323F"/>'
                     f'<text x="{x+14}" y="106" fill="{MUTED}" font-size="10" letter-spacing="1">{label}</text>'
                     f'<text x="{x+14}" y="133" fill="{ACCENT}" font-size="25">{esc(value)}</text>')
    activity += f'<text x="35" y="174" fill="{MUTED}" font-size="11" letter-spacing="1">MONTHLY CONTRIBUTIONS</text>{bars}'
    save("activity.svg", svg(1000, 220, activity, .45))

    # Three navigation cards, matching the reference layout but in the user's dark/cyan identity.
    nav = [("build.svg", "BUILD", "Projects & experiments", "01"),
           ("brand.svg", "BRANDS", "Products & ideas", "02"),
           ("learn.svg", "LEARN", "Notes & articles", "03")]
    for index, (filename, title, subtitle, number) in enumerate(nav):
        x = 20
        color = ACCENT if index == 0 else ("#54D6C8" if index == 1 else "#9AABFF")
        body = (f'<rect x="1" y="1" width="291" height="150" rx="17" fill="{PANEL}" stroke="{color}" stroke-opacity=".45"/>'
                f'<text x="22" y="35" fill="{color}" font-size="11" letter-spacing="2">{number} / QADIR BUX</text>'
                f'<text x="22" y="88" fill="{WHITE}" font-size="36">{esc(title)}</text>'
                f'<text x="22" y="117" fill="{MUTED}" font-size="12">{esc(subtitle)}</text>'
                f'<path d="M248 112l18 0m-7 -7l7 7 -7 7" stroke="{color}" stroke-width="2" fill="none"/>')
        nav_svg = svg(293, 153, body, .65 + index * .12)
        save(filename, nav_svg)
        save_png(filename.replace(".svg", ".png"), nav_svg, width=586)

    # Section divider and three project cards.
    title_svg = svg(1000, 82,
        f'<text x="34" y="50" fill="{ACCENT}" font-size="12" letter-spacing="3">SELECTED WORK</text>'
        f'<text x="250" y="53" fill="{WHITE}" font-size="34">What I&#39;m building</text>'
        f'<path d="M650 43H965" stroke="#263946"/>', .8)
    save("title-coding-dark.svg", title_svg)
    save_png("title-coding.png", title_svg)
    projects = [
        ("repo-whatsx.svg", "WhatsX", "Messaging and scheduling web application", "PYTHON  ·  WEB  ·  AUTOMATION"),
        ("repo-handwritten-digits.svg", "Handwritten Digit Recognition", "Digit classification with TensorFlow and OpenCV", "PYTHON  ·  TENSORFLOW  ·  OPENCV"),
        ("repo-pipeline-defects.svg", "Pipeline Defect Detection", "Computer-vision based surface inspection", "PYTHON  ·  COMPUTER VISION"),
    ]
    for index, (filename, title, description, stack) in enumerate(projects):
        color = [ACCENT, "#54D6C8", "#9AABFF"][index]
        body = (f'<rect x="1" y="1" width="318" height="185" rx="16" fill="{PANEL}" stroke="#263946"/>'
                f'<rect x="20" y="22" width="36" height="4" rx="2" fill="{color}"/>'
                f'<text x="20" y="65" fill="{WHITE}" font-size="22">{esc(title)}</text>'
                f'<text x="20" y="94" fill="{MUTED}" font-size="12">{esc(description)}</text>'
                f'<text x="20" y="133" fill="{color}" font-size="10">{esc(stack)}</text>'
                f'<text x="20" y="164" fill="{WHITE}" font-size="11">EXPLORE REPOSITORY  ↗</text>')
        project_svg = svg(320, 188, body, 1.0 + index * .12)
        save(filename, project_svg)
        save_png(filename.replace(".svg", ".png"), project_svg, width=640)

    # Local PNG social icons: avoid external SVG/CDN image failures in GitHub mobile.
    icon_svgs = {
        "icon-portfolio.png": f'<circle cx="32" cy="32" r="25" fill="none" stroke="{ACCENT}" stroke-width="4"/><ellipse cx="32" cy="32" rx="11" ry="25" fill="none" stroke="{ACCENT}" stroke-width="3"/><path d="M8 32h48M13 20h38M13 44h38" stroke="{ACCENT}" stroke-width="3" fill="none"/>',
        "icon-linkedin.png": '<rect x="5" y="5" width="54" height="54" rx="8" fill="#0A66C2"/><text x="32" y="44" text-anchor="middle" font-family="Arial,sans-serif" font-size="36" font-weight="bold" fill="#FFFFFF">in</text>',
        "icon-github.png": '<path fill="#F4FAFF" d="M32 5C17 5 5 17 5 32c0 12 8 22 19 25 1 0 2-1 2-2v-5c-8 2-10-3-10-3-1-3-3-4-3-4-2-1 0-1 0-1 3 0 4 3 4 3 2 3 5 2 7 1 0-2 1-3 2-4-7-1-13-4-13-13 0-3 1-6 3-8 0-1-1-4 1-8 0 0 3-1 9 3 5-1 10-1 15 0 6-4 9-3 9-3 2 4 1 7 1 8 2 2 3 5 3 8 0 9-6 12-13 13 2 2 2 4 2 7v6c0 1 1 2 2 2 11-3 19-13 19-25C59 17 47 5 32 5z"/>',
        "icon-email.png": f'<rect x="5" y="11" width="54" height="42" rx="6" fill="none" stroke="{ACCENT}" stroke-width="4"/><path d="M8 16l24 19 24-19" fill="none" stroke="{ACCENT}" stroke-width="4" stroke-linejoin="round"/>'
    }
    for filename, drawing in icon_svgs.items():
        icon_svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{drawing}</svg>'
        save_png(filename, icon_svg, width=128)

    print("Rendered dark animated profile cards:", CARDS)

if __name__ == "__main__":
    main()
