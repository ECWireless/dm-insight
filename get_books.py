# All credit to @midgerate, @xivanc, and @daniel-ivanco for the original code

import os
import json
import csv
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from dotenv import load_dotenv
from calculate_token_balances import CalculateTokenBalances

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

    calculated_token_balances = CalculateTokenBalances()

    def map_balances(moloch_stats_balance):
        balances = {
            'in': 0,
            'out': 0,
        }
        token_value = abs(int(calculated_token_balances.get_balance(
            moloch_stats_balance['tokenAddress'])) - int(moloch_stats_balance['balance']))

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
                'in': token_value,
                'out': 0,
            }

        if moloch_stats_balance['payment'] is True and moloch_stats_balance['tribute'] is False:
            calculated_token_balances.increment_outflow(
                moloch_stats_balance['tokenAddress'],
                token_value
            )
            balances = {
                'in': 0,
                'out': token_value,
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
                'proposalLink': proposal_link,
                'title': proposal_title,
            }

        return {
            **balances,
            'date': moloch_stats_balance['timestamp'],
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


async def get_treasury_details():
    unsorted_treasury_transactions = await get_treasury_transactions()
    treasury_transactions = sorted(
        unsorted_treasury_transactions, key=lambda k: k['date'], reverse=True)

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
        rg_treasury.writerow(['Txn Hash', 'Timestamp', 'Type', 'Shares',
                             'Loot', 'Applicant', 'Title', 'Token', 'In', 'Out'])
        for row in data:
            if row['proposal'] == {}:
                rg_treasury.writerow([row['txHash'], row['date'], row['type'],
                                     '', '', '', '', row['tokenSymbol'], row['in'], row['out']])
            else:
                rg_treasury.writerow([row['txHash'], row['date'], row['type'], row['proposal']['shares'],
                                      row['proposal']['loot'], row['proposal']['applicant'], row['proposal']['title'], row['tokenSymbol'], row['in'], row['out']])


def format_as_csv(data):
    csv_text = 'Txn Hash,Timestamp,Type,Shares,Loot,Applicant,Title,Token,In,Out\n'
    for row in data:
        if row['proposal'] == {}:
            csv_text += f"{row['txHash']},{row['date']},{row['type']},,,,,{row['tokenSymbol']},{row['in']},{row['out']}\n"
        else:
            csv_text += f"{row['txHash']},{row['date']},{row['type']},{row['proposal']['shares']},{row['proposal']['loot']},{row['proposal']['applicant']},{row['proposal']['title']},{row['tokenSymbol']},{row['in']},{row['out']}\n"
    return csv_text


async def get_treasury_csv():
    treasury_details = await get_treasury_details()
    write_to_csv(treasury_details['transactions'])
    return format_as_csv(treasury_details['transactions'])