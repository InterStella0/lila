import discord
from discord.ext import commands
from utils.useful import prompt, BaseEmbed
from utils.converters import Player


class CasualGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.INVITATION = "{0.mention}, {1.author} has invited you to play {2}"

    @commands.command()
    async def connect4(self, ctx, player2: Player):
        GAME = "Connect 4"

        message = BaseEmbed.invite(ctx, GAME, status=None, invitation=self.INVITATION.format(player2, ctx, GAME))
        message["content"] = player2.mention
        responses_text = tuple(BaseEmbed.invite(ctx, GAME, status=not x, invited=player2) for x in range(2))  # first is approve, second disapprove
        responses = {ctx.bot.INVITE_REACT[1 - x]: y for x, y in zip(range(2), responses_text)}
        self.bot.global_player.add(ctx, [player2.id], GAME)
        error = f"Looks like {{}} seconds is up! Sorry {ctx.author}, You will have to request for another one"
        respond = await prompt(ctx, message=message, event_type="reaction_add", responses=responses, error=error)
        await ctx.send(str(respond))


def setup(bot):
    bot.add_cog(CasualGames(bot))