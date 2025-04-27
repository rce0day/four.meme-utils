from web3 import Web3
from eth_account import Account
from mnemonic import Mnemonic

DEFAULT_RPC_URL = "https://bsc-dataseed.binance.org/"
PANCAKESWAP_ROUTER = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
CURRENT_WALLET_ADDRESS = None
FOUR_MEME_TOKEN = "0x204d19e836a620a8a86aee352b2b265a83525c0e"
FOUR_MEME_ROUTER = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"
TOKEN_MANAGER_HELPER_V3 = "0xF251F83e40a78868FcfA3FA4599Dad6494E46034"

FOUR_MEME_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenAddress", "type": "address"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokensSupportingFeeOnTransferTokens",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]

TOKEN_MANAGER_HELPER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"}
        ],
        "name": "getTokenInfo",
        "outputs": [
            {"internalType": "uint256", "name": "version", "type": "uint256"},
            {"internalType": "address", "name": "tokenManager", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "lastPrice", "type": "uint256"},
            {"internalType": "uint256", "name": "tradingFeeRate", "type": "uint256"},
            {"internalType": "uint256", "name": "minTradingFee", "type": "uint256"},
            {"internalType": "uint256", "name": "launchTime", "type": "uint256"},
            {"internalType": "uint256", "name": "offers", "type": "uint256"},
            {"internalType": "uint256", "name": "maxOffers", "type": "uint256"},
            {"internalType": "uint256", "name": "funds", "type": "uint256"},
            {"internalType": "uint256", "name": "maxFunds", "type": "uint256"},
            {"internalType": "bool", "name": "liquidityAdded", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

def buy_four_meme_exact(token_address, amount_bnb, min_tokens=1, gas_price=5, rpc_url=None, private_key=None):
    web3 = Web3(Web3.HTTPProvider(rpc_url or DEFAULT_RPC_URL))
    token_address = web3.to_checksum_address(token_address)
    if private_key:
        account = web3.eth.account.from_key(private_key)
        address = account.address
        print(f"Using provided private key for address: {address}")
    else:
        raise ValueError("Private key is required")

    balance_wei = web3.eth.get_balance(address)
    balance_bnb = web3.from_wei(balance_wei, 'ether')
    print(f"Wallet balance: {balance_bnb:.8f} BNB")
    amount_wei = web3.to_wei(amount_bnb, 'ether')
    
    if balance_wei < amount_wei:
        raise ValueError(f"Insufficient balance: {balance_bnb:.8f} BNB, needed {amount_bnb} BNB")

    MEME_ROUTER = web3.to_checksum_address("0xc205f591D395d59ad5bcB8bD824d8FA67ab4d15A")
    TOKEN_MANAGER = web3.to_checksum_address("0x5c952063c7fc8610FFDB798152D69F0B9550762b")

    router_abi = [
        {
            "inputs": [
                {"internalType": "address", "name": "tokenManager", "type": "address"},
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "funds", "type": "uint256"},
                {"internalType": "uint256", "name": "minAmount", "type": "uint256"}
            ],
            "name": "buyMemeToken",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        }
    ]
    
    router_contract = web3.eth.contract(address=MEME_ROUTER, abi=router_abi)
    
    try:
        nonce = web3.eth.get_transaction_count(address)
        txn = router_contract.functions.buyMemeToken(
            TOKEN_MANAGER,
            token_address,
            address,
            amount_wei,
            min_tokens
        ).build_transaction({
            'from': address,
            'value': amount_wei,
            'gas': 800000,
            'gasPrice': web3.to_wei(str(gas_price), 'gwei'),
            'nonce': nonce,
            'chainId': 56
        })
        
        signed_txn = web3.eth.account.sign_transaction(txn, private_key)
        print(f"Buying token with {amount_bnb} BNB...")
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction).hex()
        print(f"Transaction sent! Hash: {tx_hash}")
        print(f"View on BSCScan: https://bscscan.com/tx/{tx_hash}")
        return tx_hash
        
    except Exception as e:
        print(f"Error executing buy: {str(e)}")
        raise
