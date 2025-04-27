from web3 import Web3
from eth_account import Account
import time
import threading

BNB_RPC_URL = "https://bsc-dataseed.binance.org/"
TOKEN_MANAGER_V1 = "0xEC4549caDcE5DA21Df6E6422d448034B5233bFbC"
TOKEN_MANAGER_V2 = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"
TOKEN_MANAGER_HELPER_V3 = "0xF251F83e40a78868FcfA3FA4599Dad6494E46034"

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
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "trySell",
        "outputs": [
            {"internalType": "address", "name": "tokenManager", "type": "address"},
            {"internalType": "address", "name": "quote", "type": "address"},
            {"internalType": "uint256", "name": "funds", "type": "uint256"},
            {"internalType": "uint256", "name": "fee", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

TOKEN_MANAGER_V1_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenAddress", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"}
        ],
        "name": "saleToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

TOKEN_MANAGER_V2_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "userAddress", "type": "address"},
            {"internalType": "uint256", "name": "tokenQty", "type": "uint256"}
        ],
        "name": "sellToken",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def check_token_balance(token_address, wallet_address, rpc_url=None):
    rpc_url = rpc_url or BNB_RPC_URL
    TOKEN_ABI = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        }
    ]
    
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    token_contract = web3.eth.contract(address=token_address, abi=TOKEN_ABI)
    balance_wei = token_contract.functions.balanceOf(wallet_address).call()
    try:
        symbol = token_contract.functions.symbol().call()
        decimals = token_contract.functions.decimals().call()
        balance = balance_wei / (10 ** decimals)
        print(f"Token balance: {balance:.8f} {symbol}")
        return balance_wei, decimals
    except Exception as e:
        print(f"Token balance: {balance_wei} (raw)")
        return balance_wei, 18

def get_token_info(token_address, rpc_url=None):
    rpc_url = rpc_url or BNB_RPC_URL
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    helper_contract = web3.eth.contract(address=web3.to_checksum_address(TOKEN_MANAGER_HELPER_V3), abi=TOKEN_MANAGER_HELPER_ABI)
    token_info = helper_contract.functions.getTokenInfo(token_address).call()
    info = {
        "version": token_info[0],
        "tokenManager": token_info[1],
        "quote": token_info[2],
        "lastPrice": token_info[3],
        "tradingFeeRate": token_info[4],
        "minTradingFee": token_info[5],
        "launchTime": token_info[6],
        "offers": token_info[7],
        "maxOffers": token_info[8],
        "funds": token_info[9],
        "maxFunds": token_info[10],
        "liquidityAdded": token_info[11]
    }
    
    return info

def approve_token_spending(token_address, spender_address, amount, gas_price=15, rpc_url=None, private_key=None):
    rpc_url = rpc_url or BNB_RPC_URL
    
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    spender_address = web3.to_checksum_address(spender_address)
    
    if private_key:
        account = web3.eth.account.from_key(private_key)
        address = account.address
    else:
        raise ValueError("Private key required")
    
    TOKEN_ABI = [
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }
    ]

    token_contract = web3.eth.contract(address=token_address, abi=TOKEN_ABI)
    nonce = web3.eth.get_transaction_count(address)
    approve_tx = token_contract.functions.approve(
        spender_address,
        amount
    ).build_transaction({
        'from': address,
        'gas': 100000,
        'gasPrice': web3.to_wei(str(gas_price), 'gwei'),
        'nonce': nonce,
        'chainId': 56
    })
    
    signed_tx = web3.eth.account.sign_transaction(approve_tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    try:
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"Approval confirmed! Status: {'Success' if tx_receipt.status == 1 else 'Failed'}")
        return tx_receipt.status == 1
    except Exception as e:
        print(f"Error waiting for approval: {str(e)}")
        return False

