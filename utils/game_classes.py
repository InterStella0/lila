import datetime
from utils.errors import AnotherGame


class GlobalPlayers:
    def __init__(self):
        # Author will have the Game object
        # While the player will point to the author's id
        self.games = {}

    def get_player(self, player_id):
        if player_id in self.games:
            game = self.games[player_id]
            if isinstance(game, int):
                return self.games[game]
            else:
                return game

    def add(self, ctx, players_id, game):
        if ctx.author.id in self.games:
            raise AnotherGame(ctx.author.id) # if coded correctly, this isn't possible to hit
        new_game = Game(ctx, players_id, game, False)
        self.games.update({ctx.author.id: new_game})
        for player_id in players_id:
            if player_id in self.games:
                raise AnotherGame(player_id)
            self.games.update({player_id: ctx.author.id})


class Game:
    def __init__(self, ctx, players_id: list, game: str, status: bool):
        self.ctx = ctx
        self.created_at = datetime.datetime.utcnow()
        self.author_id = ctx.author.id
        self.players_id = players_id
        self.game = game
        self.status = status

    @property
    def author(self):
        return self.ctx.bot.get_user(self.author_id)

    @property
    def players(self):
        return [self.ctx.bot.get_user(player_id) for player_id in self.players_id]

    def __contains__(self, player):
        auth, players = (self.author_id, self.players_id) if isinstance(player, int) else (self.author, self.players)
        return player in players or player == auth

    def __str__(self):
        return self.game
