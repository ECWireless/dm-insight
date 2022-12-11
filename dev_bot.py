import asyncio
import re
from datetime import datetime

from get_intent import run_intent_session
from get_member import get_member


async def on_message(message):
    if message.startswith('$ask'):
        question = message[5:]
        is_get_member_intent = await run_intent_session(question)
        if is_get_member_intent:
            addresses = re.findall(
                pattern='0x[a-fA-F0-9]{40}$', string=question.replace("?", ""))
            address = addresses[0]
            member = await get_member(address)
            if member:
                return f"Member address: {member['id']}\nDate joined: {datetime.fromtimestamp(int(member['dateJoined']) / 1000).strftime('%d-%m-%Y')}\nShares: {member['shares']}\nLoot: {member['loot']}\nJailed: {member['jailed']}\n\nVisit https://app.daohaus.club/dao/0x64/0xfe1084bc16427e5eb7f13fc19bcd4e641f7d571f/profile/{member['id']} to view profile."
        return 'Not a member!'
    return 'Not a command!'

print(asyncio.run(on_message(
    '$ask can you get member info for <MEMBER_ADDRESS>?')))
