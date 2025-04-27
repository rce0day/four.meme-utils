from web3 import Web3
from eth_account import Account
import time

BNB_RPC_URL = "https://bsc-dataseed.binance.org/"
PANCAKE_V3_ROUTER = "0x1de460f363AF910f51726DEf188F9004276Bf4bc"
PANCAKE_V3_FACTORY = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"

FEE_TIERS = [100, 500, 2500, 3000, 10000]

PANCAKE_V3_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "factoryAddress", "type": "address"},
                    {"internalType": "address", "name": "poolAddress", "type": "address"},
                    {"internalType": "address", "name": "tokenIn", "type": "address"},
                    {"internalType": "address", "name": "tokenOut", "type": "address"},
                    {"internalType": "uint24", "name": "fee", "type": "uint24"},
                    {"internalType": "address", "name": "recipient", "type": "address"},
                    {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                    {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                    {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}
                ],
                "internalType": "struct IRouter.V3ExactInputParams",
                "name": "params",
                "type": "tuple"
            }
        ],
        "name": "swapV3ExactIn",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "address", "name": "token", "type": "address"},
            {"internalType": "uint256", "name": "amount", "type": "uint256"},
            {"internalType": "address", "name": "recipient", "type": "address"}
        ],
        "name": "unwrapWETH9",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]

PANCAKE_V3_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

PANCAKE_V3_POOL_ABI = [
    {
        "inputs": [],
        "name": "token0",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "fee",
        "outputs": [{"internalType": "uint24", "name": "", "type": "uint24"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "liquidity",
        "outputs": [{"internalType": "uint128", "name": "", "type": "uint128"}],
        "stateMutability": "view",
        "type": "function"
    }
]

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
    },
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

def approve_token_spending(token_address, spender_address, amount, gas_price=5, private_key=None):
    if private_key:
        web3 = Web3(Web3.HTTPProvider(BNB_RPC_URL))
        account = web3.eth.account.from_key(private_key)
        address = account.address
    else:
        raise ValueError("Private key is required")
    
    web3 = Web3(Web3.HTTPProvider(BNB_RPC_URL))
    token_address = web3.to_checksum_address(token_address)
    spender_address = web3.to_checksum_address(spender_address)
    
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
    print(f"Approval transaction sent! Hash: {tx_hash.hex()}")
    print(f"View on BSCScan: https://bscscan.com/tx/{tx_hash.hex()}")

    try:
        print("Waiting for approval confirmation...")
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"Approval confirmed! Status: {'Success' if tx_receipt.status == 1 else 'Failed'}")
        return tx_receipt.status == 1
    except Exception as e:
        print(f"Error waiting for approval: {str(e)}")
        return False

def find_best_pool(web3, factory_contract, token_in, token_out):
    best_pool = None
    best_fee = None
    best_liquidity = 0
    is_reversed = False
    
    for fee in FEE_TIERS:
        try:
            pool_address = factory_contract.functions.getPool(token_in, token_out, fee).call()
            
            if pool_address == "0x0000000000000000000000000000000000000000":
                continue
                
            pool_contract = web3.eth.contract(address=pool_address, abi=PANCAKE_V3_POOL_ABI)
            liquidity = pool_contract.functions.liquidity().call()
            token0 = pool_contract.functions.token0().call()
            token_reversed = token0.lower() != token_in.lower()
            
            if liquidity > best_liquidity:
                best_liquidity = liquidity
                best_pool = pool_address
                best_fee = fee
                is_reversed = token_reversed
                
        except Exception as e:
            continue
    
    if best_pool is None:
        for fee in FEE_TIERS:
            try:
                pool_address = factory_contract.functions.getPool(token_out, token_in, fee).call()
                
                if pool_address == "0x0000000000000000000000000000000000000000":
                    continue
                    
                pool_contract = web3.eth.contract(address=pool_address, abi=PANCAKE_V3_POOL_ABI)
                
                liquidity = pool_contract.functions.liquidity().call()
                
                if liquidity > best_liquidity:
                    best_liquidity = liquidity
                    best_pool = pool_address
                    best_fee = fee
                    is_reversed = True
                    
            except Exception as e:
                continue
    
    return best_pool, best_fee, is_reversed

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
        return balance_wei, decimals, symbol
    except Exception as e:
        print(f"Token balance: {balance_wei} (raw)")
        return balance_wei, 18, "None"