def simulate_token_sell(token_address, amount, rpc_url="https://bsc-dataseed.binance.org/"):
    TOKEN_MANAGER_HELPER_V3 = "0xF251F83e40a78868FcfA3FA4599Dad6494E46034"
    
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    
    TOKEN_MANAGER_HELPER_ABI = [
        {
            "inputs": [
                {"internalType": "address", "name": "token", "type": "address"},
                {"internalType": "uint256", "name": "amount", "type": "uint256"}
            ],
            "name": "trySell",
            "outputs": [
                {"internalType": "address", "name": "tokenManager", "type": "address"},
                {"internalType": "address", "name": "quote", "type": "address"},
                {"internalType": "uint256", "name": "funds", "type": "uint256"},
                {"internalType": "uint256", "name": "fee", "type": "uint256"}
            ],
            "stateMutability": "view",
            "type": "function"
        }
    ]

    helper_contract = web3.eth.contract(
        address=web3.to_checksum_address(TOKEN_MANAGER_HELPER_V3), 
        abi=TOKEN_MANAGER_HELPER_ABI
    )
    try:
        simulation = helper_contract.functions.trySell(token_address, amount).call()
        
        return {
            "success": True,
            "tokenManager": simulation[0],
            "quote": simulation[1],
            "funds": simulation[2],
            "fee": simulation[3]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def sell_token_using_correct_manager(token_address, percentage=1.0, gas_price=5, rpc_url="https://bsc-dataseed.binance.org/", private_key=None, skip_approval=False):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    
    if private_key:
        account = web3.eth.account.from_key(private_key)
        wallet_address = account.address
    else:
        raise ValueError("Private key required")
    
    balance_data = check_token_balance(token_address, wallet_address, rpc_url=rpc_url)
    if isinstance(balance_data, tuple):
        balance, decimals = balance_data
    else:
        balance = balance_data
        decimals = 18
    
    if not balance or balance <= 0:
        print("No tokens to sell!")
        return None
    
    amount_to_sell = int(balance * percentage)
    if amount_to_sell <= 0:
        print("Amount to sell is too small!")
        return None
    
    if decimals == 18:
        amount_to_sell = (amount_to_sell // 1000000000) * 1000000000
    
    print(f"Selling {percentage * 100}% of tokens ({amount_to_sell} tokens)")
    simulation = simulate_token_sell(token_address, amount_to_sell, rpc_url=rpc_url)
    
    if not simulation["success"]:
        print(f"Sell simulation failed: {simulation.get('error', 'Unknown error')}")
        print("This could be due to:")
        print("1. Token selling restrictions")
        print("2. Insufficient liquidity")
        print("3. Market conditions")
        print("Try with a smaller percentage or try again later.")
        return None
    
    token_manager_address = get_token_manager_address(token_address, rpc_url=rpc_url)
    if not token_manager_address:
        print("Failed to get token manager address")
        return None

    TOKEN_MANAGER_V1 = "0xEC4549caDcE5DA21Df6E6422d448034B5233bFbC"
    TOKEN_MANAGER_V2 = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"

    if token_manager_address.lower() == TOKEN_MANAGER_V1.lower():
        print("Using TokenManager V1 (saleToken function)")
        manager_version = 1
    elif token_manager_address.lower() == TOKEN_MANAGER_V2.lower():
        print("Using TokenManager V2 (sellToken function)")
        manager_version = 2
    else:
        print(f"Unknown token manager: {token_manager_address}")
        manager_version = 2
    if not skip_approval:
        print(f"Approving token manager to spend your tokens...")
        approval_thread = approve_token_in_background(
            token_address,
            token_manager_address,
            private_key=private_key,
            rpc_url=rpc_url,
            gas_price=gas_price,
            wait_for_completion=True
        )
        time.sleep(5)
    else:
        print("Skipping approval step (already approved during buying)")

    if manager_version == 1:
        manager_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "tokenAddress", "type": "address"},
                    {"internalType": "uint256", "name": "amount", "type": "uint256"}
                ],
                "name": "saleToken",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        token_manager = web3.eth.contract(address=token_manager_address, abi=manager_abi)
        token_manager_function = token_manager.functions.saleToken(
            token_address,
            amount_to_sell
        )
    else:
        manager_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "userAddress", "type": "address"},
                    {"internalType": "uint256", "name": "tokenQty", "type": "uint256"}
                ],
                "name": "sellToken",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            }
        ]
        token_manager = web3.eth.contract(address=token_manager_address, abi=manager_abi)
        token_manager_function = token_manager.functions.sellToken(
            token_address,
            amount_to_sell
        )
    
    try:
        nonce = web3.eth.get_transaction_count(wallet_address)

        tx = token_manager_function.build_transaction({
            'chainId': 56,
            'gas': 500000,
            'gasPrice': web3.to_wei(gas_price, 'gwei'),
            'nonce': nonce,
        })

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)

        print(f"Selling token using standard RPC method...")
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_hash = tx_hash.hex()

        print(f"Transaction sent: {tx_hash}")
        print(f"View on BSCScan: https://bscscan.com/tx/{tx_hash}")

        return tx_hash
    except Exception as e:
        print(f"Error selling tokens: {str(e)}")
        raise

def approve_token_in_background(token_address, spender_address, private_key, rpc_url="https://bsc-dataseed.binance.org/", gas_price=5, wait_for_completion=True):
    def approve_task():
        try:
            print(f"Starting approval task for token {token_address}")
            web3 = Web3(Web3.HTTPProvider(rpc_url))
            token_address_checksum = web3.to_checksum_address(token_address)
            spender_address_checksum = web3.to_checksum_address(spender_address)
            
            account = web3.eth.account.from_key(private_key)
            wallet_address = account.address
            print(f"Approving from wallet: {wallet_address}")

            token_abi = [
                {
                    "constant": False,
                    "inputs": [
                        {"name": "_spender", "type": "address"},
                        {"name": "_value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "payable": False,
                    "stateMutability": "nonpayable",
                    "type": "function"
                }
            ]

            token_contract = web3.eth.contract(address=token_address_checksum, abi=token_abi)
            max_uint256 = 2**256 - 1
            nonce = web3.eth.get_transaction_count(wallet_address)
            print(f"Using nonce {nonce} for approval transaction")
            
            approve_txn = token_contract.functions.approve(
                spender_address_checksum,
                max_uint256
            ).build_transaction({
                'chainId': 56,
                'gas': 100000,
                'gasPrice': web3.to_wei(gas_price, 'gwei'),
                'nonce': nonce,
            })
            
            signed_txn = web3.eth.account.sign_transaction(approve_txn, private_key)

            tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            print(f"Approval transaction sent: {tx_hash.hex()}")
            print(f"View approval transaction on BSCScan: https://bscscan.com/tx/{tx_hash.hex()}")

            if wait_for_completion:
                print(f"Waiting for approval transaction receipt...")
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                if receipt.status == 1:
                    print(f"Approval transaction successful!")
                    return True
                else:
                    print(f"Approval transaction failed! Status: {receipt.status}")
                    return False
            return True
            
        except Exception as e:
            print(f"Error in approval process: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    thread = threading.Thread(target=approve_task)
    thread.daemon = False
    thread.start()
    
    return thread

def get_token_manager_address(token_address, rpc_url=None):
    token_info = get_token_info(token_address, rpc_url)
    return token_info["tokenManager"] 