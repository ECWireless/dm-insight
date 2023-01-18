import os
import io
import re
from datetime import datetime
import discord
from discord import app_commands
from dotenv import load_dotenv

from get_member import get_member
from get_members import get_all_members
from get_intent import run_intent_session
from get_books import get_treasury_csv
from get_dm_members import get_all_dm_members

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")
GUILD_NAME = os.getenv("DISCORD_GUILD_NAME")
DAO_ADDRESS = os.getenv("DAO_ADDRESS")
MAINNET_DAO_ADDRESS = os.getenv("MAINNET_DAO_ADDRESS")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


async def ask_command(interaction, question, ephemeral):
    intent = await run_intent_session(question)
    # if intent == 'get_dao_address':
    #     return await interaction.response.send_message(f"Original question: *{question}*\n\nDAO address: {DAO_ADDRESS}", ephemeral=ephemeral)
    # if intent == 'get_mainnet_dao_address':
    #     return await interaction.response.send_message(f"Original question: *{question}*\n\nMainnet DAO address: {MAINNET_DAO_ADDRESS}", ephemeral=ephemeral)
    if intent == 'get_member':
        addresses = re.findall(
            pattern='0x[a-fA-F0-9]{40}$', string=question.replace("?", ""))
        if len(addresses) == 0:
            return await interaction.response.send_message(f"Original question: *{question}*\n\nNot a member!", ephemeral=ephemeral)
        address = addresses[0]
        member = await get_member(address)
        dm_members = await get_all_dm_members()
        discord_handle = dm_members.get(address.lower(), "")
        if member:
            return await interaction.response.send_message(
                f"Original question: *{question}*\n\nMember address: {member['id']}\nDiscord handle: {discord_handle}\nDate joined: {datetime.fromtimestamp(int(member['dateJoined']) / 1000).strftime('%m-%d-%Y')}\nShares: {member['shares']}\nLoot: {member['loot']}\nJailed: {member['jailed']}\n\nVisit https://app.daohaus.club/dao/0x64/0xfe1084bc16427e5eb7f13fc19bcd4e641f7d571f/profile/{member['id']} to view profile.",
                ephemeral=ephemeral,
                suppress_embeds=True
            )
        return await interaction.response.send_message(f"Original question: *{question}*\n\nNot a member!", ephemeral=ephemeral)
    if intent == 'get_all_members':
        members = await get_all_members()
        buffer = io.BytesIO(members.encode())
        file = discord.File(buffer, filename="members_data.csv")
        return await interaction.response.send_message(f"Original question: *{question}*\n\nHere is the data for all members.", file=file, ephemeral=ephemeral)
    if intent.startswith('get_books'):
        year = intent.split(' ')[1]
        if (year == '$intent.params.date-period'):
            year = None
        treasury_csv = await get_treasury_csv(year)
        buffer = io.BytesIO(treasury_csv.encode())
        file = discord.File(buffer, filename="rg_treasury.csv")
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is RaidGuild's accounting data for {year or 'all time'}.\n\nYou can view more details here: https://books.daohaus.club/#/dao/{DAO_ADDRESS}/treasury",
            file=file,
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    if intent.startswith('get_mainnet_books'):
        year = intent.split(' ')[1]
        if (year == '$intent.params.date-period'):
            year = None
        treasury_csv = await get_treasury_csv(year, True)
        buffer = io.BytesIO(treasury_csv.encode())
        file = discord.File(buffer, filename="mainnet_rg_treasury.csv")
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is RaidGuild's mainnet accounting data for {year or 'all time'}.\n\nYou can view more details here: https://books.daohaus.club/#/dao/{MAINNET_DAO_ADDRESS}/treasury",
            file=file,
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    if intent == 'link_website':
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is the link to RaidGuild's website: https://raidguild.org",
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    if intent == 'link_handbook':
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is the link to RaidGuild's handbook: https://handbook.raidguild.org",
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    if intent == 'link_bids':
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is the link to RaidGuild's Consultation Queue: https://bids.raidguild.org",
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    if intent == 'join_raidguild':
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is the link to start the process of joining RaidGuild: https://raidguild.org/join",
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    if intent == 'hire_raidguild':
        return await interaction.response.send_message(
            f"Original question: *{question}*\n\nHere is the link to start the process of hiring RaidGuild: https://raidguild.org/hire",
            ephemeral=ephemeral,
            suppress_embeds=True
        )
    return await interaction.response.send_message("Could not determine the intent of your question.", ephemeral=ephemeral)


@tree.command(name="ask", description="Ask any question about the DAO. This will be visible to everyone.", guild=discord.Object(id=GUILD_ID))
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
