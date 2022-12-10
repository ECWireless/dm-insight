from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio
from datetime import datetime

transport = AIOHTTPTransport(
    url='https://api.thegraph.com/subgraphs/name/ecwireless/raidguild')

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
                print(member)
                return member
            return None
        except:
            return None


async def on_message(message):
    if message.startswith('$get_member'):
        address = message.split(' ')[1]
        member = await get_member(address)
        if member:
            return f"Member address: {member['id']}\nDate joined: {datetime.fromtimestamp(int(member['dateJoined']) / 1000).strftime('%d-%m-%Y')}\nShares: {member['shares']}\nLoot: {member['loot']}\nJailed: {member['jailed']}\n\nVisit https://app.daohaus.club/dao/0x64/0xfe1084bc16427e5eb7f13fc19bcd4e641f7d571f/profile/{member['id']} to view profile."
        return 'Not a member!'

asyncio.run(on_message('$get_member <MEMBER_ADDRESS>'))
