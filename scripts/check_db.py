import sqlite3
import os

print('tubefactory.db exists:', os.path.exists('data/tubefactory.db'))
print('youtube_monitor.db exists:', os.path.exists('youtube_monitor.db'))

if os.path.exists('youtube_monitor.db'):
    conn = sqlite3.connect('youtube_monitor.db')
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('youtube_monitor tables:', [r[0] for r in cursor])
    cursor = conn.execute('PRAGMA table_info(channels)')
    print('youtube_monitor channels cols:', [r[1] for r in cursor])
    cursor = conn.execute('SELECT COUNT(*) FROM crawler_tasks')
    print('youtube_monitor tasks:', cursor.fetchone()[0])

if os.path.exists('data/tubefactory.db'):
    conn = sqlite3.connect('data/tubefactory.db')
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print('tubefactory tables:', [r[0] for r in cursor])
    cursor = conn.execute('PRAGMA table_info(channels)')
    print('tubefactory channels cols:', [r[1] for r in cursor])
    cursor = conn.execute('SELECT COUNT(*) FROM crawler_tasks')
    print('tubefactory tasks:', cursor.fetchone()[0])
    cursor = conn.execute('SELECT COUNT(*) FROM channels')
    print('tubefactory channels:', cursor.fetchone()[0])
