import discord
import datetime
from typing import Union
from discord.ext.commands import Context


async def atry_catch(func, *args, catch=Exception, ret=False, **kwargs):
    try:
        return await discord.utils.maybe_coroutine(func, *args, **kwargs)
    except catch as e:
        return e if ret else None


def try_catch(func, *args, catch=Exception, ret=False, **kwargs):
    try:
        return func(*args, **kwargs)
    except catch as e:
        return e if ret else None


class BaseEmbed(discord.Embed):
    def __init__(self, color=0xffcccb, timestamp=datetime.datetime.utcnow(), **kwargs):
        super(BaseEmbed, self).__init__(color=color, timestamp=timestamp, **kwargs)

    @classmethod
    def default(cls, ctx: Union[discord.Message, Context], **kwargs):
        instance = cls(**kwargs)
        instance.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        return instance

    @classmethod
    def to_error(cls, color=discord.Color.red(), **kwargs):
        return cls(color=color, **kwargs)