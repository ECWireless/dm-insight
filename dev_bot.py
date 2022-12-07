from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import asyncio

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
        params = {"member": memberAddress}
        result = await session.execute(query, variable_values=params)
        member = result['member']
        if member:
            print(member)
            return member
        return None

asyncio.run(get_member('$get_member <MEMBER_ADDRESS>'))
