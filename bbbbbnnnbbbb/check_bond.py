from web3 import Web3

DEFAULT_RPC_URL = "https://bsc-dataseed.binance.org/"
PANCAKE_V3_FACTORY = "0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865"
WBNB_ADDRESS = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
FEE_TIERS = [100, 500, 2500, 3000, 10000]

PANCAKE_V3_FACTORY_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "tokenA", "type": "address"},
            {"internalType": "address", "name": "tokenB", "type": "address"},
            {"internalType": "uint24", "name": "fee", "type": "uint24"}
        ],
        "name": "getPool",
        "outputs": [
            {"internalType": "address", "name": "pool", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

TOKEN_ABI = [
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
        "constant": True, 
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]

def check_token_info(token_address, rpc_url=DEFAULT_RPC_URL):
    try:
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        token_address = web3.to_checksum_address(token_address)

        token_contract = web3.eth.contract(address=token_address, abi=TOKEN_ABI)

        try:
            name = token_contract.functions.name().call()
            symbol = token_contract.functions.symbol().call()
            decimals = token_contract.functions.decimals().call()
            return name, symbol, decimals
        except Exception:
            return None, None, None
            
    except Exception:
        return None, None, None

def is_token_bonded(token_address, verbose=True, rpc_url=DEFAULT_RPC_URL):
    try:
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        token_address = web3.to_checksum_address(token_address)
        if verbose:
            name, symbol, decimals = check_token_info(token_address, rpc_url)
            if symbol:
                print(f"Checking if {symbol} ({name}) is bonded...")
            else:
                print(f"Checking if token {token_address} is bonded...")
        
        factory_contract = web3.eth.contract(
            address=web3.to_checksum_address(PANCAKE_V3_FACTORY),
            abi=PANCAKE_V3_FACTORY_ABI
        )

        for fee in FEE_TIERS:
            try:
                pool = factory_contract.functions.getPool(token_address, WBNB_ADDRESS, fee).call()
                if pool != "0x0000000000000000000000000000000000000000":
                    if verbose:
                        print(f"✅ Token is bonded! Found liquidity pool with fee tier: {fee/10000:.4f}%")
                        print(f"Pool address: {pool}")
                    return True
            except Exception:
                continue

        for fee in FEE_TIERS:
            try:
                pool = factory_contract.functions.getPool(WBNB_ADDRESS, token_address, fee).call()
                if pool != "0x0000000000000000000000000000000000000000":
                    if verbose:
                        print(f"✅ Token is bonded! Found reverse liquidity pool with fee tier: {fee/10000:.4f}%")
                        print(f"Pool address: {pool}")
                    return True
            except Exception:
                continue
        
        if verbose:
            print("❌ Token is NOT bonded. No liquidity pool found on PancakeSwap V3.")
        return False
            
    except Exception as e:
        if verbose:
            print(f"Error checking if token is bonded: {str(e)}")
        return False 