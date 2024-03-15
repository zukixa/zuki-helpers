from discord.app_commands import Choice
import math, ujson as json, discord, datetime, aiofiles, asyncio
from discord.ext import commands, tasks
from discord import app_commands
import datetime, typing
from ftc import FictionalTimeController, load_ftcs_state, save_ftcs_state


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()
with open("/home/kira/k_zuki.helpers/config.json", "r") as f:
    config = json.load(f)


if __name__ == "__main__":
    intents = discord.Intents.all()
    intents.message_content = False
    intents.presences = False
    intents.members = False
    client = MyClient(intents=intents)

ftcs = load_ftcs_state()
        
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

@client.tree.command(name="time-help", description="Displays help information for time-related commands.")
async def time_help(interaction: discord.Interaction):
    help_message = discord.Embed(title="Time Bot Help", color=0x00ff00)
    help_message.add_field(name="/report", value="Notify the bot owners of an issue.", inline=False)
    help_message.add_field(name="/time-set", value="Set your Roleplay (RP) time. Usage: /time-set [speed] [notify_interval] [day] [month] [year] [channel] [role] [voice_channel]. Note: Requires administrator permissions.", inline=False)
    help_message.add_field(name="/time-info", value="Grab server's Time Info.", inline=False)
    help_message.add_field(name="/time-do", value="Manage your server's RP time. Operations include: Get Current Time, Toggle Time Progression, Delete Time Data.", inline=False)
    help_message.add_field(name="/time-until", value="Calculate the real-life time until a specified fictional time. Use the format DD/MM/YYYY for the timestr parameter.", inline=False)
    help_message.add_field(name="/time-del", value="Remove time-related configurations from the server, including Time Notification Channel, Time Notification Ping Role, and Voice Channel Update Channel.", inline=False)
    help_message.add_field(name="/time-set-channel", value="Set the channel where time update notifications will be posted.", inline=False)
    help_message.add_field(name="/time-set-voice", value="Set the voice channel where the current time will be displayed.", inline=False)
    
    help_message.set_footer(text="Use these commands to control and manage your server's fictional RP time settings and notifications. Make sure to have the appropriate permissions where required.")

    await interaction.response.send_message(embed=help_message, ephemeral=True)

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


@client.tree.command(description="Set your RP time! (Enable w/ /time-manage toggle)!",name="time-set")
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
        app_commands.Choice(name="Update on each IRP Month passed.", value="monthly"),
        app_commands.Choice(name="Update on each IRP Year passed.", value="yearly"),
    ]
)
@app_commands.default_permissions(administrator=True)
async def settime(
    interaction: discord.Interaction,
    speed: str,
    notify_interval: app_commands.Choice[str],
    day: int,
    month: int,
    year: int,
    channel: typing.Optional[discord.TextChannel] = None,
    role: typing.Optional[discord.Role] = None,
    voice_channel: typing.Optional[discord.VoiceChannel] = None,
):
    await interaction.response.defer()

    # Validate input parameters for day, month, year
    if day > 28 or day < 1 or month > 12 or month < 1 or year < 2 or year > 5000:
        await interaction.followup.send("Invalid date input.")
        return
    # Check if the bot has permissions in the provided text channel
    if channel and not channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.followup.send(f"I do not have permission to send messages in {channel.mention}.")
        return

    # If a voice channel is provided, check if the bot has permission to join and speak in it
    if voice_channel and not (voice_channel.permissions_for(interaction.guild.me).manage_channels):
        await interaction.followup.send(f"I do not have permission to join or speak in the voice channel {voice_channel.mention}.")
        return

    # Determine the start_date based on day, month, and year inputs
    start_date = datetime.datetime(year=year, month=month, day=day)

    # Create or update an FTC instance for the guild
    guild_id = str(interaction.guild_id)
    try:
        ftc = FictionalTimeController(start_date=start_date, speed=speed, 
                                    notify_interval=notify_interval.value, 
                                    guild_id=guild_id, channel=channel.id if channel else None, role_id=role.id if role else None, voice=voice_channel.id if voice_channel else None)
    except Exception as e:
        await interaction.followup.send(e)    
        return
    # Store FTC in the dictionary
    ftcs[guild_id] = ftc

    # Save the updated FTCs state
    save_ftcs_state(ftcs)

    await interaction.followup.send("Time settings updated! Don't forget to toggle-on your time :)")

