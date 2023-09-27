import discord, re
import json, asyncio
import sympy
from discord import app_commands

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


def load_counter():
    with open(counter_file, "r") as f:
        return json.load(f)


def save_counter(data):
    with open(counter_file, "w") as f:
        json.dump(data, f, indent=4)


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
@app_commands.default_permissions(administrator=True)
async def setup(interaction, channel: discord.TextChannel, direction: str):
    await interaction.response.defer()

    try:
        counter_data = load_counter()
        current_seq = 0
        counter_data[str(channel.id)] = {"direction": direction, "current": current_seq}
        save_counter(counter_data)
        await interaction.followup.send(
            f"Counting game set up in {channel.mention} with direction '{direction}'."
        )
    except:
        await interaction.followup.send(
            "Failed to set up counting game. Please try again."
        )


@client.event
async def on_ready():
    print("hi")
    act = discord.Activity(name="countu countu ～", type=discord.ActivityType.streaming)
    await client.change_presence(status=discord.Status.idle, activity=act)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    async with client.counter_lock:
        counter_data = load_counter()
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
            save_counter(counter_data)


client.run(config["counterbot"])
