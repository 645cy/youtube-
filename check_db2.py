import sqlite3, json
conn = sqlite3.connect('data/tubefactory.db')
c = conn.cursor()

c.execute('PRAGMA table_info(channel_discovery_results)')
print('channel_discovery_results 表结构:')
for col in c.fetchall():
    print(f'  {col[1]}: {col[2]}')

c.execute('SELECT COUNT(*) FROM channel_discovery_results')
print(f'\nChannelDiscoveryResult 数量: {c.fetchone()[0]}')

c.execute("SELECT id, task_id, items_found, result_json FROM crawler_task_runs WHERE status='success' ORDER BY id DESC LIMIT 3")
print('\n最近3次成功运行的 result_json:')
for row in c.fetchall():
    print(f'  Run {row[0]} (task={row[1]}, items={row[2]})')
    if row[3]:
        try:
            data = json.loads(row[3])
            print(f'    source_status: {data.get("source_status")}')
            print(f'    channels_found: {data.get("channels_found")}')
            print(f'    channels_passed: {data.get("channels_passed")}')
        except:
            print(f'    (invalid json)')
    else:
        print(f'    (no result_json)')

conn.close()
