import re
from collections import Counter
ids = []
with open('tmp/seed_bulk.py', 'r') as f:
    for line in f:
        if 'youtube_id' in line and 'channel_idx' in line:
            m = re.search(r'"youtube_id": "([^"]+)"', line)
            if m:
                ids.append(m.group(1))
dups = {k: v for k, v in Counter(ids).items() if v > 1}
print('Duplicates:', dups)
