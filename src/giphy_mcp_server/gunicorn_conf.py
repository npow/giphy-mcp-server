import asyncio


def post_fork(server, worker):
    """Reset asyncio state in each worker after fork."""
    try:
        loop = asyncio.get_event_loop()
        if not loop.is_closed():
            loop.close()
    except Exception:
        pass
    asyncio.set_event_loop(asyncio.new_event_loop())
