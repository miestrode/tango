# Tools for sniping a name
import asyncio
import datetime
import aiohttp
import time
import src.error
import platform


if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # If you're using the Windows operating system


# Display the logo
print(f"""{src.error.BLUE}{src.error.BOLD}
88888888888                                  
    888                                      
    888                                      
    888   8888b.  88888b.   .d88b.   .d88b.  
    888      "88b 888 "88b d88P"88b d88""88b 
    888  .d888888 888  888 888  888 888  888 
    888  888  888 888  888 Y88b 888 Y88..88P 
    888  "Y888888 888  888  "Y88888  "Y88P"  
{src.error.GRAY}{src.error.BOLD}The open-source name sniper     {src.error.BLUE}{src.error.BOLD}888          
                           Y8b d88P          
                            "Y88P"\n""")


async def availability_time(username: str) -> int:
    """
    Sends a request to Teun's API and returns the time of availability of that name

    :param username: An available or "dropping" username
    :return: The amount of seconds until the specified name is available
    """

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://mojang-api.teun.lol/droptime/{username}") as drop_time_response:
            if drop_time_response.status != 200:
                async with session.get(f"https://account.mojang.com/available/minecraft/{username}") as availability_response:
                    if await availability_response.text() == "TAKEN":
                        src.error.UsernameUnavailableError(await availability_response.text())

                return 0

            return (await drop_time_response.json())["UNIX"] - time.time()


class SnipeAccount:
    def __init__(self, email, password) -> None:
        """
        A minecraft account

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

                async with session.get("https://api.mojang.com/user/security/location", headers=self.authorization_header) as security_response:
                    if security_response.status != 204:
                        async with session.get("https://api.mojang.com/user/security/challenges", headers=self.authorization_header) as question_response:
                            json = await question_response.json()
                            questions = {question["answer"]["id"]: question["question"]["question"] for question in json}

                            print(f"{src.error.LIGHT_BLUE}In order to finish authenticating {self.email} you need to answer 3 security questions. Please do so.")

                            answers = [{"id": key, "answer": input(f"\n{src.error.GRAY}{questions[key]}\n{src.error.DARK_GRAY}> ")} for key in questions]

                            async with session.post("https://api.mojang.com/user/security/location", headers=self.authorization_header, json=answers) as answer_response:
                                if answer_response.status != 204:
                                    src.error.SecurityAnswerError(await answer_response.text())

    async def __snipe_request(self, target_name: str) -> None:
        """
        Send a singular name change request to the Mojang API

        :param target_name: A name you want to switch to
        """
        async with aiohttp.ClientSession() as session:
            async with session.put(f"https://api.minecraftservices.com/minecraft/profile/name/{target_name}", headers=self.authorization_header) as name_change_response:
                if name_change_response.status == 200:
                    asyncio.get_event_loop().close()
                    print(f"{src.error.BLUE}Succeeded{src.error.GRAY} in sniping the name {target_name} to {self.email} at {datetime.datetime.now()}.")
                else:
                    print(f"{src.error.RED}Failed{src.error.GRAY} in sniping the name {target_name} to {self.email} at {datetime.datetime.now()}.")

    async def __send_snipe_requests(self, target_name: str, repeat: int) -> None:
        """
        Send multiple name change requests to the Mojang API

        :param target_name: A name you want to switch to
        :param repeat: The amount of requests sent
        """
        await asyncio.gather(*([self.__snipe_request(target_name) for _ in range(repeat)]))

    def snipe_username(self, target_name: str, offset: int) -> None:
        """
        Change the name of this account to a target name when possible

        :param offset: The offset of the snipe, the sniper will activate a bit late or early depending on it. Specified in milliseconds
        :param target_name: A name you want to switch to
        """
        sleep_time = asyncio.run(availability_time(target_name)) + offset / 1000
        current_time = datetime.datetime.now()
        start_time = current_time + datetime.timedelta(seconds=sleep_time)

        print(f"{src.error.GRAY}\nSniping session began at {src.error.BLUE}{current_time.strftime('%Y/%m/%d %H:%M:%S')}{src.error.GRAY}.")
        print(f"{src.error.GRAY}Attempts to snipe {src.error.BLUE}{target_name}{src.error.GRAY} to {self.email} will begin at {src.error.BLUE}{start_time.strftime('%Y/%m/%d %H:%M:%S')}{src.error.GRAY}.")

        asyncio.run(asyncio.sleep(sleep_time))

        print(f"{src.error.GRAY}Sniping started.")

        asyncio.run(self.__send_snipe_requests(target_name, 80))
