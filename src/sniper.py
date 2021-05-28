import error

import asyncio
import datetime
import json
import aiohttp  # For asynchronous requests
import bs4
import time
import platform

# Compatibility with windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def teun_availability_time(username: str) -> float:
    """
    Sends a request to Teun's API and returns the time of availability of that name

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    async with aiohttp.ClientSession() as session:
        # Teun's API can get name drop times, as this is impossible since Mojang disabled the use of the "timestamp" parameter since 2020
        async with session.get(f"https://mojang-api.teun.lol/droptime/{username}") as drop_time_response:
            if drop_time_response.status != 200:
                # Unfortunately, the API doesn't distinguish between available and unavailable names. So we have to send a second call to the Mojang API
                async with session.get(f"https://account.mojang.com/available/minecraft/{username}") as availability_response:
                    if await availability_response.text() == "TAKEN":
                        error.UsernameUnavailableError(await availability_response.text())

                return 0  # The name is available, so it's "available" in 0 seconds

            return (await drop_time_response.json())["UNIX"] - time.time()


async def name_mc_availability_time(username: str) -> float:
    """
    Sends a request to name mc and uses bs4 to scrape the time of availability of its html source

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://namemc.com/search?q={username}") as html_response:
            html = bs4.BeautifulSoup(await html_response.text(), "html.parser")
            availability_time = html.find("time", {"id": "availability-time"})["datetime"]
            unix_availability_time = (datetime.datetime.strptime(availability_time, "%Y-%m-%dT%H:%M:%S.000Z") - datetime.datetime(1970, 1, 1)).total_seconds()

            return unix_availability_time - time.time()


class Account:
    def __init__(self, email: str, password: str) -> None:
        """
        Storage for a basic Minecraft account for sniping

        :param email: The accounts email
        :param password: The accounts password
        """
        self.email = email
        self.password = password
        self.session = None
        self.authorization_header = None

    async def __authenticate(self) -> None:
        """
        Authenticate this account, to access restricted parts of the Mojang API
        """
        async with aiohttp.ClientSession() as session:
            async with session.post("https://authserver.mojang.com/authenticate", headers={"Content-Type": "application/json"},
                                    json={"username": self.email, "password": self.password}) as authentication_response:
                # Only feasible response code is 403 or 200
                if authentication_response.status != 200:
                    error.InvalidCredentialsError(await authentication_response.text())

                print(f"{error.LIGHT_BLUE}Email and password confirmed, {self.email} exists.")

                access_token = (await authentication_response.json())['accessToken']
                self.authorization_header = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Accept": "application/json"}

                # Check if you need security questions
                async with session.get("https://api.mojang.com/user/security/location", headers=self.authorization_header) as security_response:
                    if security_response.status != 204:
                        # Get the security questions
                        async with session.get("https://api.mojang.com/user/security/challenges", headers=self.authorization_header) as question_response:
                            response_json = await question_response.json()
                            questions = {question["answer"]["id"]: question["question"]["question"] for question in response_json}

                            print(f"{error.LIGHT_BLUE}In order to finish authenticating {self.email} you need to answer 3 security questions. Please do so.")

                            # Retrieve answers supplied by the user
                            answers = [{"id": key, "answer": input(f"\n{error.GRAY}{questions[key]}\n{error.DARK_GRAY}> ")} for key in questions]

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
        print(f"{error.DARK_GRAY}{index}){error.GRAY} Trying to snipe {error.BLUE}{target_name}{error.GRAY} to {self.email} at {datetime.datetime.now()}.")

        # Send a request to change the account's name
        async with aiohttp.ClientSession() as session:
            async with session.put(f"https://api.minecraftservices.com/minecraft/profile/name/{target_name}", headers=self.authorization_header) as name_change_response:
                if name_change_response.status == 200:
                    self.got_name = True
                    print(f"{error.DARK_GRAY}{index}){error.GRAY} Succeeded in sniping {error.BLUE}{target_name}{error.GRAY} to {self.email} at {datetime.datetime.now()}.")
                else:
                    print(f"{error.DARK_GRAY}{index}){error.GRAY} Failed in sniping {error.RED}{target_name}{error.GRAY} to {self.email} at {datetime.datetime.now()}.")

            await asyncio.sleep(0)  # Pass control

            return current_time


class GiftCodeAccount(Account):
    def __init__(self, email: str, password: str) -> None:
        """
        Storage for a basic Minecraft account with a gift code for sniping

        :param email: The accounts email
        :param password: The accounts password
        """

        super().__init__(email, password)

    async def send_snipe_request(self, target_name: str, index: int) -> datetime.datetime:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        :param index: The order of this snipe request
        """
        current_time = datetime.datetime.now()
        print(f"{error.DARK_GRAY}{index}){error.GRAY} Trying to snipe {error.BLUE}{target_name}{error.GRAY} to {self.email} at {datetime.datetime.now()}.")

        async with self.session.post(f"https://api.minecraftservices.com/minecraft/profile", headers=self.authorization_header,
                                     json={"profileName": target_name}) as claim_response:
            if claim_response.status == 200:
                self.got_name = True
                print(f"{error.BLUE}{index}){error.GRAY} Succeeded in sniping {error.BLUE}{target_name}{error.GRAY} to {self.email} at {datetime.datetime.now()}.")
            else:
                print(f"{error.RED}{index}){error.GRAY} Failed in sniping {error.RED}{target_name}{error.GRAY} to {self.email} at {datetime.datetime.now()}.")

        await asyncio.sleep(0)  # Pass control

        return current_time


class Session:
    def __init__(self, accounts: list[Account], target_name: str, offset: int, requests: int, timing_system: str, optimize_offset: bool = True) -> None:
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

            for account in self.accounts:
                account.session = session  # Preload session object
                requests.extend([account.send_snipe_request(self.target_name, index + 1) for index in range(self.requests)])

            availability_time = await teun_availability_time(self.target_name) if self.timing_system == "teun" else await name_mc_availability_time(self.target_name)
            sleep_time = max(availability_time - self.offset / 1000 - 0.5, 0)  # The offset is in milliseconds, so we convert it to seconds
            current_time = datetime.datetime.now()
            start_time = current_time + datetime.timedelta(seconds=sleep_time)

            print(f"{error.GRAY}\nSniping session began at {error.BLUE}{current_time.strftime('%Y/%m/%d %H:%M:%S')}{error.GRAY}.")
            print(f"{error.GRAY}Attempts to snipe {error.BLUE}{self.target_name}{error.GRAY} will begin at {error.BLUE}{start_time.strftime('%Y/%m/%d %H:%M:%S')}{error.GRAY}.")
            await asyncio.sleep(sleep_time)
            print(f"{error.GRAY}Sniping started at {error.BLUE}{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%M')}{error.GRAY}. "
                  f"The name is available in {error.BLUE}{start_time.strftime('%Y/%m/%d %H:%M:%S.%M')}{error.GRAY}\n")
            request_times = await asyncio.gather(*requests)

            # Generally, a good scenario is for your last request to occur at the names availability time + 0.1 seconds. We attempt to make the offset fall in that range
            new_offset = max(self.offset + (request_times[-1] - (start_time + datetime.timedelta(milliseconds=100))).microseconds / 1000, 0)

            # Directly change the offset in the configuration file
            with open("../src/config.json", 'r') as file:
                configuration_json = json.loads(file.read())

            if configuration_json["optimize"]:
                with open("../src/config.json", 'w') as file:
                    configuration_json["offset"] = new_offset
                    json.dump(configuration_json, file, indent=4)