def sell_tokens_for_bnb_v3(token_address, percentage=1.0, gas_price=5, rpc_url=BNB_RPC_URL, private_key=None):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    
    if private_key:
        account = web3.eth.account.from_key(private_key)
        address = account.address
    else:
        raise ValueError("Private key is required")
    
    print(f"Using wallet: {address}")
    
    token_balance, decimals, symbol = check_token_balance(token_address, address)
    if token_balance[0] <= 0:
        raise ValueError("No tokens to sell")

    sell_amount = int(token_balance[0] * percentage)
    if sell_amount <= 0:
        raise ValueError("Amount to sell is too small")
    
    print(f"Selling {percentage * 100}% of {symbol} tokens ({web3.from_wei(sell_amount, 'ether')} tokens)")
    
    # approve token spending first (approve max uint256 for unlimited usage)
    token_contract = web3.eth.contract(address=token_address, abi=TOKEN_ABI)
    max_approve = 2**256 - 1
    
    allowance = token_contract.functions.allowance(address, PANCAKE_V3_ROUTER).call()
    if allowance < sell_amount:
        print(f"Approving {symbol} for trading on PancakeSwap V3...")
        
        nonce = web3.eth.get_transaction_count(address)
        approve_tx = token_contract.functions.approve(
            PANCAKE_V3_ROUTER,
            max_approve
        ).build_transaction({
            'from': address,
            'gas': 100000,
            'gasPrice': web3.to_wei(gas_price, 'gwei'),
            'nonce': nonce,
            'chainId': 56
        })
        
        signed_approve = web3.eth.account.sign_transaction(approve_tx, private_key)
        approve_tx_hash = web3.eth.send_raw_transaction(signed_approve.rawTransaction)
        print(f"Approval transaction sent: {approve_tx_hash.hex()}")
        
        print("Waiting for approval confirmation...")
        approve_receipt = web3.eth.wait_for_transaction_receipt(approve_tx_hash, timeout=120)
        if approve_receipt.status != 1:
            raise ValueError("Token approval failed")
        print("Token approved for trading!")
    else:
        print(f"Token already approved for trading")
    
    router_contract = web3.eth.contract(address=web3.to_checksum_address(PANCAKE_V3_ROUTER), abi=PANCAKE_V3_ROUTER_ABI)
    factory_contract = web3.eth.contract(address=web3.to_checksum_address(PANCAKE_V3_FACTORY), abi=PANCAKE_V3_FACTORY_ABI)
    
    token_in = token_address
    token_out = WBNB_ADDRESS
    pool_address, pool_fee = find_best_pool(web3, factory_contract, token_in, token_out)
    
    if not pool_address:
        print(f"No pool found for token pair {token_address}/WBNB")
        pool_address, pool_fee = find_best_pool(web3, factory_contract, token_out, token_in)
        
        if not pool_address:
            raise ValueError(f"No pool found for token pair WBNB/{token_address}")
        print(f"Found pool with reversed token order: {pool_address}, fee: {pool_fee}")
    else:
        print(f"Found pool: {pool_address}, fee: {pool_fee}")
    
    deadline = int(time.time() + 1800)
    amount_out_min = 1
    swap_params = {
        'factoryAddress': web3.to_checksum_address(PANCAKE_V3_FACTORY),
        'poolAddress': web3.to_checksum_address(pool_address),
        'tokenIn': web3.to_checksum_address(token_in),
        'tokenOut': web3.to_checksum_address(token_out),
        'fee': pool_fee,
        'recipient': address,
        'deadline': deadline,
        'amountIn': sell_amount,
        'amountOutMinimum': amount_out_min,
        'sqrtPriceLimitX96': 0
    }
    
    router_function = router_contract.functions.swapV3ExactIn(swap_params)
    
    try:
        nonce = web3.eth.get_transaction_count(address)
        swap_txn = router_function.build_transaction({
            'from': address,
            'value': 0,
            'gas': 500000,
            'gasPrice': web3.to_wei(str(gas_price), 'gwei'),
            'nonce': nonce,
            'chainId': 56
        })
        
        signed_txn = web3.eth.account.sign_transaction(swap_txn, private_key)
        
        print(f"Selling token using standard RPC method...")
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash = tx_hash.hex()
        
        print(f"Transaction sent! Hash: {tx_hash}")
        print(f"View on BSCScan: https://bscscan.com/tx/{tx_hash}")
        
        return tx_hash
    except Exception as e:
        print(f"Error executing V3 swap: {str(e)}")
        raise 