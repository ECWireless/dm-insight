# All credit to @midgerate, @xivanc, @daniel-ivanco, and the DAOHaus team for the original code
import os
import json
import csv
from datetime import datetime
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv
from calculate_token_balances import CalculateTokenBalances
from get_dm_members import get_all_dm_members

load_dotenv()
DAO_ADDRESS = os.getenv("DAO_ADDRESS")

balancesQuery = gql(
    """
        query MolochBalances($molochAddress: Bytes!, $first: Int, $skip: Int) {
            balances(
                first: $first,
                skip: $skip,
                where: {molochAddress: $molochAddress, action_not: "summon"}
                orderBy: timestamp
                orderDirection: asc
            ) {
                id
                timestamp
                balance
                tokenSymbol
                tokenAddress
                transactionHash
                tokenDecimals
                action
                payment
                tribute
                amount
                counterpartyAddress
                proposalDetail {
                    proposalId
                    applicant
                    details
                    sharesRequested
                    lootRequested
                }
            }
        }
    """
)

balancesTransport = AIOHTTPTransport(
    url="https://api.thegraph.com/subgraphs/name/odyssy-automaton/daohaus-stats-xdai"
)

PAGINATE_COUNT = 1000


async def retrieve_all_balances():
    async def fetch_balances(session, skip, all_balances):
        params = {
            "molochAddress": DAO_ADDRESS,
            "first": PAGINATE_COUNT,
            "skip": skip,
        }
        moloch_stats_balances = await session.execute(balancesQuery, variable_values=params)

        all_balances = [*all_balances, *moloch_stats_balances['balances']]
        skip += PAGINATE_COUNT

        if (len(moloch_stats_balances['balances']) == PAGINATE_COUNT):
            return await fetch_balances(session, skip, all_balances)

        return moloch_stats_balances['balances']

    async with Client(
        transport=balancesTransport,
        fetch_schema_from_transport=True,
    ) as session:
        try:
            return await fetch_balances(session, 0, [])
        except Exception as e:
            print(e)
            return None


async def get_treasury_transactions():
    moloch_stats_balances = await retrieve_all_balances()
    dm_members = await get_all_dm_members()

    calculated_token_balances = CalculateTokenBalances()

    def map_balances(moloch_stats_balance):
        balances = {
            'in': 0,
            'out': 0,
        }
        token_value = abs(int(calculated_token_balances.get_balance(
            moloch_stats_balance['tokenAddress'])) - int(moloch_stats_balance['balance']))

        formatted_value = int(token_value)
        if moloch_stats_balance['tokenSymbol'] == 'WXDAI':
            formatted_value = round(int(token_value) / 10 ** 18, 2)

        if moloch_stats_balance['payment'] is False and moloch_stats_balance['tribute'] is False:
            balances = {
                'in': 0,
                'out': 0,
            }
        if moloch_stats_balance['payment'] is False and moloch_stats_balance['tribute'] is True:
            calculated_token_balances.increment_inflow(
                moloch_stats_balance['tokenAddress'],
                token_value
            )
            balances = {
                'in': formatted_value,
                'out': 0,
            }

        if moloch_stats_balance['payment'] is True and moloch_stats_balance['tribute'] is False:
            calculated_token_balances.increment_outflow(
                moloch_stats_balance['tokenAddress'],
                token_value
            )
            balances = {
                'in': 0,
                'out': formatted_value,
            }

        tx_explorer_link = f"https://blockscout.com/xdai/mainnet/tx/{moloch_stats_balance['transactionHash']}"

        proposal = {}

        if moloch_stats_balance['proposalDetail'] is not None:
            details_data = moloch_stats_balance['proposalDetail']['details']
            details = json.loads(details_data)
            proposal_title = details['title']
            proposal_id = moloch_stats_balance['proposalDetail']['proposalId']
            proposal_link = f"https://app.daohaus.club/dao/0x64/{DAO_ADDRESS}/proposals/{proposal_id}"
            proposal = {
                'id': proposal_id,
                'shares': moloch_stats_balance['proposalDetail']['sharesRequested'],
                'loot': moloch_stats_balance['proposalDetail']['lootRequested'],
                'applicant': moloch_stats_balance['proposalDetail']['applicant'],
                'applicantDiscord': dm_members.get(moloch_stats_balance['proposalDetail']['applicant'].lower(), ''),
                'proposalLink': proposal_link,
                'title': proposal_title,
            }

        return {
            **balances,
            'date': datetime.fromtimestamp(int(moloch_stats_balance['timestamp'])),
            'type': moloch_stats_balance['action'].capitalize(),
            'tokenSymbol': moloch_stats_balance['tokenSymbol'],
            'tokenDecimals': moloch_stats_balance['tokenDecimals'],
            'tokenAddress': moloch_stats_balance['tokenAddress'],
            'txHash': moloch_stats_balance['transactionHash'],
            'txExplorerLink': tx_explorer_link,
            'counterparty': moloch_stats_balance['counterpartyAddress'],
            'proposal': proposal,
        }

    return list(map(map_balances, moloch_stats_balances))


