from discord.app_commands import Choice
import math
import discord
from discord.ext import tasks
import json
from discord import app_commands
import typing
import re
import datetime
import time
import aiofiles, asyncio

time_data_filename = "./time.json"
data_lock = asyncio.Lock()
with open("./config.json", "r") as f:
    config = json.load(f)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


if __name__ == "__main__":
    intents = discord.Intents.all()
    intents.message_content = False
    intents.presences = False
    intents.members = False
    client = MyClient(intents=intents)


async def load_time_data():
    try:
        async with aiofiles.open(time_data_filename, mode="r") as f:
            return json.loads(await f.read())
    except Exception as e:
        print(f"Issue in dataload: {str(e)}")
        return None


async def save_time_data(data):
    try:
        # Read the current state of the file before overwriting
        existing_data = await load_time_data()

        if existing_data is not None:
            # Loop through keys in the new data
            for key, value in data.items():
                # Update the existing data with the new data
                existing_data[key] = value
            
            # At this point, any key not in `data` but present in `existing_data` is preserved

        # Write the merged data back to the file
        async with aiofiles.open(time_data_filename, mode="w") as f:
            await f.write(json.dumps(existing_data or data, indent=4))
    except Exception as e:
        print(f"Issue in datasave: {str(e)}")


def create_time_notification(current_time):
    month_map = {
        1: "Jan.",
        2: "Feb.",
        3: "Mar.",
        4: "Apr.",
        5: "May.",
        6: "Jun.",
        7: "Jul.",
        8: "Aug.",
        9: "Sep.",
        10: "Oct.",
        11: "Nov.",
        12: "Dec.",
    }
    day = math.floor(current_time["day"])
    if day < 1:
        day = 1
    month = current_time["month"]
    if month < 1:
        month = 1
    year = current_time["year"]
    if day == 0:
        day = 1
    appendix = "th"

    if str(day)[-1] == "1" and day != 11:  # excluding 11
        appendix = "st"
    elif str(day)[-1] == "2" and day != 12:  # excluding 12
        appendix = "nd"
    elif str(day)[-1] == "3" and day != 13:  # excluding 13
        appendix = "rd"

    return f"{month_map[month]} {day}{appendix}, {year}"


def split_into_batches(iterable, n):
    """
    Splits an iterable object into n approximately evenly sized chunks
    """
    lst = list(iterable)
    size = len(lst)
    batch_size = size // n
    for i in range(0, size, batch_size):
        if i + batch_size < size:
            yield lst[i : i + batch_size]
        else:
            yield lst[i:]


current_batch = 1
batch_factor = 5
def validate_and_format_date(year, month, day):
    # Adjust the year to have four digits if necessary
    # If year or day is 0, set it to 1.
    year = max(1, year)
    day = max(1, day)

    # Skip or flag dates with negative year, zero month, or day exceeds valid range
    if 1 <= month <= 12:
        # Zero-padding month and day to ensure correct string format
        return f"{year:04d}-{month:02d}-{day:02d}"
    else:
        # Handle invalid dates based on your application's needs
        return None


