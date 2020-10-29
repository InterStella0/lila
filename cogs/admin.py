import discord
import re
from discord.ext import commands
from utils.converters import ValidPrefix
from utils.useful import BaseEmbed
from discord.ext.commands import BotMissingPermissions, CooldownMapping, BucketType, CommandOnCooldown


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.global_cooldown = CooldownMapping.from_cooldown(1, 5, BucketType.user)
        self.PREFIX_UPDATE = """UPDATE prefixes 
                                SET prefixes= {}
                                WHERE snowflake_id=$1"""

    @commands.check
    async def check_perms(self, ctx):
        bucket = self.global_cooldown.get_bucket(ctx.message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            raise CommandOnCooldown(bucket, retry_after)
        if ctx.guild.me.guild_permissions.embed_links:
            return True
        raise BotMissingPermissions("embed_links")

    @commands.Cog.listener()
    async def on_message(self, message):
        if re.fullmatch("<@(!?)771054549775417344>", message.content):
            prefixes = await self.bot.get_prefix(message)
            str_prefix = "`, `".join(prefixes) if isinstance(prefixes, set) else prefixes
            return await message.channel.send(embed=BaseEmbed.default(message,
                                                                      title="Current prefix in here",
                                                                      description=f"My prefixes is `{str_prefix}`"))
        await self.bot.process_commands(message)

    @commands.group(invoke_without_command=True)
    async def prefix(self, ctx):
        prefixes = await self.bot.get_prefix(ctx.message)
        str_prefix = "`, `".join(prefixes) if isinstance(prefixes, set) else prefixes
        await ctx.send(embed=BaseEmbed.default(ctx,
                                               title="Current prefix in here",
                                               description=f"My prefixes is `{str_prefix}`"))

    @prefix.command(name="add", aliases=["+", "ad", "adds", "added"])
    async def _add(self, ctx, new_prefix: ValidPrefix):
        snowflake = ctx.guild.id if ctx.guild and ctx.author.guild_permissions.administrator else ctx.author.id
        if new_prefix not in self.bot.cache_prefix[snowflake]:
            values = (snowflake, [new_prefix])
            await self.bot.pg_con.execute(self.PREFIX_UPDATE.format("prefixes || $2"), *values)
        self.bot.cache_prefix[snowflake] = self.bot.cache_prefix[snowflake].union({new_prefix})
        prefix = "`, `".join(self.bot.cache_prefix[snowflake])
        await ctx.send(embed=BaseEmbed.default(ctx,
                                               title="Prefix Addition",
                                               description=f"Current new prefix is `{prefix}`"))

    @prefix.command(name="remove", aliases=["del", "-", "deletes", "delete", "rem", "removes", "removed"])
    async def _remove(self, ctx, del_prefix: ValidPrefix(del_mode=True)):
        snowflake = ctx.guild.id if ctx.guild and ctx.author.guild_permissions.administrator else ctx.author.id
        self.bot.cache_prefix[snowflake].discard(del_prefix)
        values = (snowflake, self.bot.cache_prefix[snowflake])
        await self.bot.pg_con.execute(self.PREFIX_UPDATE.format("$2"), *values)
        await ctx.send(embed=BaseEmbed.default(ctx,
                                               title="Prefix Deletion",
                                               description=f"Current prefix is `{'`, `'.join(self.bot.cache_prefix[snowflake])}`"))


def setup(bot):
    bot.add_cog(Admin(bot))
