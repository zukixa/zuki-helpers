import discord
import json
from discord.app_commands import Choice
from discord import app_commands
import time, aiofiles

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
CHECK_7 = "1155955452740370585"  # api

class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


if __name__ == "__main__":
    intents = discord.Intents.all()
    bot = MyClient(intents=intents)
checkArray = [CHECK_BOT_ID, CHECK_2, CHECK_3, CHECK_4, CHECK_5, CHECK_6, CHECK_7]
names = [
    "zuki.ai",
    "zuki.risk",
    "zuki.trivia",
    "zuki.time",
    "zuki.test",
    "zuki.star",
    "zuki.api",
]
curstat = None


async def load_db(filepath):
    async with aiofiles.open(filepath, "r") as f:
        return json.loads(await f.read())


async def save_db(filepath, data):
    async with aiofiles.open(filepath, "w") as f:
        await f.write(json.dumps(data, indent=4))


def calc_uptime_since_june11(bot_uptime, total_time):
    june11_timestamp = time.mktime((2022, 6, 12, 0, 0, 0, -1, -1, -1))
    time_since_june11 = time.time() - june11_timestamp
    return bot_uptime / time_since_june11


db_filepath = "bot_data.json"


@bot.event
async def on_ready():
    print(f"{bot.user} is online")
    act = discord.Activity(
        name="distress calls...", type=discord.ActivityType.listening
    )
    await bot.change_presence(status=discord.Status.idle, activity=act)

    db_data = await load_db(db_filepath)

    for bot_id in checkArray:
        if bot_id not in db_data:
            db_data[bot_id] = {
                "last_seen_status": "offline",
                "last_status_change_time": time.time(),
                "total_uptime": 0,
            }

    await save_db(db_filepath, db_data)


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
    db_data = await load_db(db_filepath)
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
            await channel.send(f"`{name} is offline, undergoing maintenance.` <@325699845031723010>")

        elif after.status == discord.Status.idle:
            curstat = after.status
            await channel.send(f"`{name} is operational :)` <@325699845031723010>")

        else:
            curstat = after.status
            await channel.send(f"`{name} is starting...` <@325699845031723010>")
            if str(name) != "zuki.ai":
                await channel.send(f"`{name} is operational :)` <@325699845031723010>")

    # Save the updated JSON database regardless of the if condition
    await save_db(db_filepath, db_data)


@bot.tree.command(name="stats", description="grab usage stats for the bots.")
@app_commands.choices(
    bot=[
        Choice(name="zuki.gm", value=1),
        Choice(name="zuki.risk", value=2),
        Choice(name="zuki.trivia", value=3),
        Choice(name="zuki.time", value=4),
        Choice(name="zuki.test", value=5),
        Choice(name="zuki.star", value=6),
        Choice(name="zuki.api", value=7),
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
    db_data = await load_db(db_filepath)

    start_time = 1682373600.0
    if "api" in bot.name:
        start_time = 1692972414

    last_seen_status = db_data[bot_id]["last_seen_status"]
    last_status_change_time = db_data[bot_id]["last_status_change_time"]
    total_uptime = db_data[bot_id]["total_uptime"]

    current_time = time.time()

    #  total_up = total_uptime + (current_time - last_status_change_time)

    #  total_down = current_time - last_status_change_time - total_up

    total_up = total_uptime
    # Determine if the bot is currently up
    is_currently_up = (
        last_seen_status not in ("offline", "online") or bot_name == "zuki.risk"
    )

    # Add current uptime to total uptime if the bot is currently up
    if is_currently_up:
        current_uptime = current_time - last_status_change_time
        total_up += current_uptime

    # Now calculate total_down
    total_down = current_time - start_time - total_up
    if total_down < 0:
        total_down = -total_down

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


bot.run(TOKEN)
