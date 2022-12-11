import os
import re
import discord
from dotenv import load_dotenv
from datetime import datetime

from get_member import get_member
from get_intent import run_intent_session

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("$ask"):
        question = message.content[5:]
        is_get_member_intent = await run_intent_session(question)
        if is_get_member_intent:
            addresses = re.findall(
                pattern='0x[a-fA-F0-9]{40}$', string=question.replace("?", ""))
            address = addresses[0]
            member = await get_member(address)
            if member:
                await message.channel.send(
                    f"Member address: {member['id']}\nDate joined: {datetime.fromtimestamp(int(member['dateJoined']) / 1000).strftime('%m-%d-%Y')}\nShares: {member['shares']}\nLoot: {member['loot']}\nJailed: {member['jailed']}\n\nVisit https://app.daohaus.club/dao/0x64/0xfe1084bc16427e5eb7f13fc19bcd4e641f7d571f/profile/{member['id']} to view profile."
                )
                return
            await message.channel.send("Not a member!")


client.run(TOKEN)
