from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

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


def format_all_members_for_CSV(members):
    data = "address,shares\n"
    for member in members:
        data += f"{member['id']},{member['shares']}\n"
    return data


async def get_all_members():
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            result = await session.execute(query)
            members = result["members"]
            if members:
                return format_all_members_for_CSV(members)
            return format_all_members_for_CSV([])
        except:
            return format_all_members_for_CSV([])
