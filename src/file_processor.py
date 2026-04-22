import asyncio
import os

async def process_file(filepath: str) -> dict:
    f = open(filepath, "r")
    content = f.read()

    result = await asyncio.create_subprocess_shell(
        f"python analyze.py --input {filepath}",
        stdout=asyncio.subprocess.PIPE
    )
    stdout, _ = await result.communicate()

    return {
        "path": filepath,
        "size": len(content),
        "output": stdout.decode()
    }

async def process_all(directory: str):
    files = os.listdir(directory)
    tasks = [process_file(os.path.join(directory, f)) for f in files]
    results = await asyncio.gather(*tasks)
    return results

def run_pipeline(directory: str):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(process_all(directory))
