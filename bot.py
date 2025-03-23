import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# load .env
load_dotenv()
TOKEN = os.getenv("TOKEN")

# intents
intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    async def setup_hook(self):
       await self.load_extension("cogs.dice")

bot = MyBot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name=""))

bot.run(TOKEN)