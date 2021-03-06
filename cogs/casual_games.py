import discord
import asyncio
import datetime
from discord.ext import commands
from utils.useful import prompt, BaseEmbed, atry_catch
from utils.converters import Player
from utils.errors import CurrentlyPlaying, Connect4ColumnFull
from utils import game_classes
from discord.utils import maybe_coroutine
from typing import Union


class CasualGames(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.INVITATION = "{0.mention}, **{1.author}** has invited you to play `{2}`"

    async def cog_check(self, ctx):
        # lock the user from making another game while in game or while requesting a game
        if game := ctx.bot.global_player.get_player(ctx.author.id):
            argument = f"You are currently waiting for a request of `{game}` game. You cannot request another game until this ends.", ctx.author, game
            if game.status:
                argument = f"You are currently playing `{game}`. You cannot request another game until this ends.", ctx.author, game

            raise CurrentlyPlaying(*argument)
        return True

    @commands.command()
    @commands.guild_only()
    async def connect4(self, ctx, player2: Player):
        GAME = "Connect 4"
        message = BaseEmbed.invite(ctx, GAME, status=None, invitation=self.INVITATION.format(player2, ctx, GAME))
        message["content"] = player2.mention
        responses_text = tuple(BaseEmbed.invite(ctx, GAME, status=not x, invited=player2) for x in range(2))  # first is approve, second disapprove
        responses = {ctx.bot.INVITE_REACT[1 - x]: y for x, y in zip(range(2), responses_text)}
        game = self.bot.global_player.add(ctx, [player2.id], game_classes.Connect4)
        error = f"Looks like {{}} seconds is up! Sorry **{ctx.author}**, You will have to request for another one"
        respond = await prompt(ctx, message=message, event_type="reaction_add", responses=responses, error=error,
                               target_id={player2.id})
        if not respond:
            self.bot.global_player.remove(game)
            return
        game.status = True

        def check_turn(game):
            def predicate(m):
                checking = (m.author in (game.current_player, self.bot.stella),
                            m.content.isdigit() and 1 <= int(m.content) <= game.cols)
                return all(checking)
            return predicate

        async def connect4_prompt(game, message=None):
            if not message:
                display = await game.render_board()
                player = game.current_player
                description = f"`{player}`, It's your turn. Please choose a column between `1` to `7`."
                message = BaseEmbed.board(player.mention, game.color, display, "connect_4",
                                          title="Connect 4", description=description)
            error = f"`{{}}` seconds is up. Looks like `{game.last_player}` wins"
            return await prompt(ctx, message=message, predicate=check_turn(game), error=error, delete_after=True, ret=True,
                                delete_timeout=True)

        message_sent = None
        while response := await connect4_prompt(game, message_sent):
            if isinstance(response, discord.Message):
                message_sent = None
                if game_result := await atry_catch(game.insert, int(response.content) - 1, ret=True):
                    if not isinstance(game_result, Connect4ColumnFull):
                        await ctx.send(**game_result)
                        break
                    else:
                        message_sent = {"embed": BaseEmbed.to_error(title="Connect 4",
                                                                    description=str(game_result))}
            elif isinstance(response, asyncio.TimeoutError):
                game.ended_at = datetime.datetime.utcnow()
                break
        print(game.moves)
        self.bot.global_player.remove(game)


def setup(bot):
    bot.add_cog(CasualGames(bot))