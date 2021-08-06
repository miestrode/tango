import error

import aiohttp
import bs4

import asyncio
import warnings
import datetime
import toml
import time
import platform

# Compatibility with windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Make the program ignore warnings, such as some coroutines never being awaited
warnings.simplefilter("ignore")


async def macho_availability_time(username: str) -> float:
    """
    Sends a request to CoolKidMacho's API and returns the time of availability of that name

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    async with aiohttp.ClientSession() as session:
        print(f"\nGetting availability time for {error.BLUE}{username}{error.GRAY} from Macho's API.")

        # Macho's API can get name drop times, as this is impossible since Mojang disabled the use of the "timestamp" parameter since 2020
        async with session.get(f"http://api.coolkidmacho.com/droptime/{username}") as drop_time_response:
            if drop_time_response.status != 200:
                print(f"Checking if {error.BLUE}{username}{error.GRAY} is available or unavailable.")

                # Unfortunately, the API doesn't distinguish between available and unavailable names. So we have to send a second call to the Mojang API
                async with session.get(f"https://account.mojang.com/available/minecraft/{username}") as availability_response:
                    if await availability_response.text() == "TAKEN":
                        error.UsernameUnavailableError(await availability_response.text())

                return 0  # The name is available, so it's "available" in 0 seconds

            return (await drop_time_response.json())["UNIX"] - time.time()


async def name_mc_availability_time(username: str) -> float:
    """
    Sends a request to nameMC and gets the availability time off the HTML source code

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    async with aiohttp.ClientSession() as session:
        print(f"\nGetting availability time for {error.BLUE}{username}{error.GRAY} from nameMC.")

        # Send a request to nameMC and get HTML as a response. That is the source code of the page
        async with session.get(f"https://namemc.com/search?q={username}") as html_response:
            html = bs4.BeautifulSoup(await html_response.text(), "html.parser")

            if html.find("title", text="Please Wait... | Cloudflare"):
                error.UnavailableTimerError("NameMC turned on CloudFlare")

            # Attempts to find the availability time. If it fails, the username is either unavailable, or available
            availability_time = html.find("time", {"id": "availability-time"})["datetime"]

            if not availability_time:
                print(f"Checking if {error.BLUE}{username}{error.GRAY} is available or unavailable.")

                if not html.find("div", text="Available"):
                    error.UsernameUnavailableError("TAKEN")

                return 0

            unix_availability_time = (datetime.datetime.strptime(availability_time, "%Y-%m-%dT%H:%M:%S.000Z") - datetime.datetime(1970, 1, 1)).total_seconds()

            return unix_availability_time - time.time()


class Account:
    def __init__(self, email: str, password: str, answers: list[str]) -> None:
        """
        Storage for a basic Minecraft account for sniping

        :param email: The accounts email
        :param password: The accounts password
        :param answers: The answers to the security questions if needed
        """

        self.email = email
        self.password = password
        self.security_answers = answers
        self.session = None
        self.authorization_header = None

    async def authenticate(self) -> None:
        """
        Authenticate this account, to access restricted parts of the Mojang API
        """

        print(f"\nAuthenticating {error.BLUE}{self.email}{error.GRAY}.")

        async with aiohttp.ClientSession() as session:
            async with session.post("https://authserver.mojang.com/authenticate", headers={"Content-Type": "application/json"},
                                    json={"username": self.email, "password": self.password}) as authentication_response:
                # Only feasible response code is 403 or 200
                if authentication_response.status != 200:
                    error.InvalidCredentialsError(await authentication_response.text())

                print(f"{error.BLUE}{self.email}{error.GRAY} exists.")

                access_token = (await authentication_response.json())["accessToken"]
                self.authorization_header = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Accept": "application/json"}

                # Save an API call by getting the security questions. The API returns "[]" when no security questions are present
                async with session.get("https://api.mojang.com/user/security/challenges", headers=self.authorization_header) as question_response:
                    response_json = await question_response.json()

                    if not response_json:
                        questions = [question["answer"]["id"] for question in response_json]

                        print(f"{error.BLUE}{self.email}{error.GRAY} has security questions, sending answers.")

                        # Retrieve answers as supplied by the user
                        answers = [{"id": key, "answer": self.security_answers[index]} for key, index in enumerate(questions)]

                        # Send the answers back
                        async with session.post("https://api.mojang.com/user/security/location", headers=self.authorization_header, json=answers) as answer_response:
                            if answer_response.status != 204:
                                error.SecurityAnswerError(await answer_response.text())

    async def send_snipe_request(self, target_name: str, index: int) -> datetime.datetime:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        :param index: The order of this snipe request
        """

        current_time = datetime.datetime.now()
        print(f"{error.DARK_GRAY}{index}){error.GRAY} Attempting to snipe {error.BLUE}{target_name}{error.GRAY} to {error.BLUE}{self.email}{error.GRAY} at "
              f"{error.BLUE}{current_time.strftime('%H:%M:%S.%f')}{error.GRAY}.")

        # Send a request to change the account's name
        async with aiohttp.ClientSession() as session:
            async with session.put(f"https://api.minecraftservices.com/minecraft/profile/name/{target_name}", headers=self.authorization_header) as name_change_response:
                result_time = datetime.datetime.now().strftime("%H:%M:%S.%f")

                if name_change_response.status == 200:
                    print(f"{error.BLUE}{index}){error.GRAY} Succeeded in sniping {error.BLUE}{target_name}{error.GRAY} to {error.BLUE}{self.email}{error.GRAY} at "
                          f"{error.BLUE}{result_time}{error.GRAY}.")
                else:
                    print(f"{error.RED}{index}){error.GRAY} Failed in sniping {error.BLUE}{target_name}{error.GRAY} to {error.BLUE}{self.email}{error.GRAY} at {error.BLUE}"
                          f"{result_time}{error.GRAY}.")

            await asyncio.sleep(0)  # Pass control

            return current_time


class GiftCodeAccount(Account):
    def __init__(self, email: str, password: str, answers: list[str]) -> None:
        """
        Storage for a basic Minecraft account with a gift code for sniping

        :param email: The accounts email
        :param password: The accounts password
        """

        super().__init__(email, password, answers)

    async def send_snipe_request(self, target_name: str, index: int) -> datetime.datetime:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        :param index: The order of this snipe request
        """

        current_time = datetime.datetime.now()
        print(f"{error.DARK_GRAY}{index}){error.GRAY} Attempting to create {error.BLUE}{target_name}{error.GRAY} for {error.BLUE}{self.email}{error.GRAY} at {error.BLUE}"
              f"{current_time.strftime('%H:%M:%S.%f')}{error.GRAY}.")

        async with self.session.post(f"https://api.minecraftservices.com/minecraft/profile", headers=self.authorization_header,
                                     json={"profileName": target_name}) as claim_response:
            result_time = datetime.datetime.now().strftime("%H:%M:%S.%f")

            if claim_response.status == 200:
                print(f"{error.BLUE}{index}){error.GRAY} Succeeded in creating {error.BLUE}{target_name}{error.GRAY} for {error.BLUE}{self.email}{error.GRAY} at {error.BLUE}"
                      f"{result_time}{error.GRAY}.")
            else:
                print(f"{error.RED}{index}){error.GRAY} Failed in creating {error.BLUE}{target_name}{error.GRAY} for {error.BLUE}{self.email}{error.GRAY} at {error.BLUE}"
                      f"{result_time}{error.GRAY}.")

        await asyncio.sleep(0)  # Pass control

        return current_time


