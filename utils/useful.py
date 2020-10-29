import discord


async def atry_catch(func, catch=Exception, ret=False, *args, **kwargs):
    try:
        return await discord.utils.maybe_coroutine(func, *args, **kwargs)
    except catch as e:
        return e if ret else None


def try_catch(func, catch=Exception, ret=False, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except catch as e:
        return e if ret else None
