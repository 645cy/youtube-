import sqlite3, json
conn = sqlite3.connect('data/tubefactory.db')
c = conn.cursor()

c.execute('SELECT COUNT(*) FROM channels')
total = c.fetchone()[0]
c.execute('SELECT COUNT(*) FROM channels WHERE discovery_score IS NOT NULL')
discovered = c.fetchone()[0]
print(f'数据库总频道: {total}')
print(f'有评分的发现频道: {discovered}')

c.execute('SELECT id, name, config_json FROM crawler_tasks')
rows = c.fetchall()
print(f'\n任务数: {len(rows)}')
for row in rows:
    print(f'  任务{row[0]}: {row[1]}')
    if row[2]:
        try:
            cfg = json.loads(row[2])
            keywords = cfg.get('keywords', [])
            max_r = cfg.get('max_results_per_keyword', 25)
            print(f'    关键词: {keywords} | 每词{max_r}个')
        except:
            pass

c.execute('SELECT COUNT(*) FROM channel_discovery_results')
print(f'\nChannelDiscoveryResult 总数: {c.fetchone()[0]}')

c.execute("SELECT COUNT(*), SUM(items_found) FROM crawler_task_runs WHERE status='success'")
row = c.fetchone()
print(f'成功运行次数: {row[0]} | 总发现数: {row[1] or 0}')

conn.close()
