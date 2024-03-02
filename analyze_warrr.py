from web3 import Web3
import json
import requests
import time
import os
import sys
from datetime import datetime

contract_address = "0xcdaf240c90f989847c56ac9dee754f76f41c5833"
bsc_rpc = 'https://bsc-dataseed.binance.org/'
bsc_api_endpoint = "https://api.bscscan.com/api"
bsc_api_key = "YOUR_API_KEY"
bsc_api_cps = 4
chunk_size = 1000000                                # Number of blocks to fetch per request (reduce if hitting records limit)
output_filename = 'warrr_analysis_report.txt'       # report filename
transfer_events_filename = 'transfer_events.json'   # filename to save transfer events
warrrABI = "warrrABI.json"                          # warrr contract abi in json array 
rr_json = "rr.json"                                 # json array of addresses

# addresses that the purpose or owner is known
known_addresses = [
    {"address": "0xcdaf240c90f989847c56ac9dee754f76f41c5833", "purpose": "wARRR contract  "},
    {"address": "0xabf1a0039c3e5741d1c816a1685b455a06e0dad4", "purpose": "wARRR multisig  "},
    {"address": "0x5502920b1c231d3b4d8f124658c447a72b72db4d", "purpose": "wARRR staking   "},
    {"address": "0xf01575e88e5c9e1fec464128096106155458e2a1", "purpose": "liquidity pool  "},
    {"address": "0x4FF60F02e7b10D1d06fb5930AC010e0e1A99f3f3", "purpose": "bridge primary  "},
    {"address": "0x8a0AcB5D2D71A882Be0557FB8c02d57Ac1f6d2ac", "purpose": "bridge deposit  "},
    {"address": "0x820f92c1B3aD8E962E6C6D9d7CaF2a550Aec46fB", "purpose": "tip.cc bot      "},
    {"address": "0xA05f7dB550Bd1C84e6d7D7a480a369E94Fa901B3", "purpose": "fee wallet      "},
    {"address": "0x472486b3f80f43265c89C0f709D384b677a05771", "purpose": "contract owner  "},
    {"address": "0xf2e98C90322CBf7cc691BcC2eA0c0B9A39F99d48", "purpose": "deployer        "}
]

# Convert known addresses to checksum format and map them by address for easy lookup
known_addresses_map = {Web3.to_checksum_address(addr["address"]): addr["purpose"] for addr in known_addresses}

# Check if rr.json exists
if os.path.exists(rr_json):
    # Load the RR addresses from rr.json
    with open(rr_json, 'r') as file:
        rr_addresses = set(json.load(file))
        # Convert to checksum addresses for consistent comparison
        rr_addresses = {Web3.to_checksum_address(addr) for addr in rr_addresses}
else:
    # If rr.json does not exist, initialize rr_addresses as an empty set
    rr_addresses = set()

def fetch_transfer_events(contract_address, bsc_api_key):
    all_transfer_events = []  # To store all transfer events
    
    # Get the block number of the earliest transfer event
    startblock = get_start_block(contract_address, bsc_api_key)
    
    # Fetch transfer events in chunks
    current_block = get_current_block(bsc_api_key)
    
    total_chunks = (current_block - startblock) // chunk_size
    chunks_processed = 0
    
    while startblock < current_block:
        endblock = min(startblock + chunk_size - 1, current_block)
        print(f"Requesting transfer data | chunk {chunks_processed + 1} of {total_chunks + 1} ({total_chunks - chunks_processed} remaining)")

        transfer_events = fetch_events_in_range(contract_address, startblock, endblock, bsc_api_key)
        all_transfer_events.extend(transfer_events)
        startblock += chunk_size
        chunks_processed += 1

        # Obey! 
        time.sleep(1 / bsc_api_cps)
    
    return all_transfer_events

def get_start_block(contract_address, bsc_api_key):
    # Fetch the first transfer event to determine the start block
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "page": 1,
        "offset": 1,
        "sort": "asc",
        "apikey": bsc_api_key,
    }
    response = requests.get(bsc_api_endpoint, params=params)
    result = response.json()
    
    if 'status' in result and result['status'] == '0':
        print(f"Error: {result['result']}")
        sys.exit(1)  # Exit with error status
    elif 'result' in result and len(result['result']) > 0:
        return int(result['result'][0]['blockNumber'])
    else:
        return 0  # No transfer events found

