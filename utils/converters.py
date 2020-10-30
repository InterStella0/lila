import discord
from discord.ext import commands
from utils.errors import InvalidPrefix, CurrentlyPlaying


class ValidPrefix(commands.Converter):
    def __init__(self, del_mode=False):
        self.del_mode = del_mode

    async def convert(self, ctx, argument):
        if len(argument) <= 10:
            return argument

        if not self.del_mode:
            raise InvalidPrefix(f"`{argument}` is bigger than 10 characters.")

        snowflake = ctx.guild.id if ctx.guild and ctx.author.guild_permissions.administrator else ctx.author.id
        prefix = ctx.bot.cache_prefix[snowflake]
        if argument in prefix:
            return argument
        else:
            process_prefix = "`, `".join(prefix) if isinstance(prefix, set) else prefix
            raise InvalidPrefix(f"`{argument}` does not exist in your prefix list. "
                                f"Your current prefix list is {process_prefix}")


class Player(commands.MemberConverter):
    async def convert(self, ctx, argument):
        member = await super().convert(ctx, argument)
        if game := ctx.bot.global_player.get_player(member.id):
            raise CurrentlyPlaying(f"{member} is currently playing {game}", member, game)
        return member

