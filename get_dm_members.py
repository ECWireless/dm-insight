import os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv

load_dotenv()
DM_API_SECRET = os.getenv("DM_API_SECRET")
DM_API_URL = os.getenv("DM_API_URL")

query = gql(
    """
        query {
            members {
                eth_address
                contact_info {
                    discord
                }
            }
        }
    """
)


transport = AIOHTTPTransport(
    url=DM_API_URL,
    headers={
        'x-hasura-admin-secret': DM_API_SECRET,
    },
)


async def get_all_dm_members():
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            members = {}
            result = await session.execute(query)
            if result['members']:
                for member in result['members']:
                    if member['eth_address'] and member['contact_info'] and member['contact_info']['discord']:
                        members[member['eth_address'].lower()
                                ] = member['contact_info']['discord']
            return members
        except:
            return {}
