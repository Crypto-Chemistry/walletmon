#! /usr/bin/python3

import argparse
import json
from discord_webhook import DiscordWebhook,DiscordEmbed
import re
import requests
import git
import pathlib
import os

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--addresses",
        nargs='+',
        dest="addresses",
        type=str,
        required=True,
        help="Addresses to check balances"
    )
    parser.add_argument(
        "-d",
        "--discord",
        dest="discord_webhook_url",
        type=str,
        required=True,
        help="Discord webhook url to send notifications to"
    )
    parser.add_argument(
        "-l",
        "--label",
        dest="label",
        type=str,
        required=False,
        help="Wallet Label"
    )
    parser.add_argument(
        "-t",
        "--threshold",
        nargs='+',
        dest="threshold",
        required=False,
        help="Chain specific thresholds for wallet balances before sending notifications"
    )
    parser.add_argument(
        "-g",
        "--globalthreshold",
        dest="global_threshold",
        type=int,
        required=False,
        help="Global threshold for wallet balances before sending notifications"
    )
    parser.add_argument(
        "-u",
        "--userid",
        dest="discord_uuid",
        type=str,
        required=False,
        help="Discord User by UUID to tag in alerts"
    )

    args = parser.parse_args()

    if args.discord_webhook_url:
        global discord_webhook_url
        discord_webhook_url=args.discord_webhook_url
    else:
        print("Error - Please supply a Discord webhook URL with the '-d' flag")
        quit()

    if args.threshold:
        thresholds=parse_chain_thresholds(args.threshold)

    if args.global_threshold:
        threshold=args.global_threshold
    else:
        threshold=1000000

    update_chain_registry()

    wallets=[]
    if args.addresses:
        for address in args.addresses:
            wallets.append(map_address_to_chain(address))
    else:
        print("Error - Please supply addresses to monitor using the '-a' flag")
        quit()

    for wallet in wallets:
        if args.label:
            wallet['label'] = args.label
        else:
            wallet['label'] = None
        if wallet['denom'] in thresholds.keys():
            wallet['balance']=check_balance(wallet)
            check_threshold(wallet,int(thresholds[wallet['denom']]),args.discord_uuid)
        else:
            wallet['balance']=check_balance(wallet)
            check_threshold(wallet,threshold,args.discord_uuid)

def update_chain_registry():
    git_url="https://github.com/cosmos/chain-registry.git"
    repo_dir="chain-registry"
    script_dir=pathlib.Path( __file__ ).parent.absolute()
    repo_path=os.path.join(script_dir,repo_dir)
    if not os.path.exists(repo_path):
        git.Repo.clone_from(git_url, repo_path)
    repo = git.Repo(repo_path)
    origin = repo.remotes.origin
    origin.pull()

def map_address_to_chain(address=str):
    repo_dir="chain-registry"
    script_dir=pathlib.Path( __file__ ).parent.absolute()
    repo_path=os.path.join(script_dir,repo_dir)
    chain_json=find_chain_json(address)
    f = open(chain_json)
    chain_data=json.load(f)

    asset_json=chain_json.replace("chain.json","assetlist.json")
    f = open(asset_json)
    asset_data=json.load(f)

    #Get chain name from chain.json
    try:
        chain_name=chain_data['chain_name']
    except KeyError as e:
        print("KeyError - Chain name likely does not exist in chain-registry")
        quit()

    #Get base denom from assetlist.json
    try:
        chain_base_denom=asset_data['assets'][0]['base']
    except KeyError as e:
        print("KeyError - Fee denomination likely does not exist in chain-registry")
        quit()

    return {'address':address,
            'chain': chain_name,
            'denom': chain_base_denom}

def find_chain_json(address=str):
    repo_dir="chain-registry"
    script_dir=pathlib.Path( __file__ ).parent.absolute()
    repo_path=os.path.join(script_dir,repo_dir)
    filenames = []

    #Retrieve all json files and add to array
    testnet_folder="testnets"
    for root, dirs, files in os.walk(repo_path):
        for file in files:
            if file.endswith(".json") and testnet_folder not in root:
                filenames.append(os.path.join(root, file))

    #Get Human Readable Portion of address
    hrp=re.split('1',address)[0]

    #Match the prefix and return the file name
    pattern = re.compile(f'\"bech32_prefix\":\s\"{hrp}\"')
    chain_json=""
    for file in filenames:
        for i, line in enumerate(open(file)):
            for match in re.finditer(pattern, line):
                chain_json=file
                break
    return chain_json

def check_balance(wallet=dict):
    url=f"https://rest.cosmos.directory/{wallet['chain']}/cosmos/bank/v1beta1/balances/{wallet['address']}/by_denom?denom={wallet['denom']}"
    query = requests.get(url)
    results=json.loads(query.text)
    balance = (results['balance']['amount'])
    print(f"Wallet Balance for {wallet['address']}: {balance}{wallet['denom']}")
    return balance

def send_discord_message(discord_webhook_url, address, label, balance,**kwargs):
    embed = DiscordEmbed(title="Low Balance Alert", description="", color='e53935')
    embed.add_embed_field(name='Address', value=address, inline=False)
    if label:
        embed.add_embed_field(name='Label', value=label, inline=False)
    embed.add_embed_field(name='Balance', value=balance, inline=False)

    if 'uuid' in kwargs:
        webhook = DiscordWebhook(url=discord_webhook_url,content=f"<@{kwargs['uuid']}>")
    else:
        webhook = DiscordWebhook(url=discord_webhook_url)
    webhook.add_embed(embed)
    response = webhook.execute()

def check_threshold(wallet=dict,threshold=int,discord_uuid=str):
    if int(wallet['balance']) < threshold:
        if discord_uuid:
            send_discord_message(discord_webhook_url,wallet['address'], wallet['label'], f"{wallet['balance']}{wallet['denom']}", uuid=discord_uuid)
        else:
            send_discord_message(discord_webhook_url, wallet['address'], wallet['label'], f"{wallet['balance']}{wallet['denom']}")

def parse_chain_thresholds(thresholds=str):
    threshold_mapping={}
    for threshold in thresholds:
        chain=re.sub(r'[^a-zA-Z]', "", threshold)
        amount=re.sub("\D", "", threshold)
        threshold_mapping[chain]=amount
    return threshold_mapping

if __name__ == "__main__":
    main()