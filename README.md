# AI 速听 · 英文播客中文版

把英文音视频内容自动转写、翻译并用 AI 配音成中文播客。每集附中英文字幕。

## 订阅

**RSS Feed**: <https://vktsien.github.io/podcast/feed.xml>

把上面这个链接复制到任何播客 App（Apple Podcasts / 小宇宙 / Pocket Casts / Overcast / Spotify 等）即可订阅。

## 工作流

```
URL → yt-dlp 下载音频 → faster-whisper 转写英文
   → deep-translator 翻译中文 → Edge TTS 生成中文音频
   → 写入 feed.xml → push GitHub Pages
```

由 [audio-to-podcast](https://github.com/vktsien/audio-to-podcast) 技能驱动。

## 目录结构

```
podcast/
├── feed.xml             ← RSS 订阅入口
├── cover.jpg            ← 播客封面（建议 1400x1400 JPG）
├── generate_feed.py     ← 重新构建 feed.xml
└── episodes/
    └── YYYY-MM-DD-slug.mp3
        YYYY-MM-DD-slug.zh.txt   中文文稿
        YYYY-MM-DD-slug.en.txt   英文原文
        YYYY-MM-DD-slug.zh.srt   中文字幕
        YYYY-MM-DD-slug.en.srt   英文字幕
```

## 版权

每集配音由 AI 生成，原内容版权归原作者。
