import discord
from discord.ext import commands
from utils.useful import prompt, BaseEmbed
from utils.converters import Player
from utils import game_classes
from typing import Union


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
        game = self.bot.global_player.add(ctx, [player2.id], game_classes.Connect4)
        error = f"Looks like {{}} seconds is up! Sorry {ctx.author}, You will have to request for another one"
        respond = await prompt(ctx, message=message, event_type="reaction_add", responses=responses, error=error)
        if not respond:
            self.bot.global_player.remove(game)
            return
        game.status = True

        def check_turn(game):
            def predicate(m):
                checking = (m.author == game.current_player,
                            m.content.isdigit() and 1 <= int(m.content.isdigit()) <= game.cols
                            )

                return all(checking)
            return predicate

        async def connect4_prompt(game):
            display = await game.render_board()
            player = game.current_player
            description = f"{player}, It's your turn. Please choose a column between 1 to 7."
            message = BaseEmbed.board(player.mention, game.color, display, "connect_4",
                                      title="Connect 4", description=description)
            error = f"{{}} seconds is up. Looks like {game.last_player} wins"
            return await prompt(ctx, message=message, predicate=check_turn(game), error=error, delete_after=True)

        while response := await connect4_prompt(game):
            game.insert(int(response.content) - 1)




def setup(bot):
    bot.add_cog(CasualGames(bot))