def fetch_events_in_range(contract_address, startblock, endblock, bsc_api_key):
    params = {
        "module": "account",
        "action": "tokentx",
        "contractaddress": contract_address,
        "startblock": startblock,
        "endblock": endblock,
        "apikey": bsc_api_key,
    }
    response = requests.get(bsc_api_endpoint, params=params)
    result = response.json()
    if 'result' in result:
        return result['result']
    else:
        return []  # No transfer events found

def get_current_block(bsc_api_key):
    params = {
        "module": "proxy",
        "action": "eth_blockNumber",
        "apikey": bsc_api_key,
    }
    response = requests.get(bsc_api_endpoint, params=params)
    result = response.json()
    if 'result' in result:
        return int(result['result'], 16)
    else:
        return 0  # Failed to fetch current block

# Save transfer events to a JSON file
def save_transfer_events_to_file(transfer_events, filename):
    with open(filename, 'w') as file:
        json.dump(transfer_events, file, indent=4)

# Load transfer events from a JSON file
def load_transfer_events_from_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)

# Update user
print(f"Connecting to BSCscanAPI")
print(f"Requesting all wARRR transfers in {chunk_size} block chunks")

# Check if the filename argument is provided
if len(sys.argv) > 1:
    transfer_events_filename = sys.argv[1]
    # Check if transfer events data file exists
    if os.path.exists(transfer_events_filename):
        print(f"Loading transfer events from {transfer_events_filename}...")
        transfer_events = load_transfer_events_from_file(transfer_events_filename)
        print("Transfer events loaded successfully.")
    else:
        print(f"File '{transfer_events_filename}' does not exist. Fetching transfer events...")
        transfer_events = fetch_transfer_events(contract_address, bsc_api_key)
        print("Transfer events fetched successfully.")
        # Save transfer events to a JSON file
        save_transfer_events_to_file(transfer_events, transfer_events_filename)
else:
    print("Fetching transfer events...")
    transfer_events = fetch_transfer_events(contract_address, bsc_api_key)
    print("Transfer events fetched successfully.")
    # Save transfer events to a JSON file
    save_transfer_events_to_file(transfer_events, transfer_events_filename)

addresses = set()
if transfer_events:
    print(f"Number of transfers found: {len(transfer_events)}")
    for event in transfer_events:
        from_address = event['from']
        to_address = event['to']
        addresses.add(Web3.to_checksum_address(from_address))
        addresses.add(Web3.to_checksum_address(to_address))

    print(f"Unique addresses: {len(addresses)}")
else:
    print("Failed to fetch transfer events or no events found.")

# Initialize counters and sum for RR addresses
rr_balance_sum = 0
rr_address_count_with_balance = 0

# Connect to BSC RPC
print(f"Connecting to BSC RPC")
w3 = Web3(Web3.HTTPProvider(bsc_rpc))
print(f"Connection established: {w3.is_connected()}")
print(f"Fetching balances for all detected addresses...")

# Load the wARRR token contract ABI
with open(warrrABI, 'r') as abi_file:
    wARRR_abi = json.load(abi_file)

# Initialize the wARRR token contract
wARRR_contract = w3.eth.contract(address=Web3.to_checksum_address(contract_address), abi=wARRR_abi)

# Fetch the total supply for percentage calculations
total_supply_raw = wARRR_contract.functions.totalSupply().call()
total_supply = total_supply_raw / 10**8 # convert arrrtoshis to 8 decimals

# Dictionary to hold address details, including RR addresses
address_details = {}

# Fetch balances and classify addresses
total_addresses = len(addresses.union(rr_addresses))
address_counter = 0

