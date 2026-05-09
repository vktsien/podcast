#!/usr/bin/env python3
"""扫描 episodes/ 目录生成 feed.xml（iTunes Podcast 兼容）。"""
import datetime
import json
import re
import subprocess
import xml.sax.saxutils
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).parent
EP_DIR = ROOT / "episodes"
FEED_PATH = ROOT / "feed.xml"

# 频道元数据（可改）
CHANNEL = {
    "title": "每日WEB4",
    "subtitle": "AI 自动转写英文音频并配中文 TTS",
    "description": "把英文音视频内容自动转写、翻译并用 AI 配音成中文播客。每集附中英文字幕。",
    "language": "zh-CN",
    "author": "vktsien",
    "owner_name": "vktsien",
    "owner_email": "vktsien@gmail.com",
    "category": "Technology",
    "explicit": "no",
    "site_url": "https://vktsien.github.io/podcast/",
    "feed_url": "https://vktsien.github.io/podcast/feed.xml",
    "image_url": "https://vktsien.github.io/podcast/cover.jpg",
    "copyright": "© 2026 vktsien (内容版权归原作者，本站仅 AI 转写翻译)",
}


def esc(s):
    return xml.sax.saxutils.escape(s or "")


def cdata(s):
    return f"<![CDATA[{s or ''}]]>"


def ffprobe_duration(mp3_path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_path)],
        capture_output=True, text=True,
    ).stdout.strip()
    return int(float(out)) if out else 0


def fmt_duration(secs):
    h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def build_episode_item(mp3_path):
    base = mp3_path.stem  # YYYY-MM-DD-slug
    parts = base.split("-", 3)
    if len(parts) < 4:
        raise ValueError(f"unexpected episode filename: {mp3_path.name}")
    date_str = "-".join(parts[:3])
    slug = parts[3]
    pub = datetime.datetime.fromisoformat(date_str).replace(tzinfo=datetime.timezone.utc)

    # 优先读 meta.json（含原始章节标题/演讲者/简介），fallback 才用 slug
    meta_path = mp3_path.parent / f"{base}.meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    # show notes：用 zh.txt + 末尾贴 en.txt 链接
    zh_txt = (mp3_path.parent / f"{base}.zh.txt").read_text(encoding="utf-8") if (mp3_path.parent / f"{base}.zh.txt").exists() else ""
    en_url = f"{CHANNEL['site_url']}episodes/{base}.en.txt"
    speakers = meta.get("speakers") or []
    summary = meta.get("summary") or ""
    header_lines = []
    if speakers:
        header_lines.append("讲者: " + " / ".join(speakers))
    if summary:
        header_lines.append(summary)
    header = "\n".join(header_lines)
    description = (header + "\n\n" if header else "") + zh_txt + f"\n\n---\n英文原文: {en_url}"

    if meta.get("title"):
        title_human = meta["title"]
    else:
        # fallback：剥掉 slug 开头可能存在的 yt-id（含连字符）+ 章节号 NN
        # 形如 "Da-K16R-s-k-13-ethereum-meets-hardware" → "ethereum meets hardware"
        m = re.match(r"^[A-Za-z0-9_-]+?-(\d{2})-(.+)$", slug)
        if m:
            title_human = m.group(2).replace("-", " ").title()
        else:
            title_human = slug.replace("-", " ").title()
    duration = ffprobe_duration(mp3_path)
    size = mp3_path.stat().st_size
    enclosure_url = f"{CHANNEL['site_url']}episodes/{mp3_path.name}"

    return f"""    <item>
      <title>{esc(title_human)}</title>
      <description>{cdata(description)}</description>
      <itunes:summary>{cdata(description[:500])}</itunes:summary>
      <pubDate>{format_datetime(pub)}</pubDate>
      <enclosure url="{esc(enclosure_url)}" length="{size}" type="audio/mpeg"/>
      <guid isPermaLink="false">{base}</guid>
      <itunes:author>{esc(CHANNEL['author'])}</itunes:author>
      <itunes:duration>{fmt_duration(duration)}</itunes:duration>
      <itunes:explicit>{CHANNEL['explicit']}</itunes:explicit>
    </item>"""


def main():
    eps = sorted(EP_DIR.glob("*.mp3"), reverse=True)  # 新→旧
    items_xml = "\n".join(build_episode_item(p) for p in eps)
    last_build = format_datetime(datetime.datetime.now(datetime.timezone.utc))

    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
     xmlns:atom="http://www.w3.org/2005/Atom"
     xmlns:content="http://purl.org/rss/1.0/modules/content/"
     version="2.0">
  <channel>
    <title>{esc(CHANNEL['title'])}</title>
    <link>{esc(CHANNEL['site_url'])}</link>
    <atom:link href="{esc(CHANNEL['feed_url'])}" rel="self" type="application/rss+xml"/>
    <description>{cdata(CHANNEL['description'])}</description>
    <language>{esc(CHANNEL['language'])}</language>
    <copyright>{esc(CHANNEL['copyright'])}</copyright>
    <lastBuildDate>{last_build}</lastBuildDate>
    <generator>audio-to-podcast skill</generator>
    <itunes:author>{esc(CHANNEL['author'])}</itunes:author>
    <itunes:subtitle>{esc(CHANNEL['subtitle'])}</itunes:subtitle>
    <itunes:summary>{esc(CHANNEL['description'])}</itunes:summary>
    <itunes:owner>
      <itunes:name>{esc(CHANNEL['owner_name'])}</itunes:name>
      <itunes:email>{esc(CHANNEL['owner_email'])}</itunes:email>
    </itunes:owner>
    <itunes:image href="{esc(CHANNEL['image_url'])}"/>
    <itunes:category text="{esc(CHANNEL['category'])}"/>
    <itunes:explicit>{CHANNEL['explicit']}</itunes:explicit>
{items_xml}
  </channel>
</rss>
"""
    FEED_PATH.write_text(feed, encoding="utf-8")
    print(f"feed.xml 写出 {FEED_PATH}（{len(eps)} 集）")


if __name__ == "__main__":
    main()
