# Cosmos WalletMon

Cosmos WalletMon is a simple script that helps send notifications whenever a wallet drops below a specified threshold balance. This was inspired by me always forgetting to check whether my Restake hot wallet had funds to keep auto-compounding delegate's balance.

# Support Chains

Chain data is obtained from the [Chain Registry](https://github.com/cosmos/chain-registry).

Any chain that has a chain_name set in the chain's `chain.json` and asset base in the `assetlist.json` files is supported.

# Usage

The easiest way to run this is using docker-compose.

## Docker-Compose

Clone the repository

`git clone https://github.com/Crypto-Chemistry/walletmon.git`

Move example.docker-compose.yml to docker-compose.yml

`mv example.docker-compose.yml docker-compose.yml`

Edit docker-compose.yml and modify the variables. After the `-a` flag, a list of space-separated addresses to monitor should be provided. These do not need to belong to the same chain. After the `-d` flag, add the Discord webhook for the channel that you want to receive low balance notifications on.

Example docker-compose.yml command segement:

```
command: "walletmon.py \
              -a kujira1tfknxt857r4lm8eh2py5n3yq00t3mq5eerh6qs clan1wg7nrqc29veuzw9p6ujhad697a3tpzl3zrfplr \ 
              -d https://discord.com/api/webhooks/1234567890123456789/abcdefghijklmnop-1A-2B3CD4-e5f6g7h8i9j10"
```

Build the image

`docker-compose build --no-cache`

Run the application (It acts as a one-shot similar to Restake. To configure it as a repeated service, see [Configuring a WalletMon Service](#configuring-a-walletmon-service))

`docker-compose run --rm walletmon`

## Running from source

Running this application from source is a bit more work to set up reliably and comes with additional requirements.

Python 3.10 or greater must be installed for this function properly. However, it has only been tested on Python 3.10.5 so far.

Clone the repository

`git clone https://github.com/Crypto-Chemistry/walletmon.git`

Switch to the repo directory

`cd walletmon`

Pull down the library dependencies

`pip3 install -r requirements.txt`

Run the walletmon.py script with the required arguments

`python3 walletmon.py -a address1 address2 address3 -d discord_webhook_url`

Example command:

```
python3 walletmon.py -a kujira1tfknxt857r4lm8eh2py5n3yq00t3mq5eerh6qs clan1wg7nrqc29veuzw9p6ujhad697a3tpzl3zrfplr \
                     -d https://discord.com/api/webhooks/1234567890123456789/abcdefghijklmnop-1A-2B3CD4-e5f6g7h8i9j10
```

## Update Instructions

To update to a newer version navigate to where the repo is cloned and run the following commands

```
git fetch --all
git pull
```

If using the Docker Compose method to run the application, make sure to force rebuild the image:

```
docker-compose kill
docker-compose build --no-cache
```

If running from source, make sure to reinstall the requirements.txt file in case new dependencies have been added:
`pip3 install -r requirements.txt`

# Configuring a WalletMon Service

To configure WalletMon as a service, first create a service file.

`sudo nano /etc/systemd/system/walletmon.service`

Copy the following contents into the `walletmon.service` file, replacing the WorkingDirectory variable with the path to where the repo is cloned.

```
[Unit]
Description=Cosmos Wallet Monitoring Service
Requires=docker.service
After=docker.service
Wants=walletmon.timer

[Service]
Type=oneshot
WorkingDirectory=/path/to/walletmon
ExecStart=/usr/bin/docker-compose run --rm walletmon

[Install]
WantedBy=multi-user.target
```

Next, create the timer that dictates how often the service is called.

`sudo nano /etc/systemd/system/walletmon.timer`

Copy the following contents into the `walletmon.timer` file. Adjust the OnCalendar variable to change how frequently the application runs. It's configured to run every hour by default.

```
[Unit]
Description=Cosmos Wallet Monitoring Timer

[Timer]
AccuracySec=1min
OnCalendar=*-*-* *:00:00

[Install]
WantedBy=timers.target
```

# Available Parameters

| Parameter            | Type                       | Required | Description                                                                |
|----------------------|----------------------------|----------|----------------------------------------------------------------------------|
| -a,--addresses       | String or multiple strings | Yes      | Addresses to check balances                                                |
| -d,--discord         | String                     | Yes      | Discord webhook url to send notifications to                               |
| -t,--threshold       | String or multiple strings | No       | Chain specific thresholds for wallet balances before sending notifications |
| -g,--globalthreshold | Int                        | No       | Global threshold for wallet balances before sending notifications          |