import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure


class InvalidPrefix(CheckFailure):
    def __init__(self, argument):
        super().__init__(self, argument)

