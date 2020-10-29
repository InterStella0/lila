import discord
from discord.ext import commands
from utils.useful import prompt, BaseEmbed
from utils.converters import Player


class CasualGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.INVITATION = "{0.mentions}, {1.author} has invited you to play {2}"

    @commands.command()
    async def connect4(self, ctx, player2: Player):
        GAME = "Connect 4"

        def check(reaction, user):
            return str(reaction) in self.bot.INVITE_REACT and user == player2

        message = BaseEmbed.invite(ctx, GAME, status=None, invitation=self.INVITATION.format(player2, ctx, GAME))
        message["content"] = player2.mention
        approved = BaseEmbed.invite(ctx, GAME)
        disapproved = BaseEmbed.invite(ctx, GAME, status=False)
        if not await prompt(ctx, message, check, "reaction_add", app=approved, disapp=disapproved):
            return


def setup(bot):
    bot.add_cog(CasualGames(bot))