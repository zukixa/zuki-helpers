import discord, json
from discord.ext import commands

with open("config.json", "r") as f:
    config = json.load(f)


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
state_populations = {
    "California": 39538223,
    "Texas": 29145505,
    "Florida": 21538187,
    "New York": 20201249,
    "Pennsylvania": 13002700,
    "Illinois": 12812508,
    "Ohio": 11747694,
    "Georgia": 10711908,
    "North Carolina": 10611862,
    "Michigan": 10077331,
    "New Jersey": 9288994,
    "Virginia": 8631393,
    "Washington": 7693612,
    "Arizona": 7151502,
    "Massachusetts": 7029917,
    "Tennessee": 6910840,
    "Indiana": 6785528,
    "Missouri": 6154913,
    "Maryland": 6177224,
    "Wisconsin": 5893718,
    "Colorado": 5773714,
    "Minnesota": 5706494,
    "South Carolina": 5218040,
    "Alabama": 5024279,
    "Louisiana": 4657757,
    "Kentucky": 4505836,
    "Oregon": 4301089,
    "Oklahoma": 3959353,
    "Connecticut": 3605944,
    "Utah": 3271616,
    "Iowa": 3190369,
    "Nevada": 3104614,
    "Arkansas": 3011524,
    "Mississippi": 2961279,
    "Kansas": 2937880,
    "New Mexico": 2117522,
    "Nebraska": 1961504,
    "West Virginia": 1793716,
    "Idaho": 1839106,
    "Hawaii": 1455271,
    "New Hampshire": 1377529,
    "Maine": 1362359,
    "Montana": 1084225,
    "Rhode Island": 1097379,
    "Delaware": 989948,
    "Alaska": 733391,
    "North Dakota": 779004,
    "South Dakota": 903027,
    "Vermont": 643077,
    "Wyoming": 576851,
}


def get_population(state):
    if state in state_populations.keys():
        return state_populations[state]
    else:
        return None


@bot.event
async def on_ready():
    print("we online babyyyyy")
    act = discord.Activity(name="your despair >:)", type=discord.ActivityType.watching)
    await bot.change_presence(status=discord.Status.idle, activity=act)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(
            "Command not found. Please use a valid command. Use !help to learn more."
        )


@bot.command()
async def compare_population(ctx, state1, state2):
    population1 = get_population(state1)
    population2 = get_population(state2)

    if population1 and population2:
        comparison = f"Population of {state1}: {population1}\nPopulation of {state2}: {population2}"
        if population1 > population2:
            comparison += f"\n{state1} has a higher population than {state2}."
        elif population1 < population2:
            comparison += f"\n{state2} has a higher population than {state1}."
        else:
            comparison += f"\n{state1} and {state2} have the same population."
        await ctx.send(comparison)
    else:
        await ctx.send("Unable to retrieve population data for one or both states.")


bot.run(config["prez"])
