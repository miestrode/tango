import error
import sniper
import build_json
import json
import time


try:
    open("../src/config.json", 'r')
except FileNotFoundError:
    run_build_json = build_json.gather_info("A configuration file does not exist. Would you like to build one? [True/False]", build_json.to_bool)

    if run_build_json:
        build_json.build_config()
    else:
        print(f"{error.LIGHT_BLUE}Okay, but keep in mind you cannot continue without a configuration file. Exiting now.")
        time.sleep(1)
        exit(1)

file = open("../src/config.json", 'r')
configuration_json = json.loads(file.read())
accounts = []

for account in configuration_json["accounts"]:
    if account["code"]:
        accounts.append(sniper.GiftCodeAccount(account["email"], account["password"]))
    else:
        accounts.append(sniper.Account(account["email"], account["password"]))

session = sniper.Session(accounts, configuration_json["target"], configuration_json["offset"], configuration_json["requests"], configuration_json["optimize"])
session.run()