class Session:
    def __init__(self, accounts: list[Account], target_name: str, offset: int, requests: int, timing_system: str, optimize_offset: bool) -> None:
        """
        A sniping session, where you attempt to claim a name to any of your accounts

        :param offset: The amount of milliseconds by which the sniper will be early
        :param requests: The amount of requests to be sent with each account
        :param optimize_offset: Whether or not you want to optimize your offset at the end of the session
        :param accounts: A list of accounts you will use
        :param timing_system: The way in which you want to calculate availability time for the name
        :param target_name: A name you want to snipe
        """

        self.accounts = accounts
        self.target_name = target_name
        self.offset = offset
        self.requests = requests
        self.timing_system = timing_system
        self.optimize_offset = optimize_offset

    async def run(self) -> None:
        """
        Change the name of this account to the target name when possible
        """

        async with aiohttp.ClientSession() as session:
            requests = []
            print(f"\n{error.GRAY}Preparing and authenticating accounts for sniping.")

            for account in self.accounts:
                account.session = session  # Preload session object
                await account.authenticate()  # Authenticate the account so we can use it for other things

                requests.extend([account.send_snipe_request(self.target_name, index + 1) for index in range(self.requests)])

            # Get the availability time of the name
            availability_time = await macho_availability_time(self.target_name) if self.timing_system == "macho" else await name_mc_availability_time(self.target_name)

            # Calculate some timing data
            print(f"{error.GRAY}Calculating timing data for {error.BLUE}{self.target_name}{error.GRAY}.\n")

            sleep_time = max(availability_time - self.offset / 1000, 0)  # The offset is in milliseconds, so we convert it to seconds
            current_time = datetime.datetime.now()
            start_time = current_time + datetime.timedelta(seconds=sleep_time)

            # Display that the session began
            print(f"{error.GRAY}Sniping session ready at {error.BLUE}{current_time.strftime('%A, %H:%M:%S.%f')}{error.GRAY}. Attempts to snipe {error.BLUE}{self.target_name}"
                  f"{error.GRAY} will begin at {error.BLUE}{start_time.strftime('%A, %H:%M:%S.%f')}{error.GRAY}.")

            # Wait out the time until sniping should begin
            await asyncio.sleep(sleep_time)

            # Display that sniping start
            print(f"{error.GRAY}Now sniping {error.BLUE}{self.target_name}{error.GRAY} at {error.BLUE}{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%M')}"
                  f"{error.GRAY}.\n")

            request_times = await asyncio.gather(*requests)

            # Generally, a good scenario is for your last request to occur at the names availability time + 0.1 seconds. We attempt to make the offset fall in that range
            new_offset = max(self.offset + (request_times[-1] - (start_time + datetime.timedelta(milliseconds=100))).microseconds / 1000, 0)

            # Directly change the offset in the configuration file
            with open("config.toml", 'r') as file:
                configuration_json = toml.loads(file.read())

            if configuration_json["timing"]["optimize"]:
                with open("config.toml", 'w') as file:
                    configuration_json["timing"]["offset"] = new_offset
                    toml.dump(configuration_json, file)
