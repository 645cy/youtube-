import yt_dlp, os

print("HTTPS_PROXY:", os.environ.get("HTTPS_PROXY"))

ydl_opts = {
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'extract_flat': True,
    'playlistend': 5,
    'proxy': os.environ.get("HTTPS_PROXY", ""),
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    print("Extracting...")
    info = ydl.extract_info('ytsearch5:test', download=False)
    entries = info.get('entries', [])
    print(f'Found {len(entries)} results')
    for e in entries[:3]:
        print(f"  {e.get('title', '')[:40]} | {e.get('channel', '')}")
