import error
import sniper
import build_config

import toml

import asyncio
import time
import getpass


def run_sniper():
    try:
        open("config.toml", 'r')
    except FileNotFoundError:
        run_build_json = build_config.gather_info("\nA configuration file does not exist. Would you like to build one? [Yes/No]", build_config.choice)

        if run_build_json:
            build_config.build_config()
        else:
            print(f"\n{error.GRAY}Okay, but keep in mind you cannot continue without a configuration file. Exiting now.")
            time.sleep(1)
            exit(1)

    with open("config.toml", 'r') as file:
        configuration_json = toml.loads(file.read())

    accounts = []

    for account in configuration_json["accounts"]:
        if account["exists"]:
            accounts.append(sniper.GiftCodeAccount(account["email"], account["password"], account["answers"]))
        else:
            accounts.append(sniper.Account(account["email"], account["password"], account["answers"]))

    sniping_session = sniper.Session(accounts, configuration_json["request"]["target"], configuration_json["timing"]["offset"], configuration_json["request"]["count"], configuration_json["timing"]["system"], configuration_json["timing"]["optimize"])
    asyncio.run(sniping_session.run())


if __name__ == "__main__":
    build_config.print_logo()
    print(f"{error.GRAY}\nWelcome to {error.BLUE}Tango's runtime{error.GRAY}. You can issue a snipe using this program.")

    run_sniper()
    getpass.getpass(f"{error.GRAY}\nSniping session ended. Press {error.BLUE}Enter{error.GRAY} to exit.")
