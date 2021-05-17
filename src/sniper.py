import asyncio
import datetime
import aiohttp  # For asynchronous requests
import time
import src.error
import platform


# Compatibility with windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def availability_time(username: str) -> int:
    """
    Sends a request to Teun's API and returns the time of availability of that name

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    async with aiohttp.ClientSession() as session:
        # Teun's API uses a bypass to Cloudflare protection so it can get availability times from nameMC
        async with session.get(f"https://mojang-api.teun.lol/droptime/{username}") as drop_time_response:
            if drop_time_response.status != 200:
                # Unfortunately, the API doesn't distinguish between available and unavailable names. So we have to send a second call to Mojang's API
                async with session.get(f"https://account.mojang.com/available/minecraft/{username}") as availability_response:
                    if await availability_response.text() == "TAKEN":
                        src.error.UsernameUnavailableError(await availability_response.text())

                return 0  # The name is available, so it's "available" in 0 seconds

            return (await drop_time_response.json())["UNIX"] - time.time()


class SnipeAccount:
    def __init__(self, email, password) -> None:
        """
        A Minecraft account to perform a snipe on

        :param email: Account email (Allows username)
        :param password: Account password
        """
        self.email = email
        self.password = password
        self.authorization_header = None
        asyncio.run(self.__authenticate())

    async def __authenticate(self) -> None:
        """
        Authenticate a minecraft account, to access restricted parts of the Mojang API
        """
        async with aiohttp.ClientSession() as session:
            async with session.post("https://authserver.mojang.com/authenticate", headers={"Content-Type": "application/json"}, json={"username": self.email, "password": self.password}) as authentication_response:
                # Only feasible response code is 403 or 200
                if authentication_response.status != 200:
                    src.error.InvalidCredentialsError(await authentication_response.text())

                print(f"{src.error.LIGHT_BLUE}Email and password confirmed, account exists.")

                self.authorization_header = {"Authorization": f"Bearer {(await authentication_response.json())['accessToken']}", "Content-Type": "application/json"}

                # Check if you need security questions
                async with session.get("https://api.mojang.com/user/security/location", headers=self.authorization_header) as security_response:
                    if security_response.status != 204:
                        # Get the security questions
                        async with session.get("https://api.mojang.com/user/security/challenges", headers=self.authorization_header) as question_response:
                            json = await question_response.json()
                            questions = {question["answer"]["id"]: question["question"]["question"] for question in json}

                            print(f"{src.error.LIGHT_BLUE}In order to finish authenticating {self.email} you need to answer 3 security questions. Please do so.")

                            # Retrieve answers supplied by the user
                            answers = [{"id": key, "answer": input(f"\n{src.error.GRAY}{questions[key]}\n{src.error.DARK_GRAY}> ")} for key in questions]

                            # Send the answers back
                            async with session.post("https://api.mojang.com/user/security/location", headers=self.authorization_header, json=answers) as answer_response:
                                if answer_response.status != 204:
                                    src.error.SecurityAnswerError(await answer_response.text())

    async def __snipe_request(self, target_name: str) -> None:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        """
        async with aiohttp.ClientSession() as session:
            # Send a request to change the account's name
            async with session.put(f"https://api.minecraftservices.com/minecraft/profile/name/{target_name}", headers=self.authorization_header) as name_change_response:
                if name_change_response.status == 200:
                    asyncio.get_event_loop().close()
                    print(f"{src.error.BLUE}Succeeded{src.error.GRAY} in sniping the name {target_name} to {self.email} at {datetime.datetime.now()}.")
                else:
                    print(f"{src.error.RED}Failed{src.error.GRAY} in sniping the name {target_name} to {self.email} at {datetime.datetime.now()}.")

    def snipe_username(self, target_name: str, offset: int, requests: int) -> None:
        """
        Change the name of this account to a target name when possible

        :param offset: The offset of the snipe, the sniper will activate a bit late or early depending on it. Specified in milliseconds
        :param target_name: A name you want to switch to
        :param requests: The amount of requests to be sent
        """
        sleep_time = asyncio.run(availability_time(target_name)) + offset / 1000  # The offset is in milliseconds, so we convert it to seconds
        current_time = datetime.datetime.now()
        start_time = current_time + datetime.timedelta(seconds=sleep_time)

        print(f"{src.error.GRAY}\nSniping session began at {src.error.BLUE}{current_time.strftime('%Y/%m/%d %H:%M:%S')}{src.error.GRAY}.")
        print(f"{src.error.GRAY}Attempts to snipe {src.error.BLUE}{target_name}{src.error.GRAY} to {self.email} will begin at {src.error.BLUE}{start_time.strftime('%Y/%m/%d %H:%M:%S')}{src.error.GRAY}.")

        asyncio.run(asyncio.sleep(sleep_time))
        print(f"{src.error.GRAY}Sniping started.")

        asyncio.run(asyncio.gather(*([self.__snipe_request(target_name) for _ in range(requests)])))
