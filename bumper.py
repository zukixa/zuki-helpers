import discord
from discord.ext import commands, tasks
import json

description = """An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here."""

bot = commands.Bot(command_prefix="?", description=description, self_bot=True)

with open("config.json", "r") as f:
    config = json.load(f)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    ping_loop.start()


@tasks.loop(hours=2.01)
async def ping_loop():
    channel = await bot.fetch_channel(1090022628946886729)
    # Replace with the channel where you want to send the message
    # ctx = await bot.get_context()

    async for cmd in channel.slash_commands():
        print(cmd)
        if str(cmd) == "bump":
            await cmd.__call__()
    await channel.send("pong")


@bot.command()
async def ping(ctx):
    """Says if a user is cool.

    In reality this just checks if a subcommand is being invoked.
    """
    async for cmd in ctx.channel.slash_commands():
        print(cmd)
        if str(cmd) == "cat":
            await cmd.__call__()
    await ctx.send("pong")


bot.run(config["bumper_token"])
