import asyncio
from functools import update_wrapper


def coroutine(fn):
    fn = asyncio.coroutine(fn)

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(fn(loop, *args, **kwargs))

    return update_wrapper(wrapper, fn)