# Update the current role-play time and notify users if necessary
@tasks.loop(seconds=60)
async def update_time():
    global current_batch
    time_data = await load_time_data()
    guilds_to_run = {k: v for k, v in time_data.items() if v["is_running"] == "true"}
    batches = list(split_into_batches(guilds_to_run.items(), batch_factor))
    current_batch = (current_batch + 1) % batch_factor   #---> will probably eventually return depending on ratelimits
    current_items = batches[current_batch]
    invalid_guilds = []
    for guild_id, guild_data in current_items:
        try:
            if guild_data["is_running"] == "true":
                print('processing guild')
                print(guild_id)

                # Define current datetime from guild_data
                # Extract integer and fractional parts of the day
                try:
                    # Extracting and handling day values
                    day_integer = int(guild_data['current_time']['day'])
                    day_fraction = guild_data['current_time']['day'] - day_integer

                    # Construct the date string
                    year = guild_data['current_time']['year']
                    month = guild_data['current_time']['month']
                    current_time_str = validate_and_format_date(year, month, day_integer)
                    if not current_time_str:
                        invalid_guilds.append(guild_id)
                        continue
                    # Parse the datetime object
                    current_datetime = datetime.datetime.strptime(current_time_str, "%Y-%m-%d")

                    # Calculating fractional day in seconds and adding it
                    fractional_day_in_seconds = day_fraction * 86400
                    fractional_day_timedelta = datetime.timedelta(seconds=fractional_day_in_seconds)
                    current_datetime = current_datetime + fractional_day_timedelta

                except Exception as e:
                    print(f"Error processing date values: {e}")


                # Calculate added time in days
                added_secs = datetime.timedelta(seconds=(batch_factor * float(guild_data["speed"])))
                new_datetime = current_datetime + added_secs
                # Calculate the fractional day component

                hours_as_fraction_of_day = new_datetime.hour / 24
                minutes_as_fraction_of_day = new_datetime.minute / (24 * 60)
                seconds_as_fraction_of_day = new_datetime.second / (24 * 60 * 60)
                fractional_day_component = hours_as_fraction_of_day + minutes_as_fraction_of_day + seconds_as_fraction_of_day

                notify = False
                # Identify if notification conditions are met
                if guild_data["notify_interval"] == "daily":

                    notify = True
                elif guild_data["notify_interval"] == "monthly" and new_datetime.month != current_datetime.month:

                    notify = True
                elif guild_data["notify_interval"] == "yearly" and new_datetime.year != current_datetime.year:

                    notify = True
                print(f'old day: {float(int(new_datetime.day))}')
                print(f'new day: {float(int(new_datetime.day)) + float(fractional_day_component)}')
                # Update guild_data with new date
                guild_data["current_time"]["year"] = new_datetime.year
                guild_data["current_time"]["month"] = new_datetime.month
                guild_data["current_time"]["day"] = float(int(new_datetime.day)) + float(fractional_day_component)
                time_data[guild_id] = guild_data
                # or maybe await save_time_data(time_data) here as well?
                await save_time_data(time_data)# too often
                guild = None
                channel = None
                voice = None
                role = None
                if notify:
                    guild = client.get_guild(int(guild_id))
                    if not guild:
                        guild = await client.fetch_guild(int(guild_id))
                    if not guild:
                        invalid_guilds.append(guild_id)
                        continue
                    try:
                        channel = client.get_channel(guild_data['channel_id'])
                        if not channel:
                            channel = await client.fetch_channel(guild_data["channel_id"])
                        if not channel:
                            invalid_guilds.append(guild_id)
                            continue
                        if guild_data.get("voice_id", None):
                            voice = await client.fetch_channel(
                                guild_data["voice_id"]
                            )
                            if not voice:
                                invalid_guilds.append(guild_id)
                                continue
                            if voice:
                                await voice.edit(
                                    name=create_time_notification(
                                        guild_data["current_time"]
                                    )
                                )
                        if guild_data.get("role_id", None):
                            role = await guild.fetch_role(guild_data["role_id"])
                            if not role:
                                invalid_guilds.append(guild_id)
                                continue
                            notif = create_time_notification(guild_data["current_time"])
                            if not channel:
                                channel = guild.system_channel
                            try:
                                await channel.send(f"{role.mention} Time update! {notif}")
                            except Exception as e:
                                print(str(e))
                                await channel.send(str(e))
                        else:
                            notif = create_time_notification(guild_data["current_time"])
                            if not channel:
                                channel = guild.system_channel
                            try:
                                try:
                                    await channel.send(f"Time update! {notif}")
                                except Exception as e:
                                    print(str(e))
                            #      pass  # what
                            except Exception as e:
                                try:
                                    await channel.send(str(e))
                                except Exception as e:
                                    print(str(e))
                    except:
                        invalid_guilds.append(guild_id)
        except:
            invalid_guilds.append(guild_id)
    for invalid_guild in invalid_guilds:
        del time_data[invalid_guild]
    await save_time_data(time_data)


