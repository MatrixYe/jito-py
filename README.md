# jito-py

`jito-py` is a Python library for interacting with the Solana blockchain via JSON-RPC.

## Installation

```bash
pip install jito_py

## Usage
```python
from jito_py.searcher import Searcher

# Create a searcher instance
searcher = Searcher("https://api.mainnet-beta.solana.com")

# Use the searcher to interact with the Solana blockchain
response = searcher.get_balance("your_account_address")
print(response)

```