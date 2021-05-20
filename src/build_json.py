import error

import json
import typing


def to_bool(to_convert: str) -> bool:
    """
    Custom "bool()" like implementation for info gathering

    :param to_convert: A value to convert into a boolean
    :return: A boolean, based on the original value
    """

    if to_convert not in ("True", "False"):
        raise ValueError(f"invalid literal for bool(): '{to_convert}'")

    return to_convert == "True"


def gather_info(prompt: str, requested_type: typing.Callable) -> any:
    """
    Gather any information and check if it fits a certain type

    :param prompt: A prompt the users sees. It details what is to be inputted
    :param requested_type: A type you want the response from the user to have
    :return: A response from the user
    """

    response = input(f"{error.GRAY}{prompt}{error.BLUE}\n> ")

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
    print(f"""
{error.LIGHT_BLUE}Welcome to the json builder. This program will create a configuration file for you.

Note that:{error.GRAY}

{error.LIGHT_BLUE}*{error.GRAY} Your sniping offset is gradually changed every snipe to better adapt to your computer.
Using this program will overwrite the current offset value.
{error.LIGHT_BLUE}*{error.GRAY} Make sure no one is watching.
You are about to enter {error.LIGHT_RED}sensitive{error.GRAY} information.
{error.LIGHT_BLUE}*{error.GRAY} Some configuration settings are not filled out here, and are set to default values.
You can manually create or modify your configuration file to prevent that.
""")

    account_count = gather_info("How many accounts would you like to use?", int)
    accounts = []

    for index in range(account_count):
        email = gather_info(f"\nEnter the {to_ordinal(index + 1)} account's email:", str)

        password = gather_info(f"Enter the {to_ordinal(index + 1)} account's password:", str)

        answers = None
        use_security_questions = gather_info(f"Does the {to_ordinal(index + 1)} account have security questions? [True/False]", to_bool)

        if use_security_questions:
            answers = [gather_info(f"Enter the {to_ordinal(index + 1)} account's {to_ordinal(rank + 1)} security answer:", str) for rank in range(2)]

        has_profile = gather_info(f"Does the {to_ordinal(index + 1)} account have a profile? [True/False]", to_bool)

        accounts.append({"email": email, "password": password, "answers": answers, "profile": has_profile})

    target_name = gather_info("\nEnter the name you want to snipe:", str)

    with open("../src/config.json", 'w') as file:
        json.dump({"accounts": accounts, "requests": 3, "offset": 400, "optimize": True, "target": target_name}, file, indent=4)


if __name__ == "__main__":
    print_logo()
    build_config()
