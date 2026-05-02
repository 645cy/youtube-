# -*- coding: utf-8 -*-
import urllib.request, json, os, sqlite3

print("=" * 60)
print("  TubeFactory 深度架构审计")
print("=" * 60)

# 1. 分析类 POST API
print("\n【1. 分析模块 POST API】")
analysis_posts = [
    ("/api/v1/analysis/viral-detection", b'{"target_type":"video","target_id":"1","analysis_types":["viral_detection"]}'),
    ("/api/v1/analysis/evergreen", b'{"target_type":"video","target_id":"1","analysis_types":["evergreen"]}'),
    ("/api/v1/analysis/sentiment", b'{"target_type":"video","target_id":"1","analysis_types":["sentiment"]}'),
    ("/api/v1/analysis/monetization", b'{"target_type":"video","target_id":"1","analysis_types":["monetization"]}'),
    ("/api/v1/analysis/full-analysis", b'{"target_type":"video","target_id":"1"}'),
]
for path, body in analysis_posts:
    try:
        req = urllib.request.Request(f"http://localhost:8000{path}", data=body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            print(f"  ✅ POST {path.split('/')[-1]}: {r.status}")
    except urllib.error.HTTPError as e:
        print(f"  ⚠️  POST {path.split('/')[-1]}: HTTP {e.code} (数据库无视频数据时预期)")
    except Exception as e:
        print(f"  ❌ POST {path.split('/')[-1]}: {type(e).__name__} {str(e)[:60]}")

# 2. 雷达模块
print("\n【2. 雷达模块】")
try:
    req = urllib.request.Request("http://localhost:8000/api/v1/radar/compare?channel_ids=1,2")
    with urllib.request.urlopen(req, timeout=3) as r:
        print(f"  ✅ GET /radar/compare: {r.status}")
except Exception as e:
    print(f"  ⚠️  GET /radar/compare: {type(e).__name__} (无数据时预期)")

# 3. 数据库实体检查
print("\n【3. 数据库实体检查】")
db_path = r"D:\Projects\YouTube\tubefactory-ocp\data\tubefactory.db"
if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ["channels", "videos", "monitor_jobs", "analysis_logs", "metric_history"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} 条记录")
            except sqlite3.OperationalError:
                print(f"  ⚠️  {table}: 表不存在")
        conn.close()
    except Exception as e:
        print(f"  ❌ 数据库读取失败: {e}")
else:
    print(f"  ❌ 数据库文件不存在: {db_path}")

# 4. 前端源码假数据检查
print("\n【4. 前端源码假数据检查】")
web_dir = r"D:\Projects\YouTube\tubefactory-ocp\apps\web\app"
found_random = []
for root, dirs, files in os.walk(web_dir):
    for f in files:
        if f.endswith('.tsx'):
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                if 'Math.random()' in content:
                    found_random.append(os.path.relpath(filepath, web_dir))

if found_random:
    for f in found_random:
        print(f"  ⚠️  {f} 包含 Math.random()")
else:
    print(f"  ✅ page.tsx 中无 Math.random() 假数据")

# 5. 环境配置检查
print("\n【5. 环境配置检查】")
env_path = r"D:\Projects\YouTube\tubefactory-ocp\apps\api\.env"
if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        env_content = f.read()
        has_youtube_key = 'YOUTUBE_API_KEY' in env_content
        print(f"  {'✅' if has_youtube_key else '❌'} YouTube API Key 已配置")
else:
    print(f"  ❌ .env 文件不存在")

# 6. 缩略图域名配置
print("\n【6. 缩略图域名配置】")
next_config = r"D:\Projects\YouTube\tubefactory-ocp\apps\web\next.config.js"
if os.path.exists(next_config):
    with open(next_config, 'r', encoding='utf-8') as f:
        config = f.read()
        domains = ['yt3.ggpht.com', 'yt3.googleusercontent.com', 'i.ytimg.com']
        all_found = all(d in config for d in domains)
        print(f"  {'✅' if all_found else '❌'} YouTube 缩略图域名已配置")
        if not all_found:
            for d in domains:
                print(f"     {'✅' if d in config else '❌'} {d}")
else:
    print(f"  ❌ next.config.js 不存在")

# 7. 启动脚本检查
print("\n【7. 启动脚本检查】")
bat_path = r"D:\Projects\YouTube\tubefactory-ocp\Start-TubeFactory.bat"
if os.path.exists(bat_path):
    with open(bat_path, 'r', encoding='utf-8') as f:
        bat = f.read()
        has_browser = 'start http://localhost:3000' in bat
        has_backend = 'uvicorn' in bat
        has_frontend = 'standalone' in bat or 'server.js' in bat
        print(f"  {'✅' if has_backend else '❌'} 启动后端")
        print(f"  {'✅' if has_frontend else '❌'} 启动前端")
        print(f"  {'✅' if has_browser else '❌'} 自动打开浏览器")
else:
    print(f"  ❌ Start-TubeFactory.bat 不存在")

print("\n" + "=" * 60)
print("  深度审计完成")
print("=" * 60)
