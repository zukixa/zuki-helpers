import discord, re
import json, asyncio
import sympy, aiofiles
from discord import app_commands
from discord.app_commands import Choice

with open("config.json", "r") as f:
    config = json.load(f)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.counter_lock = asyncio.Lock()

    async def setup_hook(self):
        await self.tree.sync()


if __name__ == "__main__":
    intents = discord.Intents.all()
    client = MyClient(intents=intents)

counter_file = "counter.json"


async def load_counter():
    async with aiofiles.open(counter_file, "r") as f:
        return json.loads(await f.read())


async def save_counter(data):
    async with aiofiles.open(counter_file, "w") as f:
        await f.write(json.dumps(data, indent=4))


def is_equation_valid(equation, expected_value, max_value=10**18, max_exponent=100):
    try:
        # Split equation by operators
        components = re.split("\+|-|\*|/", equation)

        for component in components:
            # If the component contains exponentiation
            if "^" in component:
                # Extract base and exponent
                base, exponent = component.split("^")
                # If base or exponent exceed limits, return False
                if abs(int(base)) > max_value or abs(int(exponent)) > max_exponent:
                    return False

        # Extract all numbers from the equation
        numbers = map(int, re.findall("\d+", equation))
        # If any number in the equation exceeds max_value, return False
        if any(abs(number) > max_value for number in numbers):
            return False

        result = sympy.sympify(equation)
        return result == expected_value
    except:
        return False


def get_new_seq(current, direction):
    if direction == "forward":
        return current + 1
    else:  # reverse
        return current - 1


@client.tree.command(
    name="setup",
    description="Set up the counting game in a specified channel and direction.",
)
@app_commands.choices(
    direction=[Choice(name="forward", value=0), Choice(name="backward", value=1)]
)
@app_commands.default_permissions(administrator=True)
async def setup(interaction, channel: discord.TextChannel, direction: Choice[int]):
    await interaction.response.defer()

    try:
        counter_data = await load_counter()
        current_seq = 0
        counter_data[str(channel.id)] = {
            "direction": direction.name,
            "current": current_seq,
        }
        await save_counter(counter_data)
        await interaction.followup.send(
            f"Counting game set up in {channel.mention} with direction '{direction.name}'."
        )
    except:
        await interaction.followup.send(
            "Failed to set up counting game. Please try again."
        )


@client.event
async def on_ready():
    print("hi")
    await client.change_presence(
        status=discord.Status.idle,activity=discord.CustomActivity(name="ping pong i can count ping pong", emoji="🖥"
    ))

@client.event
async def on_message_delete(message):
    if message.author.bot:
        return

    async with client.counter_lock:
        counter_data = await load_counter()
        channel_id = str(message.channel.id)
        if channel_id in counter_data:
            old_msg = f"A message containing the number {counter_data[channel_id]['current']} was deleted."
            await message.channel.send(old_msg)
            counter_data[channel_id]['current'] -= 1
            await save_counter(counter_data)

        # Delete previous announcements about deleted messages

        BOT_USER_ID = 1102325506294153348 # Replace this with your bot's user id
        limit = 100   # define a limit - Max amount of messages to search through
        async for msg in message.channel.history(limit=limit):
            if msg.author.id == BOT_USER_ID and "was deleted" in msg.content:
                await msg.delete()

@client.event
async def on_message(message):
    if message.author.bot:
        return

    async with client.counter_lock:
        counter_data = await load_counter()
        channel_id = str(message.channel.id)
        if channel_id in counter_data:
            data = counter_data[channel_id]
            direction = data["direction"]
            current_seq = data["current"]
            new_seq = get_new_seq(current_seq, direction)
            if is_equation_valid(message.content, new_seq):
                await message.add_reaction("✅")
                data["current"] = new_seq
            else:
                await message.add_reaction("❌")
                await message.channel.send(
                    f"Wrong number! The next number should have been {new_seq}. We are now back at 0."
                )
                data["current"] = 0
            await save_counter(counter_data)


client.run(config["counterbot"])
