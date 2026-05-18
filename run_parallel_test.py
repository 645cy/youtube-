import subprocess, sys, os, time, json

def run_task(task_id):
    env = os.environ.copy()
    env['DATABASE_URL'] = 'sqlite+aiosqlite:///D:/Projects/YouTube/tubefactory-ocp/data/tubefactory.db'
    try:
        proc = subprocess.run(
            [sys.executable, 'run_single.py', str(task_id)],
            cwd='D:\\Projects\\YouTube\\tubefactory-ocp',
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        return {'task_id': task_id, 'code': proc.returncode, 'output': proc.stdout.strip()}
    except subprocess.TimeoutExpired:
        return {'task_id': task_id, 'code': -1, 'output': 'TIMEOUT'}
    except Exception as e:
        return {'task_id': task_id, 'code': -1, 'output': f'ERROR: {e}'}

if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor
    task_ids = [15, 16, 17, 18, 19]
    start = time.time()
    with ProcessPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(run_task, task_ids))
    elapsed = time.time() - start
    print(f'ELAPSED: {elapsed:.1f}s')
    for r in results:
        print(f'TASK {r["task_id"]}: code={r["code"]} output={r["output"]}')
