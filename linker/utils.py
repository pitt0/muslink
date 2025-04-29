import asyncio
import json
from functools import wraps


def loop(seconds: int = 60):
    def inner(func):
        @wraps(func)
        async def runner(*args, **kwargs):
            while True:
                func(*args, **kwargs)
                await asyncio.sleep(seconds)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return asyncio.create_task(runner(*args, **kwargs))

        return wrapper

    return inner


def read(fp: str) -> dict:
    with open(fp) as f:
        return json.load(f)
