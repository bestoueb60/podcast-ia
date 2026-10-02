#!/usr/bin/env python3
"""Rebuild feed.xml and index.html from episodes/*.mp3 and scripts/*.txt."""
import glob, os, re, subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

BASE = "https://bestoueb60.github.io/podcast-ia"
KEEP = 30
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def long_date(d):
    return f"{JOURS[d.weekday()]} {d.day}{'er' if d.day == 1 else ''} {MOIS[d.month-1]} {d.year}"

def duration(path, size):
    try:
        out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "default=nw=1:nk=1", path], text=True)
        return int(float(out.strip()))
    except Exception:
        return int(size * 8 / 48000)  # estimate at ~48 kbit/s

mp3s = sorted(glob.glob("episodes/*.mp3"), reverse=True)
for old in mp3s[KEEP:]:
    os.remove(old)
mp3s = mp3s[:KEEP]

def notes(date):
    p = f"scripts/{date}-notes.html"
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    p = f"scripts/{date}-sources.md"
    if os.path.exists(p):
        links = re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", open(p, encoding="utf-8").read())
        if links:
            return "<ul>" + "".join(f'<li><a href="{escape(u, {chr(34): "&quot;"})}">{escape(t)}</a></li>' for t, u in links) + "</ul>"
    return ""

def cdata(x):
    return "<![CDATA[" + x.replace("]]>", "]]]]><![CDATA[>") + "]]>"

def summary(date):
    p = f"scripts/{date}.summary.txt"
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    return "Actualité IA du jour."

items = []
episodes = []
for mp3 in mp3s:
    date = os.path.basename(mp3)[:-4]
    d = datetime.strptime(date, "%Y-%m-%d")
    size = os.path.getsize(mp3)
    dur = duration(mp3, size)
    url = f"{BASE}/episodes/{date}.mp3"
    pub = format_datetime(d.replace(hour=6, tzinfo=timezone.utc))
    summ = summary(date)
    nts = notes(date)
    episodes.append((date, d, nts))
    desc = f"<p>{escape(summ)}</p>" + nts
    items.append(f"""    <item>
      <title>Le Brief IA – {long_date(d)}</title>
      <description>{cdata(desc)}</description>
      <content:encoded>{cdata(nts or "<p>" + escape(summ) + "</p>")}</content:encoded>
      <itunes:summary>{escape(summ)}</itunes:summary>
      <guid isPermaLink="true">{url}</guid>
      <pubDate>{pub}</pubDate>
      <enclosure url="{url}" length="{size}" type="audio/mpeg"/>
      <itunes:duration>{dur}</itunes:duration>
    </item>""")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Le Brief IA</title>
    <link>{BASE}/</link>
    <description>Actu IA quotidienne en français</description>
    <language>fr-fr</language>
    <itunes:author>Le Brief IA</itunes:author>
    <itunes:image href="{BASE}/cover.png"/>
    <itunes:explicit>false</itunes:explicit>
{chr(10).join(items)}
  </channel>
</rss>
"""
open("feed.xml", "w", encoding="utf-8").write(feed)

blocks = "".join(
    f'<section><h2>{long_date(d)}</h2><audio controls preload="none" src="episodes/{date}.mp3"></audio>{nts}</section>'
    for date, d, nts in episodes)
open("index.html", "w", encoding="utf-8").write(f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Le Brief IA</title>
<style>body{{font-family:system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem;background:#111;color:#eee;line-height:1.5}}
a{{color:#8ab4f8}}code{{background:#222;padding:.3rem .5rem;border-radius:4px;word-break:break-all}}audio{{width:100%}}
section{{border-top:1px solid #333;margin-top:2rem}}h3{{margin-bottom:.2rem}}</style></head>
<body><h1>Le Brief IA</h1><p>Actu IA quotidienne en français.</p>
<p>Flux à copier dans votre appli de podcasts :</p><p><code>{BASE}/feed.xml</code></p>
{blocks}
</body></html>
""")
