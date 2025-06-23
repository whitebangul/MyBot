import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Intents: required to read message content
intents = discord.Intents.default()
intents.message_content = True

# Define your custom bot class
class MyBot(commands.Bot):
    async def setup_hook(self):
        # Load your cogs
        await self.load_extension("cogs.dice")
        await self.load_extension("cogs.poker")
        await self.load_extension("cogs.store")
        await self.load_extension("cogs.blackjack")

# Create an instance of the bot using your custom class
bot = MyBot(command_prefix="-", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name=""))

# Run the bot
bot.run(TOKEN)
