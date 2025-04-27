from web3 import Web3
from eth_account import Account
import time

DEFAULT_RPC_URL = "https://bsc-dataseed.binance.org/"
BNB_RPC_URL = DEFAULT_RPC_URL
CURRENT_WALLET_ADDRESS = None
PANCAKE_V3_ROUTER = "0x1de460f363AF910f51726DEf188F9004276Bf4bc"
PANCAKE_V3_FACTORY = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
TOKEN_MANAGER_HELPER_V3 = "0xF251F83e40a78868FcfA3FA4599Dad6494E46034"

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


def find_best_pool(web3, factory_contract, token_in, token_out):
    best_pool = None
    best_fee = None
    best_liquidity = 0
    
    for fee in FEE_TIERS:
        try:
            pool_address = factory_contract.functions.getPool(token_in, token_out, fee).call()
            
            if pool_address == "0x0000000000000000000000000000000000000000":
                continue
                
            pool_contract = web3.eth.contract(address=pool_address, abi=PANCAKE_V3_POOL_ABI)
            
            liquidity = pool_contract.functions.liquidity().call()
            
            if liquidity > best_liquidity:
                best_liquidity = liquidity
                best_pool = pool_address
                best_fee = fee
                
        except Exception as e:
            continue
    
    return best_pool, best_fee

def estimate_tokens_v3(amount_in):
    return int(amount_in * 0.95)

def get_token_info(token_address, rpc_url=DEFAULT_RPC_URL):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    
    try:
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
    except Exception as e:
        print(f"Error getting token info: {str(e)}")
        return None

def buy_tokens_with_bnb_v3(token_address, amount_bnb, slippage=5, gas_price=5, rpc_url=DEFAULT_RPC_URL, private_key=None):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    token_address = web3.to_checksum_address(token_address)
    
    if private_key:
        account = web3.eth.account.from_key(private_key)
        address = account.address
        print(f"Using provided private key for address: {address}")
    else:
        raise ValueError("Private key is required")
    
    global CURRENT_WALLET_ADDRESS
    CURRENT_WALLET_ADDRESS = address
    
    balance_wei = web3.eth.get_balance(address)
    balance_bnb = web3.from_wei(balance_wei, 'ether')
    print(f"Wallet balance: {balance_bnb:.8f} BNB")
    
    amount_wei = web3.to_wei(amount_bnb, 'ether')
    
    if balance_wei < amount_wei:
        raise ValueError(f"Insufficient balance: {balance_bnb:.8f} BNB, needed {amount_bnb} BNB")
    
    router_contract = web3.eth.contract(address=web3.to_checksum_address(PANCAKE_V3_ROUTER), abi=PANCAKE_V3_ROUTER_ABI)
    factory_contract = web3.eth.contract(address=web3.to_checksum_address(PANCAKE_V3_FACTORY), abi=PANCAKE_V3_FACTORY_ABI)
    
    token_in = WBNB_ADDRESS
    token_out = token_address
    pool_address, pool_fee = find_best_pool(web3, factory_contract, token_in, token_out)
    
    if not pool_address:
        print(f"No pool found for token pair WBNB/{token_address}")
        pool_address, pool_fee = find_best_pool(web3, factory_contract, token_out, token_in)
        
        if not pool_address:
            raise ValueError(f"No pool found for token pair {token_address}/WBNB")
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
        'amountIn': amount_wei,
        'amountOutMinimum': amount_out_min,
        'sqrtPriceLimitX96': 0
    }
    
    router_function = router_contract.functions.swapV3ExactIn(swap_params)
    
    try:
        nonce = web3.eth.get_transaction_count(address)
        swap_txn = router_function.build_transaction({
            'from': address,
            'value': amount_wei,
            'gas': 500000,
            'gasPrice': web3.to_wei(str(gas_price), 'gwei'),
            'nonce': nonce,
            'chainId': 56
        })
        
        signed_txn = web3.eth.account.sign_transaction(swap_txn, private_key)

        print(f"Buying token using standard RPC method...")
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash = tx_hash.hex()
        
        print(f"Transaction sent! Hash: {tx_hash}")
        print(f"View on BSCScan: https://bscscan.com/tx/{tx_hash}")
        
        return tx_hash
    except Exception as e:
        print(f"Error executing V3 swap: {str(e)}")
        raise