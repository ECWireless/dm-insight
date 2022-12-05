import os
import discord
from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
SUBGRAPH_URL = os.getenv('SUBGRAPH_URL')

transport = AIOHTTPTransport(url=SUBGRAPH_URL)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

query = gql(
    """
        query {
            members(where: {shares: 0}) {
                id
           }
        }
    """
)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


async def get_data():
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        result = await session.execute(query)
        members = result['members']
        if members:
            return members
        return None


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$get_members'):
        members = await get_data()
        if members:
            await message.channel.send(members[0])
            return
        await message.channel.send('No members!')


client.run(TOKEN)
