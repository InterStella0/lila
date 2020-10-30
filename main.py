import discord
import asyncpg
import time
import datetime
from discord.ext import commands
from os.path import join, dirname
from dotenv import load_dotenv
from os import environ
from utils.useful import try_catch
from utils.game_classes import GlobalPlayers

dotenv_path = join(dirname(__file__), "bot_settings.env")
load_dotenv(dotenv_path)


class LilaBot(commands.Bot):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        super().__init__(command_prefix=self.get_prefix, **kwargs)

    @property
    def stella(self):
        return self.get_user(self.owner_id)

    async def db_fill(self):
        prefixes = await self.pg_con.fetch("SELECT * FROM prefixes")
        self.cache_prefix = {data["snowflake_id"]: set(data["prefixes"]) for data in prefixes}

    def load_cog(self):
        for cog in self.loading_cog:
            ext = "cogs." if cog != "jishaku" else ""
            if error := try_catch(self.load_extension, f"{ext}{cog}"):
                print("Error while loading:", cog, "\n", error)
            else:
                print(cog, "is now loaded")

    async def get_prefix(self, message):
        query = "INSERT INTO prefixes VALUES ($1, $2) ON CONFLICT (snowflake_id) DO NOTHING"
        cur_prefix = {self.default_prefix}
        if message.author.id in self.cache_prefix:
            cur_prefix = cur_prefix.union(self.cache_prefix[message.author.id])
        else:
            await self.pg_con.execute(query, message.author.id, [self.default_prefix])
            self.cache_prefix.update({message.author.id: {self.default_prefix}})

        if message.guild:
            if message.guild.id in self.cache_prefix:
                cur_prefix = cur_prefix.union(self.cache_prefix[message.guild.id])
            else:
                await self.pg_con.execute(query, message.guild.id, [self.default_prefix])
                self.cache_prefix.update({message.guild.id: {self.default_prefix}})
        return cur_prefix

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
            self.loop.run_until_complete(self.db_fill())
            self.load_cog()
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
            "loading_cog": ("admin", "jishaku", "casual_games"),
            "error_color": 0xF67280,
            "positive_color": 0xDCEDC2,
            "INVITE_REACT": {True: "<:checkmark:753619798021373974>", False: "<:crossmark:753620331851284480>", None: ""},
            "global_player": GlobalPlayers()
            }
list_Nones = ["cache_prefix", "uptime", "pg_con"]
bot_data.update(dict.fromkeys(list_Nones))
bot = LilaBot(**bot_data)


@bot.event
async def on_connect():
    bot.connected = datetime.datetime.utcnow()
    print("Online: ", bot.connected)

@bot.event
async def on_message(message):
    # on_message event is handled in admin cog
    return


@bot.event
async def on_ready():
    print("Cache is ready")

bot.starter()
