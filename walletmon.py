#! /usr/bin/python3

import argparse
import subprocess
import json
import ast
from discord_webhook import DiscordWebhook
import re
import requests

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

    args = parser.parse_args()

    if args.discord_webhook_url:
        global discord_webhook_url
        discord_webhook_url=args.discord_webhook_url
        print(discord_webhook_url)

    wallets=[]
    if args.addresses:
        for address in args.addresses:
            wallets.append(map_address_to_chain(address))
    print(wallets)
    for wallet in wallets:
        wallet['balance']=check_balance(wallet)
        check_threshold(wallet)

def map_address_to_chain(address):
    pattern = re.compile(r"""(?x)
    (?P<kujira>^kujira.*) |
    (?P<clan>^clan.*) |
    (?P<secret>^secret.*) |
    (?P<cosmos>^cosmos.*)
    """)
    mo=pattern.fullmatch(address)
    match mo.lastgroup:
        case 'kujira':
            return {'address':address,
                    'chain': 'kujira',
                    'daemon': 'kujirad',
                    'denom': 'ukuji'}
        case 'clan':
            print("This is a clan address")
        case 'secret':
            print("This is a secret address")
        case 'cosmos':
            print("This is a cosmos address")
        case _:
            raise ValueError(f'Unknown pattern for {s!r}')

def check_balance(wallet=dict):
    url=f"https://rest.cosmos.directory/{wallet['chain']}/cosmos/bank/v1beta1/balances/{wallet['address']}/by_denom?denom={wallet['denom']}"
    query = requests.get(url)
    results=json.loads(query.text)
    balance = (results['balance']['amount'])
    print(f"Wallet Balance for {wallet['address']}: {balance}{wallet['denom']}")
    # return balance

def send_discord_message(content=str,discord_webhook_url=str):
    webhook = DiscordWebhook(url=discord_webhook_url, content=content)
    response = webhook.execute()

def check_threshold(wallet=dict):
    print("Matching Threshold")
    match wallet['denom']:
        case 'ukuji':
            threshold=1000000
        case 'uscrt':
            threshold=10000000
    if int(wallet['balance']) < threshold:
        content=""
        content+=f"{wallet['address']}: {wallet['balance']}{wallet['denom']}"
        print(content)
        print("Calling send_discord_message")
        send_discord_message(content,discord_webhook_url)

if __name__ == "__main__":
    main()