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


async def prompt(ctx, message, predicate, *, timeout=60, app=None, disapp=None, error="{} seconds is up",
                 event_type="message", reactions=()):
    bot = ctx.bot
    prompting = await ctx.send(**message)
    if event_type == "reaction_add":
        reactions = tuple(ctx.bot.INVITE_REACT[x] for x in range(2))
        for reaction in reactions:
            await prompting.add_reaction(reaction)
    try:
        respond = await bot.wait_for(event_type, check=predicate, timeout=timeout)
        if event_type == "message":
            return respond

        reaction, user = respond
        # 1st element will always be "approve" while 2nd will be "disapprove"
        result = reactions.index(str(reaction))
        await prompting.edit(**(app, disapp)[result])
        return not result
    except asyncio.TimeoutError:
        await prompting.edit(content=None,
                             embed=BaseEmbed.to_error(title="Timeout",
                                                      description=error.format(timeout)))
        event_type == "reaction_add" and await remove_reaction_handler(prompting)


async def remove_reaction_handler(message):
    if message.guild:
        if message.guild.me.permissions_in(message.channel).manage_messages:
            await message.clear_reactions()
            return
    [await reaction.remove(message.guild.me) for reaction in message.reactions if reaction.me]


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
                            color=color[status],
                                  **kwargs)}
        return status_app
