#!/usr/bin/env python3
"""Rebuild the profile SVGs in ./assets from live GitHub data.

  GH_TOKEN=... python scripts/generate.py     # live data (what the Action runs)
  python scripts/generate.py --sample         # offline preview from sample-data.json
"""
import json
import math
import os
import sys
import textwrap
import urllib.request
from datetime import datetime, timezone
from xml.sax.saxutils import escape as _esc

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")

LANG_COLORS = ["#4f9a9e", "#D9D9D9", "#6f9bb9", "#FFFFFF"]  # top-4 languages, in order
OTHER = "#8f8f8f"
NO_LANG = "#6f9bb9"
ACCENT = "#8fc9cb"


def esc(s):
    return _esc(str(s), {'"': "&quot;"})


def clip(s, n):
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def pct_label(p):
    return "<1%" if p < 1 else f"{round(p)}%"


def ago(days):
    if days < 1:
        return "today"
    if days < 30:
        return f"{int(days)}d ago"
    if days < 365:
        return f"{int(days // 30)}mo ago"
    return f"{int(days // 365)}y ago"


# --------------------------------------------------------------------------- data

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    login
    followers { totalCount }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        description
        stargazerCount
        pushedAt
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""


def load_live(login):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Set GH_TOKEN (or GITHUB_TOKEN) to query the GitHub API.")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": login}}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-card-generator",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    user = (payload.get("data") or {}).get("user")
    if not user:
        sys.exit(f"GitHub API returned no user: {payload.get('errors')}")

    cal = user["contributionsCollection"]["contributionCalendar"]
    best = run = 0
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            run = run + 1 if day["contributionCount"] > 0 else 0
            best = max(best, run)

    now = datetime.now(timezone.utc)
    repos = []
    for r in user["repositories"]["nodes"]:
        pushed = r.get("pushedAt")
        days = (now - datetime.fromisoformat(pushed.replace("Z", "+00:00"))).days if pushed else 0
        langs = {e["node"]["name"]: e["size"] for e in r["languages"]["edges"]}
        repos.append({
            "name": r["name"],
            "description": r["description"],
            "stars": r["stargazerCount"],
            "days_ago": days,
            "langs": langs,
        })
    return {
        "login": user["login"],
        "name": user["name"] or user["login"],
        "followers": user["followers"]["totalCount"],
        "repo_count": user["repositories"]["totalCount"],
        "contributions": cal["totalContributions"],
        "streak": best,
        "repos": repos,
    }


# ------------------------------------------------------------------------ templates