@client.tree.command(description="Grab Server's Time Info.", name='time-info')
async def timeinfo(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        ftc = ftcs.get(str(interaction.guild_id))
        
        if ftc:
            # Convert datetime to Unix timestamps for formatting
            start_date_unix = int(ftc.start_date.timestamp())
            last_fictional_time_unix = int(ftc.current_fictional_time().timestamp())

            # Optionally fetch channel names if IDs are stored
            notification_channel_name = f"<#{ftc.channel_id}>" if ftc.channel_id else "None"
            voice_channel_name = f"<#{ftc.voice_channel_id}>" if ftc.voice_channel_id else "None"

            # Building a formatted message
            info_message = (
                f"**Time Settings for Server:**\n"
                f"Start Date: <t:{start_date_unix}:F>\n"
                f"Speed (months per day): {ftc.monthsperday}\n"
                f"Notify Interval: {ftc.notify_interval.capitalize()}\n"
                f"Role ID for Notifications: {'<@&' + str(ftc.role_id) + '>' if ftc.role_id else 'None'}\n"
                f"Is Time Progression Running: {'Yes' if ftc.isRunning else 'No'}\n"
                f"Current Fictional Time: <t:{last_fictional_time_unix}:F>\n"
                f"Notification Channel: {notification_channel_name}\n"
                f"Voice Update Channel: {voice_channel_name}"
            )
        else:
            info_message = "No Time Controller Info found. Please use /settime to set one up."
        
        await interaction.followup.send(info_message, ephemeral=True)
    
    except Exception as e:
        print(f"Issue with {str(e)}")
        await interaction.followup.send(
            "Could not get data. Usually, you need to /settime first!"
        )


@client.tree.command(description="Manage your server's RP time.",name="time-do")
@app_commands.describe(operation="Select the operation you want to perform.")
@app_commands.choices(operation=[
    app_commands.Choice(name="Get Current Time", value=1),
    app_commands.Choice(name="Toggle Time Progression", value=2),
    app_commands.Choice(name="Delete Time Data", value=3),
])
async def timemanage(interaction: discord.Interaction, operation: app_commands.Choice[int]):
    await interaction.response.defer()
    try:
        ftc = ftcs.get(str(interaction.guild_id))
        
        if not ftc:
            await interaction.followup.send("No time data is available for this server. Please use /settime first.")
            return
        
        # Handle each operation based on the choice made
        # Handle each operation based on the choice made
        if operation.value == 1:  # Get Current Time
            current_time = ftc.current_fictional_time()  # Assuming this returns a datetime object for the current RP time
            # Convert the current_time (datetime object) to a Unix timestamp
            current_time_unix = int(current_time.timestamp())
            # Format and send the response using Discord's Timestamp Styling
            await interaction.followup.send(f"Current role-play time: <t:{current_time_unix}:F>")
        
        elif operation.value == 2:  # Toggle Time Progression
            if ftc.isRunning:
                ftc.last_fictional_time = ftc.current_fictional_time()
                ftc.start_date = ftc.current_fictional_time()
            else:
                ftc.start_time = datetime.datetime.now()
            ftc.isRunning = not ftc.isRunning
            state = "unpaused" if ftc.isRunning else "paused"
            save_ftcs_state(ftcs)  # Save state changes
            await interaction.followup.send(f"Role-play time progression {state}")
        
        elif operation.value == 3:  # Delete Time Data
            del ftcs[str(interaction.guild_id)]
            save_ftcs_state(ftcs)  # Save state changes after deletion
            await interaction.followup.send("Time data purged for this server.")
        
    except Exception as e:
        print(f"Issue encountered: {e}")
        await interaction.followup.send("An error occurred while managing time data.")


@client.tree.command(description="Calculate the real-life time until a specified fictional time.",name='time-until')
@app_commands.describe(timestr="DD/MM/YYYY of until when to calculate.")
async def timeuntil(interaction: discord.Interaction, timestr: str):
    await interaction.response.defer()
    # Load the FictionalTimeController instance for the guild
    ftc = ftcs.get(str(interaction.guild_id))
    
    if not ftc:
        await interaction.followup.send("No time data available for this server; please ensure the time has been set.")
        return
    
    # Parse the target fictional date from the user input
    date_format = "%d/%m/%Y"
    try:
        target_fictional_date = datetime.datetime.strptime(timestr, date_format)
    except ValueError:
        await interaction.followup.send("Invalid date format. Please use DD/MM/YYYY.")
        return

    # Get the current fictional time
    current_fictional_time = ftc.current_fictional_time()

    # Check if the target date is in the past
    if target_fictional_date <= current_fictional_time:
        await interaction.followup.send("Specified fictional time is in the past or now.")
        return
    
    # Calculate the difference in seconds between the target and current fictional times
    difference_in_seconds = (target_fictional_date - current_fictional_time).total_seconds()
    # Since ftc.speed gives roleplay seconds per real-life minute, calculate real-life minutes needed
    real_life_minutes_needed = difference_in_seconds / (ftc.speed)

    # Calculate the real-life datetime when the target fictional time will occur
    real_life_datetime_target = datetime.datetime.now() + datetime.timedelta(minutes=real_life_minutes_needed)

    # Convert the target real-life datetime to a Unix timestamp for Discord formatting
    target_real_life_unix = int(real_life_datetime_target.timestamp())
    
    await interaction.followup.send(f"The role-play date {timestr} will be reached in real life at: <t:{target_real_life_unix}:F>")

@client.tree.command(description="Remove anything unwanted.",name='time-del')
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
    guild_id = str(interaction.guild_id)
    if guild_id in ftcs:
        ftc = ftcs[guild_id]
        if object.value == 1:
            ftc.channel_id = None
            message = "Time Notification Channel has been removed."
        elif object.value == 2:
            ftc.role_id = None
            message = "Time Notification Ping Role has been removed."
        elif object.value == 3:
            # Assuming an attribute for voice channel needs to be implemented in the FTC class
            ftc.voice_channel_id = None
            message = "Voice Channel Update Channel has been removed."
        save_ftcs_state(ftcs)
        await interaction.followup.send(message)
    else:
        await interaction.followup.send("No time data available for this server; perhaps /settime hasn't been done yet.")

@client.tree.command(description="Set where the time update output is.",name='time-set-channel')
@app_commands.describe(channel="The channel in which the output shall be at")
@app_commands.default_permissions(manage_roles=True)
async def setchannel(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    if guild_id in ftcs:
        # Check if the bot has permissions in the provided text channel
        if channel and not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.followup.send(f"I do not have permission to send messages in {channel.mention}.")
            return
        ftc = ftcs[guild_id]
        ftc.channel_id = channel.id  # Assuming channel_id is intended to store text channel for notifications
        save_ftcs_state(ftcs)
        await interaction.followup.send(f"Output is now set to {channel.mention}.")
    else:
        await interaction.followup.send("Failed to set channel for output, as /settime hasn't been done yet.")

@client.tree.command(description="Set the channel where the voice shall be displayed",name='time-set-voice')
@app_commands.describe(voice_channel="The channel in which the output shall be at")
@app_commands.default_permissions(manage_roles=True)
async def setvoice(interaction: discord.Interaction, voice_channel: discord.VoiceChannel):
    await interaction.response.defer()
    guild_id = str(interaction.guild_id)
    if guild_id in ftcs:
        # If a voice channel is provided, check if the bot has permission to join and speak in it
        if voice_channel and not (voice_channel.permissions_for(interaction.guild.me).manage_channels):
            await interaction.followup.send(f"I do not have permission to join or speak in the voice channel {voice_channel.mention}.")
            return
        
        ftc = ftcs[guild_id]
        ftc.voice_channel_id = voice_channel.id  
        save_ftcs_state(ftcs)
        await interaction.followup.send(f"Voice display output is now set to {voice_channel.mention}.")
    else:
        await interaction.followup.send("Failed to set voice channel for output, as /settime hasn't been done yet.")

@client.tree.command(name='sync', description='Owner only')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == 325699845031723010:
        await client.tree.sync(guild=interaction.guild)
        print('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')

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

    Note: In order to set me up properly, you'll need Administrator permissions! /time-set only works with such permissions :)
    After using /time-set, don't forget to use /time-manage toggle!!! Otherwise your time won't start :)
    """
    try:
        await guild.channels[0].send(message)
    except:
        pass

def is_announcement_due(notify_interval, last_fictional_time, current_fictional_time):
    # Check for monthly interval
    if notify_interval == 'monthly':
        # A crossover occurs if the current month and year are different from the last announcement's month and year.
        if (current_fictional_time.year > last_fictional_time.year or
                (current_fictional_time.year == last_fictional_time.year and
                 current_fictional_time.month > last_fictional_time.month)):
            return True

    # Check for yearly interval
    elif notify_interval == 'yearly':
        # A crossover occurs if the current year is different from the last announcement's year.
        if current_fictional_time.year > last_fictional_time.year:
            return True

    # If the conditions for neither monthly nor yearly crossover are met, no announcement is due.
    return False

def craft_custom_update_message(ftc):
    # Normalize the current fictional time to the start of that month
    normalized_fictional_time = datetime.datetime(
        year=ftc.current_fictional_time().year,
        month=ftc.current_fictional_time().month,
        day=1,  # Start of the month
        hour=0, minute=0, second=0  # Start of the day
    )
    
    # Convert the normalized fictional time to a Unix timestamp
    unix_timestamp = int(normalized_fictional_time.timestamp())
    
    # Check if a role_id is present
    if ftc.role_id:
        message = f"<@&{ftc.role_id}> Time Update! It is now: <t:{unix_timestamp}:F>"
    else:
        message = f"Time Update! It is now: <t:{unix_timestamp}:F>"
    
    return message

@tasks.loop(seconds=120)
async def update_time():
    global ftcs
    for x, ftc in ftcs.items():
        if not ftc.isRunning:  # Skip if the FTC is not running
            continue
        try:
            current_fictional_time = ftc.current_fictional_time()
        except:
            print(f'{ftc.guild_id} has a too large time')
            ftc.speed /= 10000
            continue
        # Calculate the current fictional time
        # Determine if an announcement is needed based on notify_interval
        if is_announcement_due(ftc.notify_interval, ftc.last_fictional_time, current_fictional_time):
            try:
                if ftc.channel_id:
                    channel = client.get_channel(ftc.channel_id)
                    if channel:
                        await channel.send(craft_custom_update_message(ftc))
            except:
                print(f'{ftc.guild_id} has a broken channel')
                ftc.channel_id = None
                pass
            try:
                if ftc.voice_channel_id:
                    voice = client.get_channel(ftc.voice_channel_id)
                    if voice:
                        await voice.edit(name=current_fictional_time)
            except:
                print(f'{ftc.guild_id} has a broken voice channel')
                ftc.voice_icd = None
                pass
        ftc.last_fictional_time = ftc.current_fictional_time()
    save_ftcs_state(ftcs)
    ftcs = load_ftcs_state()
client.run(config["timetoken"])
