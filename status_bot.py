import discord
import json
from discord.ext import commands
from discord.app_commands import Choice
from discord import app_commands
import time

with open("config.json", "r") as f:
    config = json.load(f)
TOKEN = config["status_token"]
CHECK_BOT_ID = "1055209868899913788"  # replace with the ID of the bot you want to check
CHANNEL_ID = "1094336731089748010"  # replace with the ID of the channel where you want to announce the status changes
CHECK_2 = "1054742546343010376"  # risk
CHECK_3 = "1070246268443557968"  # trivia
CHECK_4 = "1101035453710348339"  # time
CHECK_5 = "1101000835267301458"  # test
CHECK_6 = "1116909665738051754"  # star
intents = discord.Intents.all()

bot = discord.ext.commands.Bot(command_prefix=".", intents=intents)
checkArray = [CHECK_BOT_ID, CHECK_2, CHECK_3, CHECK_4, CHECK_5, CHECK_6]
names = ["zuki.ai", "zuki.risk", "zuki.trivia", "zuki.time", "zuki.test", "zuki.star"]
curstat = None


def load_db(filepath):
    with open(filepath, "r") as f:
        return json.load(f)


def save_db(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def calc_uptime_since_june11(bot_uptime, total_time):
    june11_timestamp = time.mktime((2022, 6, 12, 0, 0, 0, -1, -1, -1))
    time_since_june11 = time.time() - june11_timestamp
    return bot_uptime / time_since_june11


db_filepath = "bot_data.json"
db_data = load_db(db_filepath)

for bot_id in checkArray:
    if bot_id not in db_data:
        db_data[bot_id] = {
            "last_seen_status": "offline",
            "last_status_change_time": time.time(),
            "total_uptime": 0,
        }

save_db(db_filepath, db_data)


@bot.event
async def on_ready():
    print(f"{bot.user} is online")
    act = discord.Activity(
        name="distress calls...", type=discord.ActivityType.listening
    )
    await bot.change_presence(status=discord.Status.idle, activity=act)


@bot.event
async def on_presence_update(before, after):
    global curstat
    if (
        str(before.id) not in checkArray
        or str(before.guild.id) != "1090022628946886726"
    ):
        return

    # get the channel object
    channel = await bot.fetch_channel(CHANNEL_ID)

    # load the JSON database
    db_data = load_db(db_filepath)
    bot_data = db_data[str(before.id)]

    current_time = time.time()

    if before.status != after.status and bot_data["last_seen_status"] != str(
        after.status
    ):
        name = names[checkArray.index(str(before.id))]
        time_diff = current_time - bot_data["last_status_change_time"]
        bot_data["last_status_change_time"] = current_time
        bot_data["last_seen_status"] = str(after.status)

        # Check if the bot is going online, which means the previous status was downtime
        if (
            before.display_name != "zuki.risk" and after.status == discord.Status.idle
        ) or (
            before.display_name == "zuki.risk" and after.status == discord.Status.online
        ):
            bot_data["total_downtime"] += time_diff
        else:
            bot_data["total_uptime"] += time_diff

        if after.status == discord.Status.offline:
            bot_data["total_uptime"] += time_diff
            curstat = after.status
            await channel.send(f"`{name} is offline, undergoing maintenance.`")

        elif after.status == discord.Status.idle:
            curstat = after.status
            await channel.send(f"`{name} is operational :)`")

        else:
            curstat = after.status
            await channel.send(f"`{name} is starting...`")
            if str(name) != "zuki.ai":
                await channel.send(f"`{name} is operational :)`")

    # Save the updated JSON database regardless of the if condition
    save_db(db_filepath, db_data)


@bot.tree.command(name="stats", description="grab usage stats for the bots.")
@app_commands.choices(
    bot=[
        Choice(name="zuki.gm", value=1),
        Choice(name="zuki.risk", value=2),
        Choice(name="zuki.trivia", value=3),
        Choice(name="zuki.time", value=4),
        Choice(name="zuki.test", value=5),
        Choice(name="zuki.star", value=6),
    ],
)
async def check_bot(interaction: discord.Interaction, bot: Choice[int]):
    await interaction.response.defer()
    if not 1 <= bot.value <= len(checkArray):
        await interaction.followup.send(
            "Invalid bot index. Please enter a valid number."
        )
        return

    bot_id = checkArray[bot.value - 1]
    bot_name = names[bot.value - 1]

    # load the JSON database
    db_data = load_db(db_filepath)

    last_seen_status = db_data[bot_id]["last_seen_status"]
    last_status_change_time = db_data[bot_id]["last_status_change_time"]
    total_uptime = db_data[bot_id]["total_uptime"]

    current_time = time.time()

    total_up = total_uptime + (current_time - last_status_change_time)

    total_down = current_time - last_status_change_time - total_up

    uptime_hours, rem = divmod(total_up, 3600)
    uptime_minutes, uptime_seconds = divmod(rem, 60)

    downtime_hours, rem = divmod(total_down, 3600)
    downtime_minutes, downtime_seconds = divmod(rem, 60)

    uptime_percentage = total_up / (total_up + total_down) * 100
    downtime_percentage = 100 - uptime_percentage

    await interaction.followup.send(
        f"`{bot_name}`:\n"
        f"- {'Down' if last_seen_status in ('offline', 'online') and bot_name != 'zuki.risk' else 'Up'}\n"
        f"- Uptime: {uptime_hours}h {uptime_minutes}m {uptime_seconds}s ({uptime_percentage:.2f}%)\n"
        f"- Downtime: {downtime_hours}h {downtime_minutes}m {downtime_seconds}s ({downtime_percentage:.2f}%)"
    )


@bot.command()
async def sync(ctx):
    print("sync command")
    if ctx.author.id == 325699845031723010:
        await bot.tree.sync()
        await ctx.send("Command tree synced.")
    else:
        await ctx.send("You must be the owner to use this command!")


bot.run(TOKEN)
