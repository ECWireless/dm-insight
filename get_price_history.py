import os
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv
import asyncio

load_dotenv()
DM_API_SECRET = os.getenv("DM_API_SECRET")
DM_API_URL = os.getenv("DM_API_URL")

query = gql(
    """
        query {
            treasury_token_history {
                id
                date
                price_usd
                symbol
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


async def get_price_history():
    async with Client(
        transport=transport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            members = {}
            result = await session.execute(query)
            if result['treasury_token_history']:
                for member in result['treasury_token_history']:
                    if members[member['symbol']] is None:
                        members[member['symbol']] = {}
                    members[member['symbol']][member['date']
                                              ] = member['price_usd']
            return members
        except Exception as e:
            print(e)
            return {}

print(asyncio.run(get_price_history()))
