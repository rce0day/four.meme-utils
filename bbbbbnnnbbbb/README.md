# Four.meme Token Trading Tools

A collection of Python scripts for interacting with tokens on the Binance Smart Chain (BSC) for four.meme, specializing in trading, checking token status, and managing both bonded and unbonded tokens.

## Table of Contents
- [Overview](#overview)
- [Scripts](#scripts)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)


## Overview

This repository contains a set of Python scripts that interact with the Binance Smart Chain (BSC) to perform various token-related operations on the four.meme platform, including buying and selling tokens, checking token bond status, and handling token approvals. These tools are designed to work with both standard tokens and specialized token mechanisms like bonded tokens on decentralized exchanges.

## Scripts

### `buy.py`
- Handles buying tokens on BSC using various routers
- Supports PancakeSwap and specialized router interactions
- Contains functions to execute BNB-to-token swaps

### `sell.py`
- Facilitates selling tokens back to BNB
- Supports different token manager versions
- Contains functions to check token balances, approve token spending, and simulate token sells
- Manages token sale execution with appropriate managers

### `check_bond.py`
- Utility to check if a token is bonded (has liquidity in a PancakeSwap V3 pool)
- Verifies token existence and retrieves basic token information
- Scans across multiple fee tiers to find liquidity pools

### `bond_buy.py`
- Specialized tool for buying bonded tokens through PancakeSwap V3
- Contains pool discovery mechanisms to find the best liquidity pool
- Handles the complete buying process for tokens with V3 liquidity

### `bond_sell.py`
- Specialized tool for selling bonded tokens through PancakeSwap V3
- Helps users exit positions in bonded tokens
- Manages token approvals and executes multi-step selling process

## Requirements

- web3.py
- eth-account

## Installation

```bash
pip install web3 eth-account mnemonic
```

## Usage

Each script can be used independently based on your needs:

```python

from check_bond import is_token_bonded

token_address = "0xYourTokenAddress"
result = is_token_bonded(token_address)
print(f"Token is bonded: {result}")


from bond_buy import buy_tokens_with_bnb_v3

private_key = "your_private_key"
token_address = "0xYourTokenAddress"
amount_bnb = 0.1
tx_hash = buy_tokens_with_bnb_v3(token_address, amount_bnb, private_key=private_key)
```

## Examples

### Buying a token:
```python
from buy import buy_four_meme_exact


token_address = "0xTokenAddress"
private_key = "your_private_key"
buy_four_meme_exact(token_address, 0.1, private_key=private_key)
```

### Selling a token:
```python
from sell import sell_token_using_correct_manager


token_address = "0xTokenAddress"
private_key = "your_private_key"
sell_token_using_correct_manager(token_address, percentage=1.0, private_key=private_key)
```
