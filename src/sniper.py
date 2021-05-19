import asyncio
import datetime
import json
import aiohttp  # For asynchronous requests
import time
import src.error
import platform

# Compatibility with windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def create_client_session():
    return aiohttp.ClientSession()


SESSION = asyncio.run(create_client_session())


async def availability_time(username: str) -> int:
    """
    Sends a request to Teun's API and returns the time of availability of that name

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    # Teun's API can get name drop times, as this is impossible with the Mojang API since Mojang disabled the use of the "timestamp" parameter since 2020
    async with SESSION.session.get(f"https://mojang-api.teun.lol/droptime/{username}") as drop_time_response:
        if drop_time_response.status != 200:
            # Unfortunately, the API doesn't distinguish between available and unavailable names. So we have to send a second call to the Mojang API
            async with SESSION.session.get(f"https://account.mojang.com/available/minecraft/{username}") as availability_response:
                if await availability_response.text() == "TAKEN":
                    src.error.UsernameUnavailableError(await availability_response.text())

            return 0  # The name is available, so it's "available" in 0 seconds

        return (await drop_time_response.json())["UNIX"] - time.time()


class Account:
    def __init__(self, email: str, password: str) -> None:
        """
        Storage for a basic Minecraft account for sniping

        :param email: The accounts email
        :param password: The accounts password
        """
        self.email = email
        self.password = password
        self.authorization_header = None

    async def __authenticate(self) -> None:
        """
        Authenticate this account, to access restricted parts of the Mojang API
        """
        async with SESSION.session.post("https://authserver.mojang.com/authenticate", headers={"Content-Type": "application/json"},
                                        json={"username": self.email, "password": self.password}) as authentication_response:
            # Only feasible response code is 403 or 200
            if authentication_response.status != 200:
                src.error.InvalidCredentialsError(await authentication_response.text())

            print(f"{src.error.LIGHT_BLUE}Email and password confirmed, {self.email} exists.")

            access_token = (await authentication_response.json())['accessToken']
            self.authorization_header = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json", "Accept": "application/json"}

            # Check if you need security questions
            async with SESSION.session.get("https://api.mojang.com/user/security/location", headers=self.authorization_header) as security_response:
                if security_response.status != 204:
                    # Get the security questions
                    async with SESSION.session.get("https://api.mojang.com/user/security/challenges", headers=self.authorization_header) as question_response:
                        response_json = await question_response.json()
                        questions = {question["answer"]["id"]: question["question"]["question"] for question in response_json}

                        print(f"{src.error.LIGHT_BLUE}In order to finish authenticating {self.email} you need to answer 3 security questions. Please do so.")

                        # Retrieve answers supplied by the user
                        answers = [{"id": key, "answer": input(f"\n{src.error.GRAY}{questions[key]}\n{src.error.DARK_GRAY}> ")} for key in questions]

                        # Send the answers back
                        async with SESSION.session.post("https://api.mojang.com/user/security/location", headers=self.authorization_header, json=answers) as answer_response:
                            if answer_response.status != 204:
                                src.error.SecurityAnswerError(await answer_response.text())

    async def send_snipe_request(self, target_name: str) -> datetime.datetime:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        """
        current_time = datetime.datetime.now()

        # Send a request to change the account's name
        async with SESSION.session.put(f"https://api.minecraftservices.com/minecraft/profile/name/{target_name}", headers=self.authorization_header) as name_change_response:
            if name_change_response.status == 200:
                asyncio.get_event_loop().close()
                self.got_name = True
                print(f"{src.error.BLUE}Succeeded{src.error.GRAY} in sniping the name {target_name} to {self.email} at {datetime.datetime.now()}.")
            else:
                print(f"{src.error.RED}Failed{src.error.GRAY} in sniping the name {target_name} to {self.email} at {datetime.datetime.now()}.")

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

    async def send_snipe_request(self, target_name: str) -> datetime.datetime:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        """
        current_time = datetime.datetime.now()

        # Send a request to change the account's name
        async with SESSION.session.post(f"https://api.minecraftservices.com/minecraft/profile", headers=self.authorization_header,
                                        json={"profileName": target_name}) as claim_response:
            if claim_response.status == 200:
                asyncio.get_event_loop().close()
                self.got_name = True
                print(f"{src.error.BLUE}Succeeded{src.error.GRAY} in claiming the name {target_name} to {self.email} at {datetime.datetime.now()}.")
            else:
                print(f"{src.error.RED}Failed{src.error.GRAY} in claiming the name {target_name} to {self.email} at {datetime.datetime.now()}.")

        await asyncio.sleep(0)  # Pass control

        return current_time


class Session:
    def __init__(self, accounts: list[Account], target_name: str, offset: int, requests: int, optimize_offset: bool = True) -> None:
        """
        A sniping session, where you attempt to claim a name to any of your accounts

        :param offset: The amount of milliseconds by which the sniper will be early
        :param requests: The amount of requests to be sent with each account
        :param optimize_offset: Whether or not you want to optimize your offset at the end of the session
        :param accounts: A list of accounts you will use
        :param target_name: A name you want to snipe
        """
        self.accounts = accounts
        self.target_name = target_name
        self.offset = offset
        self.requests = requests
        self.optimize_offset = optimize_offset

    def run(self) -> None:
        """
        Change the name of this account to the target name when possible
        """
        sleep_time = asyncio.run(availability_time(self.target_name)) - self.offset / 1000  # The offset is in milliseconds, so we convert it to seconds
        current_time = datetime.datetime.now()
        current_time.replace(microsecond=0)
        start_time = current_time + datetime.timedelta(seconds=sleep_time)

        print(f"{src.error.GRAY}\nSniping session began at {src.error.BLUE}{current_time.strftime('%Y/%m/%d %H:%M:%S')}{src.error.GRAY}.")
        print(f"{src.error.GRAY}Attempts to snipe {src.error.BLUE}{self.target_name}{src.error.GRAY} will begin at {src.error.BLUE}{start_time.strftime('%Y/%m/%d %H:%M:%S')}{src.error.GRAY}.")

        asyncio.run(asyncio.sleep(sleep_time))
        print(f"{src.error.GRAY}Sniping started.")

        request_times = asyncio.run(asyncio.gather(*([account.send_snipe_request(self.target_name) for _ in range(self.requests) for account in self.accounts])))

        # As MCsniperPY showed, the best case scenario is for your last request to occur at the names availability time + 0.1 seconds. We adjust for that
        new_offset = self.offset - (request_times[-1] - (start_time + datetime.timedelta(milliseconds=100)))

        # Directly change the offset in the configuration file
        with open("../src/config.json", "w+") as file:
            configuration_json = json.loads(file.read())
            configuration_json["offset"] = new_offset

            json.dump(configuration_json, file, indent=4)


asyncio.run(SESSION.close())
