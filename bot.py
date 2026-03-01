import discord
from discord.ext import commands
import os

TOKEN = os.environ["TOKEN"]

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} がログインしました")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

bot.run(TOKEN)