@update_time.before_loop
async def before_update_time():
    await client.wait_until_ready()


@client.event
async def on_ready():
    print(f"Logged In as {client.user}")
    await client.change_presence(
        status=discord.Status.idle,
        activity=discord.CustomActivity(
            name="The Clock of NationRP <3",
        ),
    )
    update_time.start()


@client.event
async def on_guild_join(guild: discord.Guild):
    message = """
    **Hi! Thank you for inviting me :)**
    In order to use me, I suggest you use /help ! All is explained there well :)

    Note: In order to set me up properly, you'll need Administrator permissions! /settime only works with such permissions :)
    After using /settime, don't forget to use /toggletime!!! Otherwise your time won't start :)
    """
    try:
        await guild.channels[0].send(message)
    except:
        pass


@client.tree.command(description="Calculate the time needed till X time.")
@app_commands.describe(timestr="DD/MM/YYYY of until when to calculate.")
async def timeuntil(interaction: discord.Interaction, timestr: str):
    await interaction.response.defer()
    try:
        json_current_time = (await load_time_data())[str(interaction.guild_id)][
            "current_time"
        ]
        input_date_str = timestr
        speed = (await load_time_data())[str(interaction.guild_id)]["speed"]
        date_format = "%d/%m/%Y"
        input_datetime = datetime.datetime.strptime(input_date_str, date_format)
        input_total_days = input_datetime.toordinal()

        current_datetime = datetime.datetime(
            json_current_time["year"],
            json_current_time["month"],
            math.floor(json_current_time["day"]),
        )
        current_total_days = (
            current_datetime.toordinal()
            + json_current_time["day"]
            - math.floor(json_current_time["day"])
        )

        # Calculate the difference in days
        days_difference = input_total_days - current_total_days
        # Calculate time in minutes needed to reach input date
        minutes_to_reach_date = days_difference / (speed / 86400)

        # Convert minutes to Unix epoch timestamp
        unix_epoch = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        timestamp = int(
            (unix_epoch + datetime.timedelta(minutes=minutes_to_reach_date)).timestamp()
        )

        # Get current time as Unix epoch timestamp
        current_timestamp = int(time.time())

        # Add current time to calculated timestamp
        final_timestamp = timestamp + current_timestamp
        await interaction.followup.send(
            "Your desired time will be reached at the following time: <t:"
            + str(final_timestamp)
            + ">"
        )
    except:
        await interaction.followup.send(
            "Failed to calculate output, usually because /settime has not been done yet, or the time is in the past."
        )


@client.tree.command(description="Short explanation of the bot.")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Don't forget to use /report to report any issue!",
        description="zuki.time -- general help section.",
        color=0x00FFFF,
        url="https://discord.com/invite/xRV8NJRFeK",
    )

    embed.add_field(
        name="/settime [Time per IRL day] [monthly/yearly rate] [start day] [month] [year]\n [Optional: Notification Role]\n",
        value="- Setup the time management for your server. \n> Time must be denoted in style of `12y` or  `3 months`, days are not supported. \n> Resetting the starting date requires usage of /endtime \n> # ***After setup, you MUST use /toggletime.***",
        inline=False,
    )

    embed.add_field(
        name="/timeinfo",
        value="- Receive a block of text explaining the current time settings.",
        inline=False,
    )

    embed.add_field(
        name="/endtime",
        value="- Delete the current time settings for this server, useful for resetting the year, month, day",
        inline=False,
    )

    embed.add_field(
        name="/setchannel [channel]",
        value="- Set the channel of the bot's time update output.",
        inline=False,
    )
    embed.add_field(
        name="/setvoice [channel]",
        value="- Set the channel of the bot's time update output, for a voice channel.",
        inline=False,
    )
    embed.add_field(
        name="/remove [channel/role]",
        value="- Delete current selections for time updates, voice channel updates, or role pings.",
        inline=False,
    )

    embed.add_field(
        name="/gettime",
        value="- As a roleplayer, get the current RP time as denoted in `Day X, Month X, Year X`",
        inline=False,
    )

    embed.add_field(
        name="/timeuntil [DD/MM/YYYY string]",
        value="- Calculator as for when the IRP DD/MM/YYYY is reached IRL.",
        inline=False,
    )
    embed.set_footer(
        text=f"Brought to you by @zukixa, running in {len(client.guilds)} servers, making >3000 users happy.",
        icon_url="https://cdn.discordapp.com/avatars/325699845031723010/b80a55ef4a3ce5c6cec05d69475a5bf8.png?size=4096",
    )
    await interaction.response.send_message(embed=embed)


