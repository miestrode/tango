# A simple way to communicate with the sniper.py file and snipe names, without needing technical knowledge
import subprocess
import src.sniper
import src.error


# Get the maximum latency of an available
def maximum_mojang_api_latency() -> int:
    """
    :return: Maximum latency (in milliseconds) of the Mojang API server
    """
    try:
        result = subprocess.Popen(["ping.exe", "api.mojang.com"], stdout=subprocess.PIPE).communicate()[0].__str__()
        return int(''.join(character for character in result.split(',')[-2] if character.isdigit()))
    except ValueError:
        return 0


print(f"{src.error.LIGHT_BLUE}Welcome to Tango, the open-source minecraft name sniper. Please enter your details.")

# Record details of the user, in order to perform the snipe
username = input(f"{src.error.GRAY}\nWhat's your account's email?\n{src.error.BLUE}{src.error.BOLD}> ")
password = input(f"{src.error.GRAY}\nWhat's your account's password?\n{src.error.BLUE}{src.error.BOLD}> ")
target_name = input(f"{src.error.GRAY}\nWhat name would you like to snipe?\n{src.error.BLUE}{src.error.BOLD}> ")

while True:
    offset_type = input(f"{src.error.GRAY}\nWhat offset type would you like to use? {src.error.BLUE}{src.error.BOLD}[smart/custom/none]\n> ")

    if offset_type in ("smart", "custom", "none"):
        break

    print(f"{src.error.GRAY}\nYour input must be \"smart\", \"custom\" or \"none\". Try again.")

offset = 0

while True:
    if offset_type == "custom":
        offset = input(f"{src.error.GRAY}\nWhat offset would you like (in milliseconds)?\n{src.error.BLUE}{src.error.BOLD}> ")

        try:
            offset = float(offset)
            break
        except ValueError:
            print(f"{src.error.GRAY}\nYour input must be a valid integer or decimal. Try again.")
            continue
    elif offset_type == "smart":
        print(f"{src.error.DARK_GRAY}{src.error.ITALIC}\nCalculating Mojang API server latency")
        offset = maximum_mojang_api_latency()

        if offset != 0:
            print(f"{src.error.DARK_GRAY} Offset is {offset}.")
        else:
            print(f"{src.error.DARK_GRAY} Failed to calculate server latency. Defaulting to 0.")
        break

print(f"{src.error.LIGHT_BLUE}\nThank you for entering your details. The details will now be verified.")

# Snipe the name
account = src.sniper.SnipeAccount(username, password)
account.snipe_username(target_name, offset)