async def get_treasury_details(year):
    unsorted_treasury_transactions = await get_treasury_transactions()
    treasury_transactions = sorted(
        unsorted_treasury_transactions, key=lambda k: k['date'].timestamp(), reverse=True)

    if year:
        year_unix_start = datetime(int(year), 1, 1).timestamp()
        year_unix_end = datetime(int(year), 12, 31).timestamp()
        treasury_transactions = list(
            filter(lambda x: x['date'].timestamp() >= year_unix_start and x['date'].timestamp() <= year_unix_end, treasury_transactions))

    return {
        # 'daoMetadata': daoMeta,
        'transactions': treasury_transactions,
        # 'tokenBalances': sorted(
        #     tokenBalances,
        #     ['closing.usdValue', 'closing.tokenValue'],
        #     ['desc', 'desc']
        # ),
        'vaultName': 'DAO Treasury',
    }


def write_to_csv(data):
    with open('rg_treasury.csv', 'w', newline='', encoding='utf-8') as csvfile:
        rg_treasury = csv.writer(csvfile, delimiter=',')
        rg_treasury.writerow(['Txn Hash', 'Date', 'Type', 'Shares',
                             'Loot', 'Applicant', 'Applicant Discord Handle', 'Title', 'Token', 'In', 'Out'])
        for row in data:
            if row['proposal'] == {}:
                rg_treasury.writerow([row['txHash'], row['date'].strftime('%m-%d-%Y'), row['type'],
                                     '', '', '', '', '', row['tokenSymbol'], row['in'], row['out']])
            else:
                rg_treasury.writerow([row['txHash'], row['date'].strftime('%m-%d-%Y'), row['type'], row['proposal']['shares'],
                                      row['proposal']['loot'], row['proposal']['applicant'], row['proposal']['applicantDiscord'], row['proposal']['title'], row['tokenSymbol'], row['in'], row['out']])


def format_as_csv(data):
    csv_text = 'Tx Hash,Date,Type,Shares,Loot,Applicant,Applicant Discord Handle,Title,Token,In,Out\n'
    for row in data:
        if row['proposal'] == {}:
            csv_text += f"{row['txHash']},{row['date'].strftime('%m-%d-%Y')},{row['type']},,,,,,{row['tokenSymbol']},{row['in']},{row['out']}\n"
        else:
            csv_text += f"{row['txHash']},{row['date'].strftime('%m-%d-%Y')},{row['type']},{row['proposal']['shares']},{row['proposal']['loot']},{row['proposal']['applicant']},{row['proposal']['applicantDiscord']},{row['proposal']['title']},{row['tokenSymbol']},{row['in']},{row['out']}\n"
    return csv_text


async def get_treasury_csv(year):
    treasury_details = await get_treasury_details(year)
    write_to_csv(treasury_details['transactions'])
    return format_as_csv(treasury_details['transactions'])
