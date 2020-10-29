import discord
import datetime
import asyncio
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


async def prompt(ctx, message, predicate, timeout=60, app=None, disapp=None, error="{} second is up",
                 event_type="message", reactions=()):
    bot = ctx.bot
    if not reactions:
        reactions = ctx.bot.INVITE_REACT
    prompting = await ctx.send(**message)
    if event_type == "reaction_add":
        for reaction in reactions:
            await prompting.add_reaction(reaction)
    try:
        respond = await bot.wait_for(event_type, check=predicate, timeout=timeout)
        if event_type == "message":
            return respond

        reaction, user = respond
        # 1st element will always be "approve" while 2nd will be "disapprove"
        await prompting.edit(**(app, disapp)[reactions.index(str(reaction))])

    except asyncio.TimeoutError:
        await ctx.send(embed=BaseEmbed.to_error(ctx,
                                                title="Timeout",
                                                description=error.format(timeout)))


class BaseEmbed(discord.Embed):
    def __init__(self, color=0xffcccb, timestamp=datetime.datetime.utcnow(), **kwargs):
        super().__init__(color=color, timestamp=timestamp, **kwargs)

    @classmethod
    def default(cls, ctx: Union[discord.Message, Context], **kwargs):
        instance = cls(**kwargs)
        instance.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        return instance

    @classmethod
    def to_error(cls, color=discord.Color.red(), **kwargs):
        return cls(color=color, **kwargs)

    @classmethod
    def invite(cls, ctx, game, invited=None, status=True, invitation=None, **kwargs):
        color = {True: ctx.bot.positive_color,
                 False: ctx.bot.error_color,
                 None: ctx.bot.color}
        status_app = {"content": None,
                      "embed":
                          cls.default(
                            ctx,
                            title=f"{game} Game invitation {ctx.bot.INVITE_REACT[status]}",
                            description=invitation or f"{invited} has {('', 'dis')[status]}approved the invitation.",
                            color=color[status]
                                  ** kwargs)}
        return status_app
