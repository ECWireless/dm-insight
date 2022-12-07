import os
import discord
from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

transport = AIOHTTPTransport(
    url='https://api.thegraph.com/subgraphs/name/ecwireless/raidguild')

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

query = gql(
    """
        query getMember ($member: ID!) {
            member(id: $member) {
                id
                dateJoined
                delegateKey
                shares
                loot
                highestIndexYesVote
                jailed
           }
        }
    """
)


@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')


async def get_member(memberAddress):
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            params = {"member": memberAddress}
            result = await session.execute(query, variable_values=params)
            member = result['member']
            if member:
                return member
            return None
        except:
            return None


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('$get_member'):
        address = message.content.split(' ')[1]
        member = await get_member(address)
        if member:
            await message.channel.send(member)
            return
        await message.channel.send('Not a member!')


client.run(TOKEN)
