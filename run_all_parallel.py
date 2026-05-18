import subprocess, sys, os, time, json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

def run_task(task_id):
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
            timeout=240
        )
        elapsed = time.time() - start
        output = proc.stdout.strip()
        # also capture stderr but filter out FutureWarning
        stderr_lines = [l for l in proc.stderr.strip().split('\n') if l and 'FutureWarning' not in l]
        if stderr_lines and proc.returncode != 0:
            output += ' | STDERR: ' + ' '.join(stderr_lines)
        return {
            'task_id': task_id,
            'code': proc.returncode,
            'elapsed': elapsed,
            'output': output
        }
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        return {
            'task_id': task_id,
            'code': -1,
            'elapsed': elapsed,
            'output': 'TIMEOUT after 240s'
        }
    except Exception as e:
        elapsed = time.time() - start
        return {
            'task_id': task_id,
            'code': -1,
            'elapsed': elapsed,
            'output': f'ERROR: {e}'
        }

if __name__ == '__main__':
    # get all active channel_discovery tasks
    import asyncio
    sys.path.insert(0, '.')
    sys.path.insert(0, './apps/api')
    from sqlalchemy import select
    from packages.db.schema import get_sessionmaker, CrawlerTask

    async def get_task_ids():
        sm = get_sessionmaker()
        async with sm() as session:
            result = await session.execute(
                select(CrawlerTask).where(CrawlerTask.task_type == 'channel_discovery').where(CrawlerTask.status == 'active').order_by(CrawlerTask.id)
            )
            return [t.id for t in result.scalars().all()]

    task_ids = asyncio.run(get_task_ids())
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 共 {len(task_ids)} 个任务，开始并发执行 (max_workers=20)...')
    
    overall_start = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(run_task, tid): tid for tid in task_ids}
        for future in futures:
            r = future.result()
            results.append(r)
            status = 'OK' if r['code'] == 0 else 'FAIL'
            print(f'[{datetime.now().strftime("%H:%M:%S")}] TASK {r["task_id"]} {status} elapsed={r["elapsed"]:.1f}s output={r["output"]}')
    
    overall_elapsed = time.time() - overall_start
    
    # Summary
    success = [r for r in results if r['code'] == 0]
    failures = [r for r in results if r['code'] != 0]
    total_found = 0
    total_passed = 0
    for r in success:
        try:
            parts = r['output'].split()
            for p in parts:
                if p.startswith('found='):
                    total_found += int(p.split('=')[1])
                if p.startswith('passed='):
                    total_passed += int(p.split('=')[1])
        except Exception:
            pass
    
    print(f'[{datetime.now().strftime("%H:%M:%S")}] 全部完成，总耗时={overall_elapsed:.1f}s')
    print(f'FINAL_SUMMARY: total_tasks={len(task_ids)} success={len(success)} failures={len(failures)} total_found={total_found} total_passed={total_passed}')
    for r in failures:
        print(f'FAILURE: task_id={r["task_id"]} output={r["output"]}')
