from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

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


transport = AIOHTTPTransport(
    url="https://api.thegraph.com/subgraphs/name/ecwireless/raidguild"
)


async def get_member(memberAddress):
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            params = {"member": memberAddress}
            result = await session.execute(query, variable_values=params)
            member = result["member"]
            if member:
                return member
            return None
        except:
            return None
