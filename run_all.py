import sys, os, subprocess, time
sys.path.insert(0, '.')
sys.path.insert(0, './apps/api')
import asyncio
from sqlalchemy import select
from packages.db.schema import get_sessionmaker, CrawlerTask

async def get_tasks():
    sm = get_sessionmaker()
    async with sm() as session:
        result = await session.execute(
            select(CrawlerTask).where(CrawlerTask.task_type == 'channel_discovery').where(CrawlerTask.status == 'active').order_by(CrawlerTask.id)
        )
        tasks = result.scalars().all()
        return [(t.id, t.name) for t in tasks]

def run_task(task_id, timeout=240):
    env = os.environ.copy()
    env['DATABASE_URL'] = 'sqlite+aiosqlite:///D:/Projects/YouTube/tubefactory-ocp/data/tubefactory.db'
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, 'run_single.py', str(task_id)],
            cwd='D:\\Projects\\YouTube\\tubefactory-ocp',
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        elapsed = time.time() - start
        output = proc.stdout + proc.stderr
        return {
            'task_id': task_id,
            'returncode': proc.returncode,
            'elapsed': elapsed,
            'output': output.strip()
        }
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        # try to kill any remaining child processes
        if e.process:
            try:
                e.process.kill()
            except Exception:
                pass
        return {
            'task_id': task_id,
            'returncode': -1,
            'elapsed': elapsed,
            'output': f'TIMEOUT after {timeout}s'
        }

async def main():
    tasks = await get_tasks()
    print(f'[{time.strftime(\"%H:%M:%S\")}] 共 {len(tasks)} 个任务')
    total_found = 0
    total_passed = 0
    success_count = 0
    error_count = 0
    timeout_count = 0
    
    for i, (task_id, task_name) in enumerate(tasks, 1):
        print(f'[{time.strftime(\"%H:%M:%S\")}] [{i}/{len(tasks)}] ID={task_id} {task_name} ...')
        result = run_task(task_id, timeout=240)
        output = result['output']
        print(f'[{time.strftime(\"%H:%M:%S\")}] [{i}/{len(tasks)}] 耗时={result[\"elapsed\"]:.1f}s 输出={output}')
        
        if result['returncode'] == 0 and 'SUCCESS:' in output:
            success_count += 1
            # parse found/passed
            try:
                parts = output.split()
                for p in parts:
                    if p.startswith('found='):
                        total_found += int(p.split('=')[1])
                    if p.startswith('passed='):
                        total_passed += int(p.split('=')[1])
            except Exception:
                pass
        elif result['returncode'] == -1 or 'TIMEOUT' in output:
            timeout_count += 1
            error_count += 1
        else:
            error_count += 1
        
        time.sleep(3)
    
    print(f'[{time.strftime(\"%H:%M:%S\")}] 全部完成')
    print(f'FINAL_SUMMARY: success={success_count} errors={error_count} timeouts={timeout_count} total_found={total_found} total_passed={total_passed}')

if __name__ == '__main__':
    asyncio.run(main())
