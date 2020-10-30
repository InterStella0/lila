from __future__ import annotations
import discord
import datetime
import asyncio
from typing import Union
from discord.ext.commands import Context
from discord.ext import menus
from functools import partial, wraps
from io import BytesIO

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


class ReactionAction(menus.Menu):
    def __init__(self, reactions, *, timeout=60.0,  **kwargs):
        super().__init__(timeout=timeout, **kwargs)
        self.reactions = reactions
        self.create_buttons(reactions)

    @property
    def reactions(self):
        return self._reactions

    @reactions.setter
    def reactions(self, value):
        try:
            iter(value)
        except TypeError:
            raise TypeError('invalid type for reactions: expected iterable, got {}'.format(type(value)))
        if not len(value) or len(value) > 20:
            raise ValueError(f'len(reactions) must be 0 < x <= 20: got {len(value)}')
        self._reactions = value

    def create_buttons(self, reactions):
        # override if you want button to do something different
        try:
            for index, emoji in enumerate(reactions):
                # each button calls `self.button_response(payload)` so you can do based on that
                def callback(items):
                    async def inside(self, payload):
                        await self.button_response(payload, **items)
                        self.stop()
                    return inside
                self.add_button(menus.Button(emoji, callback(reactions[emoji]), position=menus.Position(index)))
        except IndexError:
            pass

    async def button_response(self, *args, **kwargs):
        # should be overwritten for subclasses or pass
        raise NotImplementedError


class MenuPrompt(ReactionAction):
    def __init__(self, reactions, **kwargs):
        super().__init__(reactions, **kwargs)
        self.response = None

    async def button_response(self, payload, **kwargs):
        await self.message.edit(**kwargs)
        self.response = list(self.reactions).index(str(payload.emoji))

    async def finalize(self, timed_out):
        if timed_out:
            self.response = None


async def prompt(ctx, message=None, predicate=None, *, timeout=60, error="{} seconds is up",
                 event_type="message", responses=None, delete_after=False):
    bot = ctx.bot
    prompting = await ctx.send(**message or responses and responses.pop(message))
    if event_type != "reaction_add":
        respond = await atry_catch(bot.wait_for, event_type, check=predicate, timeout=timeout)
    else:
        menu = MenuPrompt(responses, message=prompting, delete_message_after=delete_after, check_embeds=True)
        await menu.start(ctx, wait=True)
        respond = menu.response
    if respond is None:
        await prompting.edit(content=None,
                             embed=BaseEmbed.to_error(title="Timeout",
                                                      description=error.format(timeout)))
    else:
        return respond if event_type != "reaction_add" else not respond


async def remove_reaction_handler(message):
    bot_member = message.guild.me
    if message.guild:
        if bot_member.permissions_in(message.channel).manage_messages:
            return await atry_catch(message.clear_reactions)

    [await r.remove(bot_member) for r in message.reactions if r.me]


def make_async(executor=None):
    def wrapped(func):
        @wraps(func)
        def function(*args, **kwargs):
            thing = partial(func, *args, **kwargs)
            loop = asyncio.get_event_loop()
            return loop.run_in_executor(executor, thing)
        return function
    return wrapped


class BaseEmbed(discord.Embed):
    def __init__(self, color=0xffcccb, timestamp=datetime.datetime.utcnow(), **kwargs):
        super().__init__(color=color, timestamp=timestamp, **kwargs)

    @classmethod
    def default(cls, ctx: Union[discord.Message, Context], **kwargs) -> BaseEmbed:
        instance = cls(**kwargs)
        instance.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.avatar_url)
        return instance

    @classmethod
    def to_error(cls, color=discord.Color.red(), **kwargs) -> BaseEmbed:
        return cls(color=color, **kwargs)

    @classmethod
    def invite(cls, ctx, game, invited=None, status=True, invitation=None, **kwargs) -> dict:
        color = {True: ctx.bot.positive_color,
                 False: ctx.bot.error_color,
                 None: ctx.bot.color}
        status_app = {"content": None,
                      "embed":
                          cls.default(
                            ctx,
                            title=f"{game} Game invitation {ctx.bot.INVITE_REACT[status]}",
                            description=invitation or f"{invited} has {('', 'dis')[not status]}approved the invitation.",
                            color=color[status],
                                  **kwargs)
                      }
        return status_app

    @classmethod
    def board(cls, message, color, bytes_obj, file_name, **kwargs) -> dict:
        bytes_obj.seek(0)
        file = discord.File(bytes_obj, filename=f"{file_name}.png")
        embed = cls(color=color, timestamp=datetime.datetime.utcnow(), **kwargs)
        embed.set_image(url=f"attachment://{file.filename}")
        content = {"content": message,
                   "embed": embed,
                   "file": file
                   }
        return content