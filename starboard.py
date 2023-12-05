import discord
from discord.ext import commands
from discord.app_commands import Choice
import math
import discord
from discord.ext import commands, tasks
import json
import asyncio
from discord.ext import commands, tasks
from discord import app_commands
from discord.app_commands import Choice
import json

with open("config.json", "r") as f:
    config = json.load(f)


def load_starboard_config():
    try:
        with open("starboard.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_starboard_config(config):
    with open("starboard.json", "w") as f:
        json.dump(config, f)


starboard_config = load_starboard_config()
intents = discord.Intents.all()


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


if __name__ == "__main__":
    intents = discord.Intents.all()
    client = MyClient(intents=intents)


async def star_reaction_check(reaction):
    if (
        reaction.emoji == "⭐"
        and reaction.count
        >= starboard_config[str(reaction.message.guild.id)]["starboard_threshold"]
        and reaction.message.channel.id
        in starboard_config[str(reaction.message.guild.id)]["watched_channels"]
    ):
        return True
    return False


@client.event
async def on_ready():
    print(f"Logged in as: {client.user}")
    act = discord.Activity(
        name="stars across the galaxy ~", type=discord.ActivityType.watching
    )
    await client.change_presence(status=discord.Status.idle, activity=act)


async def create_star_embed(reaction):
    embed = discord.Embed(
        title="Starred Message", description=reaction.message.content, color=0xFFD700
    )
    embed.set_author(
        name=reaction.message.author.display_name,
        icon_url=reaction.message.author.avatar.url,
    )
    embed.set_footer(text=f"Stars: {reaction.count - 1}")
    embed.add_field(
        name="Origin",
        value=f"[Jump to message]({reaction.message.jump_url})",
        inline=False,
    )
    return embed


async def find_starboard_message(reaction):
    starboard_channel = client.get_channel(
        starboard_config[str(reaction.message.guild.id)]["starboard_channel_id"]
    )
    msgs = [message async for message in starboard_channel.history(limit=None)]

    for msg in msgs:
        if msg.embeds:
            embed = msg.embeds[0]
            if embed.fields:
                if (
                    "Jump to message" in embed.fields[0].value
                    and reaction.message.jump_url in embed.fields[0].value
                ):
                    return msg
    return None


@client.event
async def on_reaction_add(reaction, user):
    if user == client.user:  # Ignore the bot's own reaction
        return

    if await star_reaction_check(reaction):
        starboard_channel = client.get_channel(
            starboard_config[str(reaction.message.guild.id)]["starboard_channel_id"]
        )
        message_in_starboard = await find_starboard_message(reaction)
        print(message_in_starboard)
        if message_in_starboard:
            embed = message_in_starboard.embeds[0]
            embed.set_footer(text=f"Stars: {reaction.count - 1}")
            await message_in_starboard.edit(
                embed=embed
            )  # Update the stars count in the existing starboard message
        else:
            embed = await create_star_embed(reaction)
            await starboard_channel.send(
                embed=embed
            )  # Create a new embed for the message


@client.event
async def on_message(message):
    if message.author.id == client.user.id or message.author.bot:
        return

    if (
        message.channel.id
        in starboard_config[str(message.guild.id)]["watched_channels"]
        and not starboard_config[str(message.guild.id)]["disable_autoreact"]
    ):
        await message.add_reaction("⭐")
    # this is purely for zukijourney server application, i could not bother to make another bot just for the code below.
    # ignore this if you want to use it for your own work !
    exluded = [1099481191679283250]
    channel = message.channel

    if channel.id not in exluded:
        if "discord.gg/" in message.content:
            await message.delete()
            await channel.send(
                f"{message.author.mention} You are not allowed to send discord invites here.",
                delete_after=5,
            )


@client.tree.command(name="board", description="Set the starboard channel")
@app_commands.default_permissions(administrator=True)
async def set_starboard(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer()
    guild_id = str(interaction.guild.id)
    if guild_id not in starboard_config:
        starboard_config[guild_id] = {}
    starboard_config[guild_id]["starboard_channel_id"] = channel.id
    save_starboard_config(starboard_config)
    await interaction.followup.send(f"Starboard channel set to: {channel.mention}")


@client.tree.command(name="watch", description="Add a channel to be watched")
@app_commands.default_permissions(administrator=True)
async def add_watched_channel(
    interaction: discord.Interaction, channel: discord.TextChannel
):
    await interaction.response.defer()
    guild_id = str(interaction.guild.id)
    if guild_id not in starboard_config:
        starboard_config[guild_id] = {}
    starboard_config[guild_id]["watched_channels"].append(channel.id)
    save_starboard_config(starboard_config)
    await interaction.followup.send(
        f"Added channel {channel.mention} to watched channels."
    )


@client.tree.command(name="delwatch", description="Remove a channel from being watched")
@app_commands.default_permissions(administrator=True)
async def remove_watched_channel(
    interaction: discord.Interaction, channel: discord.TextChannel
):
    await interaction.response.defer()
    guild_id = str(interaction.guild.id)
    if guild_id not in starboard_config:
        starboard_config[guild_id] = {}
    starboard_config[guild_id]["watched_channels"].remove(channel.id)
    save_starboard_config(starboard_config)
    await interaction.followup.send(
        f"Removed channel {channel.mention} to watched channels."
    )


@client.tree.command(name="minstar", description="Set the star reaction threshold")
@app_commands.default_permissions(administrator=True)
async def set_star_threshold(interaction: discord.Interaction, threshold: int):
    global star_threshold
    star_threshold = threshold
    await interaction.response.defer()
    if threshold < 2:
        await interaction.followup.send("Illegal threshold value.")
        return
    guild_id = str(interaction.guild.id)
    if guild_id not in starboard_config:
        starboard_config[guild_id] = {}
    starboard_config[guild_id]["starboard_threshold"] = threshold
    save_starboard_config(starboard_config)
    await interaction.followup.send(f"Star threshold set to: {threshold}")


async def send_help(interaction):
    await interaction.send(
        "To set up Starboard Bot, follow these steps:\n1. Use the command /board to set the starboard channel.\n2. Use the command /watch to add a watched channel. (/delwatch to delete)\n3. (Optional) Use the command /minstar if you want to set a custom star reaction threshold above 2.\n4. (Optional) Use the command /autoreact to toggle the bot's autoreactions."
    )


@client.tree.command(name="help", description="Show help message")
async def show_help(interaction: discord.Interaction):
    await interaction.response.defer()
    await send_help(interaction.channel)


@client.tree.command(name="autoreact", description="Toggle the bot's autoreactions")
@app_commands.default_permissions(administrator=True)
async def disable_autoreact(interaction: discord.Interaction):
    await interaction.response.defer()
    guild_id = str(interaction.guild.id)
    starboard_config[guild_id]["disable_autoreact"] = not starboard_config[guild_id][
        "disable_autoreact"
    ]
    save_starboard_config(starboard_config)
    status = (
        "disabled" if starboard_config[guild_id]["disable_autoreact"] else "enabled"
    )
    await interaction.followup.send(f"Autoreactions have been {status}.")


@client.event
async def on_guild_join(guild):
    default_threshold = 2
    guild_id = str(guild.id)
    starboard_config[guild_id] = {
        "starboard_channel_id": None,
        "starboard_threshold": default_threshold,
        "watched_channels": list(),
        "disable_autoreact": False,
    }
    save_starboard_config(starboard_config)
    await guild.system_channel.send("Thanks for adding zuki.star to your server!")
    await send_help(guild.system_channel)


client.run(config["starboard"])
