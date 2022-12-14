import os
import re
import discord
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime

from get_member import get_member
from get_intent import run_intent_session

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
GUILD_NAME = os.getenv("DISCORD_GUILD_NAME")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def ask_command(interaction, question, ephemeral):
    is_get_member_intent = await run_intent_session(question)
    if is_get_member_intent:
        addresses = re.findall(
            pattern='0x[a-fA-F0-9]{40}$', string=question.replace("?", ""))
        address = addresses[0]
        member = await get_member(address)
        if member:
            return await interaction.response.send_message(
                f"Original question: *{question}*\n\nMember address: {member['id']}\nDate joined: {datetime.fromtimestamp(int(member['dateJoined']) / 1000).strftime('%m-%d-%Y')}\nShares: {member['shares']}\nLoot: {member['loot']}\nJailed: {member['jailed']}\n\nVisit https://app.daohaus.club/dao/0x64/0xfe1084bc16427e5eb7f13fc19bcd4e641f7d571f/profile/{member['id']} to view profile.",
                ephemeral=ephemeral
            )
        return await interaction.response.send_message("Not a member!", ephemeral=ephemeral)
    return await interaction.response.send_message("Could not determine the intent of your question.", ephemeral=ephemeral)


@tree.command(name="ask_public", description="Ask any question about the DAO. This will be visible to everyone.", guild=discord.Object(id=GUILD_ID))
async def ask_command_public(interaction, question: str):
    return await ask_command(interaction, question, False)


@tree.command(name="ask_private", description="Ask any question about the DAO. This will be visible only to you.", guild=discord.Object(id=GUILD_ID))
async def ask_command_private(interaction, question: str):
    return await ask_command(interaction, question, True)


@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    guild = discord.utils.get(client.guilds, name=GUILD_NAME)
    print(
        f'{client.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
    print(f"We have logged in as {client.user}")

client.run(TOKEN)
