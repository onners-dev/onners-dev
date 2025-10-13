#!/usr/bin/env python3
"""
Fetch latest videos from YouTube RSS feed and replace the block in README.md
between <!-- YOUTUBE-VIDEOS-START --> and <!-- YOUTUBE-VIDEOS-END -->
"""

import argparse
import feedparser
import requests
import html
from datetime import datetime

RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

TEMPLATE = """<!-- YOUTUBE-VIDEOS-START -->
{content}
<!-- YOUTUBE-VIDEOS-END -->"""

VIDEO_ITEM_MD = """<a href="{url}" target="_blank" rel="noopener noreferrer">
  <img src="{thumb_url}" alt="{title}" width="320" style="max-width:100%;height:auto;border:1px solid #eaeaea" />
</a>

**[{title}]({url})**  
{published}
"""

def fetch_videos(channel_id, max_videos=3):
    url = RSS_URL.format(channel_id=channel_id)
    d = feedparser.parse(url)
    videos = []
    for entry in d.entries[:max_videos]:
        vid = {}
        vid['title'] = html.unescape(entry.title)
        vid['url'] = entry.link
        # published date
        try:
            published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
        except Exception:
            published = ""
        vid['published'] = published
        # thumbnail: YouTube thumbnail pattern: https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg
        # extract video id from link -> last part after 'v=' or after 'watch?v=' or /videos/VIDEO_ID? etc.
        vid_id = None
        if 'yt:videoid' in entry:
            vid_id = entry['yt:videoid']
        else:
            # fallback parse from link
            if 'v=' in entry.link:
                vid_id = entry.link.split('v=')[-1].split('&')[0]
            else:
                # possibly ends with /videos/VIDEO_ID
                vid_id = entry.link.rstrip('/').split('/')[-1]
        vid['thumb_url'] = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        videos.append(vid)
    return videos

def build_markdown(videos):
    parts = []
    for v in videos:
        part = VIDEO_ITEM_MD.format(url=v['url'], thumb_url=v['thumb_url'], title=v['title'], published=v['published'])
        parts.append(part)
    return "\n\n".join(parts)

def replace_block(readme_path, new_block):
    with open(readme_path, 'r', encoding='utf-8') as f:
        text = f.read()
    start = "<!-- YOUTUBE-VIDEOS-START -->"
    end = "<!-- YOUTUBE-VIDEOS-END -->"
    if start in text and end in text:
        before, rest = text.split(start, 1)
        _, after = rest.split(end, 1)
        new_text = before + new_block + after
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("README updated")
    else:
        print("Markers not found in README. No changes made.")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel-id", required=True)
    parser.add_argument("--readme", required=True)
    parser.add_argument("--max-videos", type=int, default=3)
    args = parser.parse_args()

    videos = fetch_videos(args.channel_id, args.max_videos)
    if not videos:
        content = "No videos found."
    else:
        content = build_markdown(videos)
    new_block = TEMPLATE.format(content=content)
    replace_block(args.readme, new_block)

if __name__ == "__main__":
    main()
