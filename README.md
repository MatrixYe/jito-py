# jito-py

`jito-py` is a Python library for interacting with the Solana blockchain via JSON-RPC.

## Installation

```bash
pip install jito_py

## Usage
```python
from jito_py.searcher import Searcher
from jito_py.block_engine import BlockEngine


# Get Block Engine Url
engines=BlockEngine.get_block_engines(network='mainnet')
print(engines)
block_engine_url=engine[0]['block_engine_url']

# Create a searcher instance
searcher = Searcher(block_engine_url)

# Get tip accounts
tip_accounts = searcher.get_tip_accounts()
print("Tip Accounts:", tip_accounts)

# Get bundle statuses
bundle_ids = ["your_bundle_id_here"]
bundle_statuses = searcher.get_bundle_statuses(bundle_ids)
print("Bundle Statuses:", bundle_statuses)

# Send a bundle
transactions = ["your_base58_encoded_transaction_here"]
bundle_id = searcher.send_bundle(transactions)
print("Sent Bundle ID:", bundle_id)

# Send a transaction
transaction = "your_base58_encoded_transaction_here"
transaction_id = searcher.send_transaction(transaction)
print("Sent Transaction ID:", transaction_id)


```