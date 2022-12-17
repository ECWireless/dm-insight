class CalculateTokenBalances:
    def __init__(self):
        self.calculated_token_balances = {}

    def init_token_balance(self, token_address):
        if token_address not in self.calculated_token_balances:
            self.calculated_token_balances[token_address] = {
                'out': 0,
                'in': 0,
                'balance': 0,
            }

    def get_balance(self, token_address):
        self.init_token_balance(token_address)
        return self.calculated_token_balances[token_address]['balance']

    def increment_inflow(self, token_address, in_value):
        self.init_token_balance(token_address)
        token_stats = self.calculated_token_balances[token_address]
        self.calculated_token_balances[token_address] = {
            'out': token_stats['out'],
            'in': token_stats['in'] + int(in_value),
            'balance': token_stats['balance'] + int(in_value),
        }

    def increment_outflow(self, token_address, out_value):
        self.init_token_balance(token_address)
        token_stats = self.calculated_token_balances[token_address]
        self.calculated_token_balances[token_address] = {
            'in': token_stats['in'],
            'out': token_stats['out'] + int(out_value),
            'balance': token_stats['balance'] - int(out_value),
        }

    def get_balances(self):
        return self.calculated_token_balances