for addr in addresses.union(rr_addresses):  # Ensure RR addresses are included in the check
    address_counter += 1
    balance_raw = wARRR_contract.functions.balanceOf(addr).call()
    balance = balance_raw / 10**8 # convert arrrtoshis to 8 decimals
    percentage_of_supply = (balance / total_supply) * 100 if total_supply else 0
    purpose = known_addresses_map.get(addr, "Unknown")
    
    # Check if address is in RR list and update counters and sum
    if addr in rr_addresses:
        rr_balance_sum += balance
        if balance > 0:
            rr_address_count_with_balance += 1
    
    address_details[addr] = {
        "balance": balance, 
        "percentage_of_supply": percentage_of_supply, 
        "purpose": purpose
    }

    print(f"Checking balances | address {address_counter} of {total_addresses} ({total_addresses - address_counter} remaining)  {balance} wARRR")

# Get the current block height
current_block_height = w3.eth.block_number

# Get the current date and time in UTC
current_utc_time = datetime.utcnow()

# Calculate total number of unknown addresses and sum of their balances
unknown_address_count = 0
unknown_addresses_balance_sum = 0
non_zero_balance_address_count = 0
known_address_count = 0
known_addresses_balance_sum = 0
known_non_zero = 0

for addr, details in address_details.items():
    if details["purpose"] == "Unknown" and addr not in rr_addresses:
        unknown_address_count += 1
        unknown_addresses_balance_sum += details["balance"]
        if details["balance"] > 0:
            non_zero_balance_address_count += 1
    elif details["purpose"] != "Unknown" and addr not in rr_addresses:
        known_address_count += 1
        known_addresses_balance_sum += details["balance"]
        if details["balance"] > 0:
            known_non_zero += 1

# Get circulating supply (supply less primary address balalnce)
circulating_supply = total_supply
primary_balance = address_details.get("0xaBF1a0039c3e5741D1C816A1685B455A06E0daD4", {}).get("balance", 0)
circulating_supply -= primary_balance

# Sort addresses by balance in descending order
sorted_known_addresses = sorted(address_details.items(), key=lambda x: x[1]["balance"], reverse=True)

# Write results to a file as a report
with open(output_filename, 'w') as file:
    file.write("wARRR HOLDINGS ANALYSIS REPORT\n\n")

    file.write(f"creation time:       {current_utc_time} UTC\n")
    file.write(f"BSC chain height:    {current_block_height}\n")
    file.write(f"contract address:    {contract_address}\n")
    file.write(f"total transfers:     {len(transfer_events)}\n")
    file.write(f"total supply:        {total_supply} wARRR\n")
    file.write(f"circulating supply:  {circulating_supply}\n")

    file.write(f"\n---------------------------------------------------------------\n")

    file.write(f"\nBridge Round Robin Summary:\n")
    file.write(f"total addresses:     {len(rr_addresses)}\n")
    file.write(f"non-zero addresses:  {rr_address_count_with_balance}\n")
    file.write(f"total wARRR held:    {rr_balance_sum}\n")

    file.write(f"\nKnown Address Summary:\n")
    file.write(f"total addresses:     {known_address_count}\n")
    file.write(f"non-zero addresses:  {known_non_zero}\n")
    file.write(f"total wARRR held:    {known_addresses_balance_sum}\n")

    file.write(f"\nUnknown Address Summary:\n")
    file.write(f"total addresses:     {unknown_address_count}\n")
    file.write(f"non-zero addresses:  {non_zero_balance_address_count}\n")
    file.write(f"total wARRR held:    {unknown_addresses_balance_sum}\n")

    file.write(f"\n---------------------------------------------------------------\n")

    file.write("\nKnown Addresses:\n")
    for addr, details in sorted_known_addresses:
        if details["purpose"] != "Unknown":
            file.write(f"Address: {addr} {details['purpose']}  Balance: {details['balance']} ({details['percentage_of_supply']:.6f}%)\n")

    file.write(f"\nUnknown Addresses:\n")
    unknown_addresses_sorted = sorted(
        ((addr, details) for addr, details in address_details.items() 
        if details["purpose"] == "Unknown" and addr not in rr_addresses),
        key=lambda x: x[1]["balance"],
        reverse=True
    )
    for addr, details in unknown_addresses_sorted:
        file.write(f"Address: {addr}, Balance: {details['balance']}\n")

print(f"summary report created: {output_filename}")
print(f"later aligator")