HERO = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="150" viewBox="0 0 800 150" role="img" aria-label="__ALT__">
  <defs>
    <radialGradient id="halo" cx="82%" cy="35%" r="45%">
      <stop offset="0" stop-color="#3C6E71" stop-opacity=".6"/>
      <stop offset="1" stop-color="#3C6E71" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    .mono{font-family:'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace}
    .disp{font-family:'Space Grotesk','Avenir Next','Segoe UI',Helvetica,Arial,sans-serif}
    .tw{animation:tw 4s ease-in-out infinite}
    .tw2{animation:tw 5.5s ease-in-out infinite;animation-delay:1.3s}
    @keyframes tw{0%,100%{opacity:.4}50%{opacity:1}}
  </style>
  <path d="M1,1 H781 L799,19 V149 H19 L1,131 Z" fill="none"/>
  <path d="M1,1 H781 L799,19 V149 H19 L1,131 Z" fill="none" stroke="#D9D9D9" stroke-opacity=".35"/>
  <text x="36" y="38" class="mono" font-size="9" letter-spacing="3" fill="#8fc9cb">PROFILE · 001 · FRONTEND / FULL-STACK</text>
  <text x="36" y="84" class="disp" font-size="__FS__" font-weight="700" letter-spacing="__LS__" fill="#FFFFFF">__NAME__</text>
  <rect x="36" y="102" width="26" height="2" fill="#3C6E71"/>
  <text x="72" y="107" class="disp" font-size="14" fill="#D9D9D9">__TAGLINE__</text>
  <line x1="36" y1="130" x2="764" y2="130" stroke="#D9D9D9" stroke-opacity=".35" stroke-width="7" stroke-dasharray="1 9"/>
  <line x1="36" y1="130" x2="764" y2="130" stroke="#D9D9D9" stroke-opacity=".7" stroke-width="12" stroke-dasharray="1.5 48.5"/>
  <polyline points="615,46 662,66 702,42 738,80 684,98 662,66" fill="none" stroke="#D9D9D9" stroke-opacity=".4" stroke-dasharray="3 3"/>
  <g fill="#FFFFFF">
    <circle class="tw" cx="615" cy="46" r="2.4"/>
    <circle class="tw2" cx="702" cy="42" r="2.2"/>
    <circle class="tw" cx="738" cy="80" r="2.6"/>
    <circle class="tw2" cx="684" cy="98" r="2"/>
  </g>
  <circle cx="662" cy="66" r="4" fill="#8fc9cb"/>
  <circle cx="662" cy="66" r="9" fill="none" stroke="#8fc9cb" stroke-opacity=".5"/>
</svg>
"""

STATS = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="88" viewBox="0 0 800 88" role="img" aria-label="__ALT__">
  <defs>
  </defs>
  <style>
    .mono{font-family:'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace}
    .disp{font-family:'Space Grotesk','Avenir Next','Segoe UI',Helvetica,Arial,sans-serif}
  </style>
  <path d="M1,1 H781 L799,19 V87 H19 L1,69 Z" fill="none" stroke="#D9D9D9" stroke-opacity=".35"/>
  <g stroke="#D9D9D9" stroke-opacity=".18">
    <line x1="172" y1="22" x2="172" y2="66"/><line x1="324" y1="22" x2="324" y2="66"/>
    <line x1="476" y1="22" x2="476" y2="66"/><line x1="628" y1="22" x2="628" y2="66"/>
  </g>
  <g class="disp" font-size="28" font-weight="700" fill="#FFFFFF" text-anchor="middle">
    <text x="96" y="47">__REPOS__</text><text x="248" y="47">__STARS__</text><text x="400" y="47">__CONTRIB__</text><text x="552" y="47">__STREAK__</text><text x="704" y="47">__FOLLOWERS__</text>
  </g>
  <g class="mono" font-size="8" letter-spacing="2" fill="#8fc9cb" text-anchor="middle">
    <text x="96" y="67">REPOSITORIES</text><text x="248" y="67">STARS</text><text x="400" y="67">CONTRIBUTIONS · 1Y</text><text x="552" y="67">LONGEST STREAK</text><text x="704" y="67">FOLLOWERS</text>
  </g>
</svg>
"""

GALAXY = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="320" viewBox="0 0 800 320" role="img" aria-label="Repo galaxy for __LOGIN__">
  <defs>
    <radialGradient id="core" cx="50%" cy="50%" r="50%">
      <stop offset="0" stop-color="#8fc9cb" stop-opacity=".7"/>
      <stop offset=".4" stop-color="#3C6E71" stop-opacity=".35"/>
      <stop offset="1" stop-color="#3C6E71" stop-opacity="0"/>
    </radialGradient>
    <path id="arm" fill="none" vector-effect="non-scaling-stroke"
      d="M0,0 a12,12 0 0 1 12,-12 a20,20 0 0 1 20,20 a28,28 0 0 1 -28,28 a36,36 0 0 1 -36,-36 a44,44 0 0 1 44,-44 a52,52 0 0 1 52,52 a60,60 0 0 1 -60,60 a68,68 0 0 1 -68,-68 a76,76 0 0 1 76,-76 a84,84 0 0 1 84,84 a92,92 0 0 1 -92,92 a100,100 0 0 1 -100,-100"/>
  </defs>
  <style>
    .mono{font-family:'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace}
    .disp{font-family:'Space Grotesk','Avenir Next','Segoe UI',Helvetica,Arial,sans-serif}
    .spin{animation:spin 260s linear infinite;transform-origin:0 0}
    @keyframes spin{to{transform:rotate(360deg)}}
    .pulse{animation:pulse 3.4s ease-out infinite;transform-box:fill-box;transform-origin:center}
    .pulse2{animation:pulse 3.4s ease-out infinite;animation-delay:1.7s;transform-box:fill-box;transform-origin:center}
    @keyframes pulse{0%{transform:scale(1);opacity:.8}100%{transform:scale(2.4);opacity:0}}
  </style>

  <path d="M1,1 H781 L799,19 V319 H19 L1,301 Z" fill="none" stroke="#D9D9D9" stroke-opacity=".35"/>

  <text x="36" y="50" class="mono" font-size="9" letter-spacing="3" fill="#8fc9cb">01 / REPO GALAXY</text>
  <text x="36" y="86" class="disp" font-size="24" font-weight="700" fill="#FFFFFF">@__LOGIN__</text>
  <text x="36" y="110" class="mono" font-size="10.5" fill="#D9D9D9">__SUMMARY__</text>
  <rect x="36" y="124" width="26" height="2" fill="#3C6E71"/>
  <text x="36" y="148" class="mono" font-size="8.5" fill="#D9D9D9" fill-opacity=".6">Each star is a repository.</text>
  <text x="36" y="161" class="mono" font-size="8.5" fill="#D9D9D9" fill-opacity=".6">Star size grows with stars.</text>

  <text x="36" y="204" class="mono" font-size="9" letter-spacing="3" fill="#8fc9cb">ORBITS</text>
  <g class="mono" font-size="10.5">
__LEGEND__
  </g>

  <g fill="none">
    <circle cx="560" cy="160" r="144" stroke="#D9D9D9" stroke-opacity=".35" stroke-width="7" stroke-dasharray="1 8.04"/>
    <circle cx="560" cy="160" r="144" stroke="#D9D9D9" stroke-opacity=".7" stroke-width="12" stroke-dasharray="1.5 89.5"/>
    <circle cx="560" cy="160" r="104" stroke="#FFFFFF" stroke-opacity=".14" stroke-dasharray="2 5"/>
    <circle cx="560" cy="160" r="64" stroke="#FFFFFF" stroke-opacity=".14" stroke-dasharray="2 5"/>
    <line x1="410" y1="160" x2="710" y2="160" stroke="#FFFFFF" stroke-opacity=".1"/>
    <line x1="560" y1="14" x2="560" y2="306" stroke="#FFFFFF" stroke-opacity=".1"/>
  </g>

  <g transform="translate(560 160)">
    <g class="spin">
      <g transform="scale(1.3)">
        <g color="#4f9a9e">
          <use href="#arm" stroke="currentColor" stroke-width="18" stroke-opacity=".09"/>
          <use href="#arm" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="0.1 6" stroke-opacity=".9"/>
          <use href="#arm" stroke="#FFFFFF" stroke-width="3.4" stroke-linecap="round" stroke-dasharray="0.1 23" stroke-dashoffset="4" stroke-opacity=".9"/>
        </g>
        <g color="#6f9bb9" transform="rotate(120)">
          <use href="#arm" stroke="currentColor" stroke-width="18" stroke-opacity=".09"/>
          <use href="#arm" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-dasharray="0.1 6" stroke-opacity=".9"/>
          <use href="#arm" stroke="#FFFFFF" stroke-width="3.4" stroke-linecap="round" stroke-dasharray="0.1 23" stroke-dashoffset="11" stroke-opacity=".9"/>
        </g>
        <g color="#D9D9D9" transform="rotate(240)">
          <use href="#arm" stroke="currentColor" stroke-width="18" stroke-opacity=".07"/>
          <use href="#arm" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-dasharray="0.1 6" stroke-opacity=".7"/>
          <use href="#arm" stroke="#FFFFFF" stroke-width="3.4" stroke-linecap="round" stroke-dasharray="0.1 23" stroke-dashoffset="17" stroke-opacity=".9"/>
        </g>
      </g>
    </g>
    <circle r="40" fill="url(#core)"/>
    <circle r="5" fill="#FFFFFF"/>
  </g>

__REPOSTARS__
</svg>
"""

PROJECTS = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="__H__" viewBox="0 0 800 __H__" role="img" aria-label="__ALT__">
  <defs>
  </defs>
  <style>
    .mono{font-family:'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace}
    .disp{font-family:'Space Grotesk','Avenir Next','Segoe UI',Helvetica,Arial,sans-serif}
    .plate{fill:#FFFFFF;fill-opacity:.04;stroke:#D9D9D9;stroke-opacity:.28}
    .no{font-size:8.5px;letter-spacing:2px;fill:#8fc9cb}
    .ttl{font-size:17px;font-weight:700;letter-spacing:.3px;fill:#FFFFFF}
    .dsc{font-size:9.5px;fill:#D9D9D9;fill-opacity:.75}
    .lang{font-size:9.5px;fill:#FFFFFF;letter-spacing:1px}
    .meta{font-size:9px;fill:#D9D9D9;fill-opacity:.7}
    .track{fill:none;stroke:#FFFFFF;stroke-opacity:.13;stroke-width:5}
    .arc{fill:none;stroke-width:5;stroke-linecap:butt}
    .tick{fill:none;stroke:#D9D9D9;stroke-opacity:.35;stroke-width:5;stroke-dasharray:1 3.32}
    .pct{font-size:10px;font-weight:700;fill:#FFFFFF;text-anchor:middle}
    .cap{font-size:6.5px;letter-spacing:1.5px;fill:#D9D9D9;fill-opacity:.6;text-anchor:middle}
    .cur{animation:b 1.1s steps(1) infinite}
    @keyframes b{50%{opacity:0}}
  </style>
  <path d="M1,1 H781 L799,19 V__HB__ H19 L1,__HC__ Z" fill="none" stroke="#D9D9D9" stroke-opacity=".35"/>
  <text x="36" y="34" class="mono" font-size="9" letter-spacing="3" fill="#8fc9cb">02 / CONSTELLATIONS</text>
  <text x="764" y="34" class="mono" font-size="9" letter-spacing="2" text-anchor="end" fill="#D9D9D9" fill-opacity=".7">__COUNT__</text>
  <line x1="24" y1="46" x2="776" y2="46" stroke="#D9D9D9" stroke-opacity=".25"/>
__PLATES__
</svg>
"""

LANGUAGES = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="250" viewBox="0 0 800 250" role="img" aria-label="__ALT__">
  <defs>
    <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#FFFFFF" stop-opacity="0"/>
      <stop offset=".5" stop-color="#FFFFFF" stop-opacity=".3"/>
      <stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="band"><rect x="36" y="68" width="728" height="34" rx="4"/></clipPath>
  </defs>
  <style>
    .mono{font-family:'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace}
    .disp{font-family:'Space Grotesk','Avenir Next','Segoe UI',Helvetica,Arial,sans-serif}
    .sweep{animation:sw 5s ease-in-out infinite}
    @keyframes sw{0%{transform:translateX(0)}100%{transform:translateX(950px)}}
    .cur{animation:b 1.1s steps(1) infinite}
    @keyframes b{50%{opacity:0}}
  </style>
  <path d="M1,1 H781 L799,19 V249 H19 L1,231 Z" fill="none" stroke="#D9D9D9" stroke-opacity=".35"/>
  <text x="36" y="34" class="mono" font-size="9" letter-spacing="3" fill="#8fc9cb">03 / SPECTRUM</text>
  <text x="764" y="34" class="mono" font-size="9" letter-spacing="1" text-anchor="end" fill="#D9D9D9" fill-opacity=".7">&gt; stack.scan<tspan class="cur">_</tspan></text>
  <line x1="24" y1="46" x2="776" y2="46" stroke="#D9D9D9" stroke-opacity=".25"/>
  <g clip-path="url(#band)">
__BAND__
    <g stroke="#353535" stroke-width="2">__SEPS__</g>
    <rect class="sweep" x="-120" y="68" width="120" height="34" fill="url(#sweep)"/>
  </g>
  <line x1="36" y1="112" x2="764" y2="112" stroke="#D9D9D9" stroke-opacity=".35" stroke-width="5" stroke-dasharray="1 6.28"/>
  <line x1="36" y1="112" x2="764" y2="112" stroke="#D9D9D9" stroke-opacity=".7" stroke-width="10" stroke-dasharray="1.5 71.3"/>
  <g class="mono" font-size="8" fill="#D9D9D9" fill-opacity=".7">
    <text x="36" y="136">0%</text>
    <text x="218" y="136" text-anchor="middle">25%</text>
    <text x="400" y="136" text-anchor="middle">50%</text>
    <text x="582" y="136" text-anchor="middle">75%</text>
    <text x="764" y="136" text-anchor="end">100%</text>
  </g>
  <g>
__LEGEND__
  </g>
</svg>
"""

TRANSMISSION = """<svg xmlns="http://www.w3.org/2000/svg" width="800" height="120" viewBox="0 0 800 120" role="img" aria-label="Open a channel: GitHub @__LOGIN__">
  <defs>
  </defs>
  <style>
    .mono{font-family:'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',monospace}
    .disp{font-family:'Space Grotesk','Avenir Next','Segoe UI',Helvetica,Arial,sans-serif}
    .wave{fill:none;stroke:#8fc9cb;stroke-width:1.4;transform-box:fill-box;transform-origin:center;animation:wave 3.6s ease-out infinite}
    .w2{animation-delay:1.2s}.w3{animation-delay:2.4s}
    @keyframes wave{0%{transform:scale(1);opacity:.9}100%{transform:scale(5);opacity:0}}
  </style>
  <path d="M1,1 H781 L799,19 V119 H19 L1,101 Z" fill="none" stroke="#D9D9D9" stroke-opacity=".35"/>
  <circle class="wave" cx="96" cy="60" r="8"/>
  <circle class="wave w2" cx="96" cy="60" r="8"/>
  <circle class="wave w3" cx="96" cy="60" r="8"/>
  <circle cx="96" cy="60" r="5" fill="#FFFFFF"/>
  <text x="170" y="40" class="mono" font-size="9" letter-spacing="3" fill="#8fc9cb">04 / SIGNAL</text>
  <text x="170" y="70" class="disp" font-size="24" font-weight="700" fill="#FFFFFF">Open a channel</text>
  <text x="170" y="92" class="mono" font-size="10" fill="#D9D9D9" fill-opacity=".75">github.com/__LOGIN__</text>
  <path d="M540,36 H750 L764,50 V84 H554 L540,70 Z" fill="#3C6E71" stroke="#8fc9cb" stroke-opacity=".7"/>
  <text x="562" y="56" class="mono" font-size="8" letter-spacing="2" fill="#FFFFFF" fill-opacity=".8">GITHUB</text>
  <text x="562" y="75" class="disp" font-size="__HFS__" font-weight="700" fill="#FFFFFF">@__LOGIN__</text>
  <text x="742" y="68" class="disp" font-size="18" fill="#FFFFFF" text-anchor="middle">→</text>
</svg>
"""


# Panels are transparent (GitHub's own background shows through). Default colours are tuned for dark
# themes; this block re-colours text and lines for light themes.
LIGHT = """    @media (prefers-color-scheme: light){
      [fill="#FFFFFF"]{fill:#1f2328}
      [fill="#D9D9D9"]{fill:#57606a}
      [fill="#8fc9cb"]{fill:#1f6f73}
      [stroke="#D9D9D9"]{stroke:#6e7781}
      [stroke="#FFFFFF"]{stroke:#6e7781}
      [stroke="#353535"]{stroke:#FFFFFF}
      .ttl,.pct{fill:#1f2328}
      .dsc,.meta,.cap,.lang{fill:#57606a}
      .no{fill:#1f6f73}
      .track,.tick{stroke:#6e7781}
      .plate{fill:#000000;fill-opacity:.03;stroke:#6e7781}
      .wave{stroke:#1f6f73}
    }
  """


def fill(tpl, **kw):
    for k, v in kw.items():
        tpl = tpl.replace(f"__{k}__", str(v))
    return tpl


# ------------------------------------------------------------------------- builders

def top_languages(repos, n=4):
    totals = {}
    for r in repos:
        for name, size in r["langs"].items():
            totals[name] = totals.get(name, 0) + size
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])[:n]
    whole = sum(size for _, size in ranked)
    return [(name, 100.0 * size / whole, LANG_COLORS[i]) for i, (name, size) in enumerate(ranked)] if whole else []


def build_hero(d, cfg):
    name = (d["name"] or d["login"]).strip()
    shown = name.upper()
    fs = min(34.0, 560 / (len(shown) * 0.82))
    return fill(HERO, NAME=esc(shown), FS=f"{fs:.1f}", LS=round(6 * fs / 34, 1),
                TAGLINE=esc(cfg["tagline"]), ALT=esc(f"{name}, {cfg['tagline']}"))


def build_stats(d, stars):
    alt = (f"{d['repo_count']} public repositories, {stars} stars, {d['contributions']} contributions "
           f"in the last year, longest streak {d['streak']} days, {d['followers']} followers")
    return fill(STATS, ALT=esc(alt), REPOS=f"{d['repo_count']:,}", STARS=f"{stars:,}",
                CONTRIB=f"{d['contributions']:,}", STREAK=f"{d['streak']}d", FOLLOWERS=f"{d['followers']:,}")


# (x, y, leader_x, leader_y, text_x, anchor, name_y, sub_y) -- filled in priority order
SLOTS = [
    (640, 120, 690, 68, 694, "start", 64, 76),
    (470, 110, 420, 62, 416, "end", 60, 72),
    (625, 215, 676, 268, 680, "start", 272, 284),
    (500, 215, 452, 268, 448, "end", 272, 284),
]
POLY_ORDER = [1, 0, 2, 3]


def primary_lang(r):
    return max(r["langs"].items(), key=lambda kv: kv[1])[0] if r["langs"] else None


def build_galaxy(d, repos, stars, langs, cfg):
    color_of_lang = {name: c for name, _, c in langs}

    def repo_color(r):
        lang = primary_lang(r)
        return color_of_lang.get(lang, OTHER) if lang else ACCENT

    legend = []
    for i, (name, p, c) in enumerate(langs):
        y = 215 + 24 * i
        w = max(2.0, 214 * p / 100)
        legend.append(
            f'    <rect x="36" y="{y}" width="7" height="7" fill="{c}"/>'
            f'<text x="52" y="{y + 7}" fill="#FFFFFF" font-weight="700">{esc(clip(name, 16))}</text>'
            f'<text x="250" y="{y + 7}" text-anchor="end" fill="#D9D9D9">{pct_label(p)}</text>\n'
            f'    <rect x="36" y="{y + 13}" width="214" height="2" fill="#FFFFFF" fill-opacity=".12"/>'
            f'<rect x="36" y="{y + 13}" width="{w:.1f}" height="2" fill="{c}"/>')
    if not langs:
        legend.append('    <text x="36" y="222" fill="#D9D9D9" fill-opacity=".6">No language data yet</text>')

    shown = repos[:4]
    pts, lines, dots, texts = {}, [], [], []
    for i, r in enumerate(shown):
        x, y, lx, ly, tx, anchor, yn, ys = SLOTS[i]
        pts[i] = (x, y)
        col = repo_color(r)
        rad = min(13.0, 4.5 + 2.0 * math.log2(1 + r["stars"]))
        cls = "pulse" if i % 2 == 0 else "pulse2"
        lines.append(f'    <line x1="{x}" y1="{y}" x2="{lx}" y2="{ly}"/>')
        dots.append(f'    <circle class="{cls}" cx="{x}" cy="{y}" r="{rad:.1f}" fill="none" stroke="{col}"/>'
                    f'<circle cx="{x}" cy="{y}" r="{rad:.1f}" fill="{col}"/>')
        lang = primary_lang(r) or "no code"
        texts.append(
            f'    <text x="{tx}" y="{yn}" text-anchor="{anchor}" font-size="10" font-weight="700" fill="#FFFFFF">{esc(clip(r["name"], 22))}</text>\n'
            f'    <text x="{tx}" y="{ys}" text-anchor="{anchor}" font-size="8.5" fill="#D9D9D9" fill-opacity=".7">{esc(lang)} · ★ {r["stars"]}</text>')
    poly = " ".join(f"{pts[k][0]},{pts[k][1]}" for k in POLY_ORDER if k in pts)
    repostars = (
        f'  <polygon points="{poly}" fill="none" stroke="#D9D9D9" stroke-opacity=".4" stroke-dasharray="3 4"/>\n'
        f'  <g stroke="#D9D9D9" stroke-opacity=".55">\n' + "\n".join(lines) + "\n  </g>\n"
        f'  <g>\n' + "\n".join(dots) + "\n  </g>\n"
        f'  <g class="mono">\n' + "\n".join(texts) + "\n  </g>")
    summary = f"{d['repo_count']} repositories · {stars} stars"
    return fill(GALAXY, LOGIN=esc(d["login"]), SUMMARY=esc(summary), LEGEND="\n".join(legend), REPOSTARS=repostars)


def wrap_desc(text):
    if not text:
        return ["No description provided."]
    lines = textwrap.wrap(" ".join(text.split()), 38)
    if len(lines) > 2:
        lines = [lines[0], clip(lines[1], 38)]
    return lines


def dial(cx, cy, pct, color, caption):
    if pct is None:
        arc, label = "", "—"
    else:
        arc = (f'<circle r="24" class="arc" stroke="{color}" '
               f'stroke-dasharray="{150.8 * pct / 100:.1f} 150.8" transform="rotate(-90)"/>')
        label = f"{round(pct)}%"
    return (f'  <g transform="translate({cx} {cy})">\n'
            f'    <circle r="33" class="tick"/><circle r="24" class="track"/>{arc}\n'
            f'    <text y="3.5" class="mono pct">{label}</text><text y="48" class="mono cap">{caption}</text>\n  </g>')


def build_projects(repos, langs):
    color_of_lang = {name: c for name, _, c in langs}
    shown = repos[:4]
    rows = max(1, math.ceil(len(shown) / 2))
    height = 62 + 148 * rows + 4
    out = []
    for i, r in enumerate(shown):
        x = 24 if i % 2 == 0 else 410
        y = 62 + 148 * (i // 2)
        lang = primary_lang(r)
        col = color_of_lang.get(lang, OTHER) if lang else NO_LANG
        desc = wrap_desc(r["description"])
        total = sum(r["langs"].values())
        share = 100.0 * r["langs"][lang] / total if lang and total else None
        parts = [
            f'  <path class="plate" d="M{x},{y} H{x + 352} L{x + 366},{y + 14} V{y + 136} H{x} Z"/>',
            f'  <rect x="{x}" y="{y}" width="3" height="136" fill="{col}"/>',
            f'  <text x="{x + 18}" y="{y + 24}" class="mono no">PLATE {i + 1:02d}</text>',
            f'  <text x="{x + 18}" y="{y + 52}" class="disp ttl">{esc(clip(r["name"], 22))}<tspan class="cur" fill="#8fc9cb"> _</tspan></text>',
        ]
        for j, line in enumerate(desc):
            parts.append(f'  <text x="{x + 18}" y="{y + 72 + 13 * j}" class="mono dsc">{esc(line)}</text>')
        if lang:
            my = y + (96 if len(desc) > 1 else 90)
            parts.append(f'  <rect x="{x + 18}" y="{my}" width="7" height="7" fill="{col}"/>'
                         f'<text x="{x + 32}" y="{my + 7}" class="mono lang">{esc(clip(lang.upper(), 20))}</text>')
        parts.append(f'  <text x="{x + 18}" y="{y + 121}" class="mono meta">★ {r["stars"]}  ·  updated {ago(r["days_ago"])}</text>')
        parts.append(dial(x + 318, y + 76, share, col, "LANG SHARE" if lang else "NO CODE"))
        out.append("\n".join(parts))
    if not shown:
        out.append('  <text x="36" y="86" class="mono dsc">No public repositories yet.</text>')
    count = f"{len(shown)} PLATE" + ("" if len(shown) == 1 else "S")
    alt = "Projects: " + ", ".join(r["name"] for r in shown) if shown else "No public repositories yet"
    return fill(PROJECTS, H=height, HB=height - 1, HC=height - 19, COUNT=count, ALT=esc(alt), PLATES="\n".join(out))


def build_languages(langs):
    x, W = 36.0, 728.0
    rects, seps, cols = [], [], []
    for i, (name, p, c) in enumerate(langs):
        w = W * p / 100
        rects.append(f'    <rect x="{x:.1f}" y="68" width="{w:.1f}" height="34" fill="{c}"/>')
        if i:
            seps.append(f'<line x1="{x:.1f}" y1="68" x2="{x:.1f}" y2="102"/>')
        x += w
        cx = 36 + 184 * i
        cols.append(
            f'    <rect x="{cx}" y="160" width="10" height="10" fill="{c}"/>\n'
            f'    <text x="{cx}" y="206" class="disp" font-size="30" font-weight="700" fill="#FFFFFF">{pct_label(p)}</text>\n'
            f'    <text x="{cx}" y="226" class="mono" font-size="10" letter-spacing="2" fill="#8fc9cb">{esc(clip(name.upper(), 14))}</text>')
    if not langs:
        rects = [f'    <rect x="36" y="68" width="728" height="34" fill="{OTHER}" fill-opacity=".4"/>']
        cols = ['    <text x="36" y="206" class="mono" font-size="12" fill="#D9D9D9">No language data yet</text>']
    alt = "Language spectrum: " + ", ".join(f"{n} {pct_label(p)}" for n, p, _ in langs) if langs else "No language data yet"
    return fill(LANGUAGES, ALT=esc(alt), BAND="\n".join(rects), SEPS="".join(seps), LEGEND="\n".join(cols))


def build_transmission(d):
    handle_fs = 15 if len(d["login"]) <= 16 else max(10, round(15 * 16 / len(d["login"])))
    return fill(TRANSMISSION, LOGIN=esc(d["login"]), HFS=handle_fs)


# ------------------------------------------------------------------------------ main

def main():
    with open(os.path.join(ROOT, "profile.config.json"), encoding="utf-8") as f:
        cfg = json.load(f)

    if "--sample" in sys.argv:
        with open(os.path.join(HERE, "sample-data.json"), encoding="utf-8") as f:
            d = json.load(f)
    else:
        d = load_live(cfg["login"])

    exclude = {n.lower() for n in cfg.get("exclude", [])}
    repos = [r for r in d["repos"] if r["name"].lower() not in exclude]
    repos.sort(key=lambda r: (-r["stars"], r["days_ago"]))
    stars = sum(r["stars"] for r in d["repos"])
    langs = top_languages(d["repos"])

    files = {
        "hero.svg": build_hero(d, cfg),
        "galaxy.svg": build_galaxy(d, repos, stars, langs, cfg),
        "stats.svg": build_stats(d, stars),
        "projects.svg": build_projects(repos, langs),
        "languages.svg": build_languages(langs),
        "transmission.svg": build_transmission(d),
    }
    os.makedirs(ASSETS, exist_ok=True)
    for name, svg in files.items():
        with open(os.path.join(ASSETS, name), "w", encoding="utf-8", newline="\n") as f:
            f.write(svg.replace("</style>", LIGHT + "</style>", 1))
    print(f"Wrote {len(files)} SVGs: {d['repo_count']} repos, {stars} stars, "
          f"{d['contributions']} contributions, streak {d['streak']}d, {d['followers']} followers")


if __name__ == "__main__":
    main()
