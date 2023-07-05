import requests
import discord
from discord.ext import commands, tasks
import json

bot = commands.Bot(command_prefix="?", self_bot=True)
with open("config.json", "r") as f:
    config = json.load(f)

# Dictionary to store ping loop information for each channel
ping_loops = {}


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    for channel_id in config["ping_channels"]:
        # Start ping loop for each configured channel
        ping_loops[channel_id] = ping_loop.start()
    await bot.change_presence(activity=discord.Game(name="Ping Loops"))


@tasks.loop(minutes=122)
async def ping_loop():
    for channel_id in config["ping_channels"]:
        channel = await bot.fetch_channel(channel_id)
        async for cmd in channel.slash_commands():
            print(cmd)
            if str(cmd) == "bump":
                await cmd.__call__()
        await channel.send("pong")


@bot.event
async def on_message(message):
    if message.author != bot.user:
        return

    if message.content.startswith("$start"):
        await start(message.channel)
    if message.content.startswith("$stop"):
        await stop(message.channel)
    if message.content.startswith("$inv"):
        print("hello")
        await invite(message.channel, message.content[5:])


async def start(channel):
    # Fetch the text channel where the ping loop should run
    # Store the channel ID in the config
    config["ping_channels"].append(channel.id)
    ping_loops[channel.id] = ping_loop.start()
    await channel.send(f"Ping loop started for {channel.guild.name}.")


async def stop(channel):
    # Stop the ping loop and remove the channel from the config
    ping_loops[channel.id].stop()
    config["ping_channels"].remove(channel.id)
    await channel.send(f"Ping loop stopped for {channel.guild.name}.")


async def invite(channel, invite_url):
    # Extract the last part of the invite URL
    print("hola como sa")
    print(invite_url)
    invite_code = invite_url.split("/")[-1]
    print(invite_code)
    # Construct the invite URL with the extracted code and bumper token
    invite_url = f"https://discordapp.com/api/v9/invites/{invite_code}"

    # Make a POST request to the invite URL with the authorization header
    headers = {"Authorization": config["bumper_token"]}
    response = requests.post(invite_url, headers=headers)
    print(response)
    if response.status_code == 200:
        await channel.send("Invite sent successfully.")
    else:
        await channel.send("Failed to send invite.")


bot.run(config["bumper_token"])
