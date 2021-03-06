import asyncio
import time
import typing

import aiohttp
import stdiomask
import toml

import error


async def get_latency(client: aiohttp.ClientSession) -> float:
    """
    Get the latency to the Minecraft name changing API, to generate a good sniping offset

    :param client: The client used to request the website
    :return: The latency of a request to the website
    """
    start = time.time()

    await client.head("https://api.minecraftservices.com/minecraft/profile/name/")

    return time.time() - start


async def get_average_latency() -> float:
    """
    Get the average latency to the Minecraft name changing API, used as the offset for the sniper, in default settings

    :return: The average latency of the Minecraft name changing API, scaled up to be used as an offset
    """

    async with aiohttp.ClientSession() as client:
        return (sum(await asyncio.gather(*[get_latency(client) for _ in range(5)])) / 5) * 1000


def choice(to_convert: str) -> bool:
    """
    Custom "bool()" like implementation for info gathering

    :param to_convert: A value to convert into a boolean
    :return: A boolean, based on the original value
    """

    to_convert = to_convert.lower()

    if to_convert not in ("yes", "no", "y", "n"):
        raise ValueError(f"invalid literal for choice(): '{to_convert}'")

    return to_convert in ("yes", "y")


def gather_info(prompt: str, requested_type: typing.Callable) -> any:
    """
    Gather any information and check if it fits a certain type

    :param prompt: A prompt the users sees. It details what is to be inputted
    :param requested_type: A type you want the response from the user to have
    :return: A response from the user, in the type specified
    """

    response = input(f"{error.GRAY}{prompt}{error.BLUE}\n> ")

    try:
        return requested_type(response)
    except ValueError as exception:
        error.InputTypeError(f"Input is not of type {requested_type.__name__}", exception.__str__())


def gather_secret(prompt: str, requested_type: typing.Callable) -> str:
    """
    Get an input from the user that is hidden, like entering a password.

    :param requested_type: A prompt the users sees. It details what is to be inputted
    :type prompt: objectA type you want the response from the user to have
    :return: A response from the user, in the type specified
    """

    response = stdiomask.getpass(f"{error.GRAY}{prompt}{error.BLUE}\n> ")

    try:
        return requested_type(response)
    except ValueError as exception:
        error.InputTypeError(f"Input is not of type {requested_type.__name__}", exception.__str__())


def to_ordinal(number: int) -> str:
    """
    Turns a number into an ordinal

    :param number: Some number you want to to turn into an ordinal
    :return: The ordinal representation of the given number
    """

    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(number % 10, 4)]

    if (number % 100) in range(11, 14):
        suffix = 'th'

    return str(number) + suffix


def print_logo() -> None:
    """
    Print the Tango logo
    """
    print(f"""{error.WHITE} 88                                            
888                                            
888                                            
888888  8888b.   88888b.    .d88b.    .d88b.      
888        "88b  888 "88b  d88P"88b  d88""88b     
888    .d888888  888  888  888  888  888  888     
Y88b.  888  888  888  888  Y88b 888  Y88..88P  d8b 
 "Y888 "Y888888  888  888   "Y88888   "Y88P"   Y8P 
                                888              
                           Y8b d88P              
                            "Y88P"               """)


def build_config() -> None:
    """
    Build the configuration file so sessions can be performed
    """

    print(f"\nNote that:{error.GRAY}\n"
          f"{error.BLUE}*{error.GRAY} Your sniping offset is gradually changed every snipe to better adapt to your computer.\n"
          "Using this program will overwrite the current offset value.\n\n"
          f"{error.BLUE}*{error.GRAY} Some configuration settings are not filled out here, and are set to default values.\n"
          "You can manually create or modify your configuration file to have control over these settings that.\n")

    account_count = gather_info("How many accounts would you like to use?", int)
    accounts = []

    for index in range(account_count):
        account_index = to_ordinal(index + 1)

        email = gather_info(f"\nEnter the {account_index} account's email:", str)
        password = gather_secret(f"Enter the {account_index} account's password:", str)

        use_security_questions = gather_info(f"Does the {account_index} account use security questions? [Yes/No]", choice)
        answers = []

        if use_security_questions:
            answers = [gather_info(f"Enter the {to_ordinal(index + 1)} account's {to_ordinal(rank + 1)} security answer:", str) for rank in range(2)]

        has_profile = gather_info(f"Does the {account_index} account have a profile? (If not, you need to claim a gift code on this account before proceeding) [Yes/No]",
                                  choice)

        accounts.append({"email": email, "password": password, "answers": answers, "exists": has_profile})

    target_name = gather_info("\nWhat name you want to snipe?", str)

    with open("config.toml", 'w') as file:
        toml.dump(
            {
                "accounts": accounts,
                "timing": {
                    "offset": asyncio.run(get_average_latency()) - 10,
                    "system": "macho",
                    "optimize": True
                },
                "request": {
                    "count": 3,
                    "target": target_name
                }
            }, file
        )


if __name__ == "__main__":
    print_logo()

    # Announce the programs purpose, and build the configuration file
    print(f"{error.GRAY}Welcome to the {error.BLUE}json builder{error.GRAY}. This program will create a configuration file for you.")
    build_config()
