import json
import discord
from discord import app_commands
import aiohttp

with open("config.json", "r") as f:
    config = json.load(f)


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


if __name__ == "__main__":
    intents = discord.Intents.default()
    client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.tree.command(
    name="ask",
    description="Talk to the AI :).",
)
@app_commands.describe(question="The Question to the AI!")
async def ask(interaction, question: str):
    await interaction.response.defer()
    headers = {"Authorization": f"Bearer {config['api_key']}"}
    messages = [{"role": "user", "content": question}]
    json_data = {"model": "gpt-3.5-turbo", "messages": messages}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(
                "https://api.pierangelo.info/v1/chat/completions/",
                json=json_data,
            ) as resp:
                response = await resp.json()
                await interaction.followup.send(
                    response["choices"][0]["message"]["content"]
                )
    except Exception as e:
        print(str(e))
        await interaction.followup.send(str(e))


client.run(config["memebot"])
