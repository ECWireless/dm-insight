from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from get_dm_members import get_all_dm_members

query = gql(
    """
        query {
            members {
                id
                shares
            }
        }
    """
)


transport = AIOHTTPTransport(
    url="https://api.thegraph.com/subgraphs/name/ecwireless/raidguild"
)


def format_all_members_for_CSV(members, dm_members={}):
    data = "Address,Shares,Discord Handle\n"
    for member in members:
        discord_handle = dm_members.get(member['id'].lower(), "")
        data += f"{member['id']},{member['shares']},{discord_handle}\n"
    return data


async def get_all_members():
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            result = await session.execute(query)
            dm_members = await get_all_dm_members()
            members = result["members"]
            if members:
                return format_all_members_for_CSV(members, dm_members)
            return format_all_members_for_CSV([])
        except:
            return format_all_members_for_CSV([])