@client.tree.command(description="Remove anything unwanted.")
@app_commands.describe(object="What to remove.")
@app_commands.choices(
    object=[
        Choice(name="Time Notification Channel", value=1),
        Choice(name="Time Notification Ping Role", value=2),
        Choice(name="Voice Channel Update Channel", value=3),
    ]
)
@app_commands.default_permissions(manage_roles=True)
async def remove(interaction: discord.Interaction, object: Choice[int]):
    await interaction.response.defer()
    try:
        time_data = await load_time_data()
        guild = str(interaction.guild.id)
        if object.value == 1:
            time_data[guild]["channel_id"] = None
        elif object.value == 2:
            time_data[guild]["role_id"] = None
        elif object.value == 3:
            time_data[guild]["voice_id"] = None
        await interaction.followup.send(
            f"{object.name} has been removed. Any associated function with such has now stopped working."
        )
        await save_time_data(time_data)  # how the fuck did i forget this
    except:
        await interaction.followup.send(
            f"Failed to remove {object.name}, usually because it is not set currently."
        )


@client.tree.command(description="set where the time update output is.")
@app_commands.describe(channel="The channel in which the output shall be at")
@app_commands.default_permissions(manage_roles=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer()
    try:
        time_data = await load_time_data()
        guild = str(interaction.guild_id)
        time_data[guild]["channel_id"] = int(channel.id)
        await save_time_data(time_data)
        await interaction.followup.send(f"Output is now in {channel.name}")
    except:
        await interaction.followup.send(
            "Failed to change output, usually because /settime has not been done yet."
        )


@client.tree.command(description="set what channel the voice shall be displayed")
@app_commands.describe(channel="The channel in which the output shall be at")
@app_commands.default_permissions(manage_roles=True)
async def setvoice(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.defer()
    try:
        time_data = await load_time_data()
        guild = str(interaction.guild_id)
        time_data[guild]["voice_id"] = int(channel.id)
        await save_time_data(time_data)
        await interaction.followup.send(f"Output is now in {channel.name}")
    except:
        await interaction.followup.send(
            "Failed to change output, usually because /settime has not been done yet."
        )


@client.tree.command(description="Set your RP time! (Enable w/ /toggletime)!")
@app_commands.describe(
    speed="Time per IRL day: '12y, 3 months'.",
    notify_interval="Update of time-progression per **IRP** Day/Month/Year",
    day="obvious...",
    month="obvious...",
    year="obvious...",
    role="Optional Role to be pinged as part of the update!",
)
@app_commands.choices(
    notify_interval=[
        Choice(name="Update on each IRP Month passed.", value="monthly"),
        Choice(name="Update on each IRP Year passed.", value="yearly"),
    ]
)
@app_commands.default_permissions(administrator=True)
async def settime(
    interaction: discord.Interaction,
    speed: str,
    notify_interval: Choice[str],
    day: int,
    month: int,
    year: int,
    role: typing.Optional[discord.Role],
):
    await interaction.response.defer()
    match = re.findall(r"(\d+(?:\.\d+)?)(\D+)", speed)
    speedTime = None
    if match:
        num, unit = match[0]
        num = float(num)
        unit = unit.strip()
        if "y" in unit:
            speedTime = num * 12
        else:
            speedTime = num
    else:
        await interaction.followup.send("Not a valid speed. Speed needs to be in format of '1 year' or '2m' type.")
        return
    if day > 28 or day < 1:
        await interaction.followup.send("Invalid day input.")
        return
    if month > 12 or month < 1:
        await interaction.followup.send("Invalid month input")
        return
    if year < 1 or year > 9000:
        await interaction.followup.send("Invalid year input")
        return
    time_data = await load_time_data()
    guild = str(interaction.guild_id)
    message = "Time settings overridden! Don't forget to toggle-on your time :)"
    if guild not in time_data:
        message = "Time settings updated! Don't forget to toggle-on your time :)"
    # the magic speed calculation
    secpermin = float(speedTime * 1826.4)  # magic constant mon/day -> sec/min
    time_data[guild] = {"current_time": {"day": day, "month": month, "year": year}}
    time_data[guild]["speed"] = secpermin
    time_data[guild]["notify_interval"] = notify_interval.value.lower()
    time_data[guild]["role_id"] = role.id if role else None
    time_data[guild]["channel_id"] = int(interaction.channel.id)
    time_data[guild]["is_running"] = "false"
    await save_time_data(time_data)
    await interaction.followup.send(
        content=message
    )


@client.tree.command(description="Grab Server's Time Info.")
async def timeinfo(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        data = (await load_time_data())[str(interaction.guild_id)]
        if not data:
            data = "No info found."
        await interaction.followup.send(data)
    except Exception as e:
        print(f"Issue with {str(e)}")
        await interaction.followup.send(
            "Could not get data. Usually, you need to /settime first!"
        )


@client.tree.command(description="Notify the Bot Owners of an issue.")
@app_commands.describe(message="Describe your problem with the bot.")
async def report(interaction: discord.Interaction, message: typing.Optional[str]):
    try:
        channel = await interaction.client.fetch_channel("1101749630632460288")
        user = await interaction.client.fetch_user("325699845031723010")
        await channel.send(
            f"zuki.time reporting error in {interaction.guild.name} by {interaction.user.name} - {user.mention}! {message}"
        )
        await interaction.response.send_message("Report succeeded.", ephemeral=True)
    except:
        await interaction.response.send_message("Report failed.", ephemeral=True)


@client.tree.command(description="Grab the current time in your RP.")
async def gettime(interaction: discord.Interaction):
    await interaction.response.defer()
    time_data = await load_time_data()
    guild = str(interaction.guild.id)

    if guild in time_data:
        current_time = time_data[guild]["current_time"]
        time_str = create_time_notification(current_time)
        await interaction.followup.send(f"Current role-play time: {time_str}")
    else:
        await interaction.followup.send("No time data is available for this server.")


@client.tree.command(description="Toggle On/Off Time Progression for your server.")
@app_commands.default_permissions(administrator=True)
async def toggletime(interaction: discord.Interaction):
    await interaction.response.defer()
    time_data = await load_time_data()
    guild = str(interaction.guild.id)

    if guild not in time_data:
        await interaction.followup.send("No time data is available for this server.")
        return
    current_data = time_data[guild]["is_running"]
    if "true" in current_data:
        time_data[guild]["is_running"] = "false"
    else:
        time_data[guild]["is_running"] = "true"
    # time_data[guild]["is_running"] = not time_data[guild]["is_running"]
    await save_time_data(time_data)

    state = "unpaused" if time_data[guild]["is_running"] == "true" else "paused"
    await interaction.followup.send(f"Role-play time progression {state}")


@client.tree.command(description="Delete your Server's Time Data.")
@app_commands.default_permissions(administrator=True)
async def endtime(interaction: discord.Interaction):
    await interaction.response.defer()
    time_data = await load_time_data()
    guild = str(interaction.guild.id)

    if guild in time_data:
        del time_data[guild]
        await save_time_data(time_data)
        await interaction.followup.send("Time data purged for this server.")
    else:
        await interaction.followup.send("No time data is available for this server.")


client.run(config["timetoken"])
