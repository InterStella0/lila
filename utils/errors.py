import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure, UserInputError


class InvalidPrefix(CheckFailure):
    def __init__(self, argument):
        super().__init__(argument)


class CurrentlyPlaying(CheckFailure):
    def __init__(self, argument, user_playing, game):
        super().__init__(argument)
        self.user_playing = user_playing
        self.game = game


class AnotherGame(CheckFailure):
    def __init__(self, author_id):
        super().__init__(message="{} is already playing. This isn't possible.".format(author_id))


class Connect4ColumnFull(UserInputError):
    def __init__(self, player, column):
        super().__init__(message="{}, column number {} is full! Choose another column.".format(player, column))
        self.player = player
        self.column = column

