import discord
import asyncpg
import time
import datetime
from discord.ext import commands
from os.path import join, dirname
from dotenv import load_dotenv
from os import environ
from utils.useful import try_catch

dotenv_path = join(dirname(__file__), "bot_settings.env")
load_dotenv(dotenv_path)


class LilaBot(commands.Bot):
    def __init__(self, attrs, **kwargs):
        super().__init__(command_prefix=self.get_prefix, **kwargs)
        self.__dict__.update({attr: kwargs[attr] if attr in kwargs else None for attr in attrs})
        self.uptime = None
        self.pg_con = None

    @property
    def stella(self):
        return self.get_user(self.owner_id)

    async def db_fill(self):
        prefixes = await self.pg_con.fetch("SELECT * FROM prefixes")
        self.cache_prefix = dict(prefixes)

    async def get_prefix(self, message):
        return "?uwu "

    def starter(self):
        try:
            print("Connecting to database...")
            start = time.time()
            loop_pg = self.loop.run_until_complete(asyncpg.create_pool(database=self.db,
                                                                       user=self.user_db,
                                                                       password=self.pass_db))
            print(f"Connected to the database ({time.time() - start})s")
        except Exception as e:
            print("Could not connect to database.")
            print(e)
            return
        else:
            self.uptime = datetime.datetime.utcnow()
            self.pg_con = loop_pg
            print("Bot running...   (", self.uptime, ")")
            self.run(self.token)


intents = discord.Intents.default()
intents.typing = False
intents.members = True

bot_data = {"intents": intents,
            "color": 0xFFB5E8,
            "token": environ.get("TOKEN"),
            "tester": bool(environ.get("TESTER")),
            "default_prefix": environ.get("PREFIX"),
            "db": environ.get("DATABASE"),
            "user_db": environ.get("USER"),
            "pass_db": environ.get("PASSWORD"),
            "owner_id": 591135329117798400,
            "attrs": ["color", "token", "tester", "default_prefix", "cache_prefix", "user_db", "pass_db", "db"]
            }

bot = LilaBot(**bot_data)


@bot.event
async def on_connect():
    bot.connected = datetime.datetime.utcnow()
    print("Online: ", bot.connected)


@bot.event
async def on_ready():
    print("Cache is ready")

bot.starter()
