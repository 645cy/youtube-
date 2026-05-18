import yt_dlp

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'extract_flat': True,
    'playlistend': 10,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info('ytsearch10:Midjourney tutorial', download=False)
    entries = info.get('entries', [])
    print(f'Found {len(entries)} results')
    for e in entries[:5]:
        print(f"  {e.get('title', '')[:50]} | channel: {e.get('channel', '')}")
