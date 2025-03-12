# jito-py

`jito-py` is a Python library for interacting with the Jito via JSON-RPC.

## Installation

```bash
pip install jito_py
```
    
## Usage

### 1.Gets the block engine url

You can access the block engine information using the interface below

```python
from jito_py.block_engine import BlockEngine

engines = BlockEngine.get_block_engines(network='mainnet')
for k, v in engines.items():
    print(k)
    print(v['block_engine_url'])
```

You can get the address of the block engine from jito's website

- [Mainnet Addresses | Jito (gitbook.io)](https://jito-labs.gitbook.io/mev/searcher-resources/block-engine/mainnet-addresses)
- [Testnet Addresses | Jito (gitbook.io)](https://jito-labs.gitbook.io/mev/searcher-resources/block-engine/testnet-addresses)

### 2.Interact with Jito as a searcher

```python  
from jito_py.searcher import Searcher

# Create a searcher instance  
block_engine_url = "https://ny.mainnet.block-engine.jito.wtf"
searcher = Searcher(block_engine_url)

# Get tip accounts  
tip_accounts = searcher.get_tip_accounts()
print("Tip Accounts:", tip_accounts)

# Get what tip amount to use
# Directly access which Percentile Jito Fee to use for your transaction in lamports
tip_floors = searcher.get_tip_floors()
print(f"Avg Jito Tip in Lamports for Top 99 Percentile Landed Txns: "
      f"{tip_floors.landed_tips_lamports_99th_percentile}")

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

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
