import colorama


# ANSI escape codes for colors
colorama.init()
RED = colorama.Fore.RED
LIGHT_RED = colorama.Fore.LIGHTRED_EX
DARK_GRAY = colorama.Fore.LIGHTBLACK_EX
BLACK = colorama.Fore.BLACK
GRAY = colorama.Fore.WHITE
WHITE = colorama.Fore.LIGHTWHITE_EX
BLUE = colorama.Fore.LIGHTBLUE_EX


# Base error class
class Error:
    def __init__(self, error_type, description, details):
        """
        A class for a custom, user-friendly error

        :param error_type: The errors type
        :param description: The description of the error
        :param details: Technical details of the error
        """

        print(f"\n{RED}{error_type.upper()}\n{'=' * len(error_type)}\n{GRAY}{description}\n\n{DARK_GRAY}{details}")
        exit(1)


class AuthenticationError(Error):
    def __init__(self, description, details):
        """
        A class for an error with authenticating a minecraft account

        :param description: The description of the error
        :param details: Technical details of the error
        """

        super().__init__("AUTHENTICATION ERROR", description, details)


class TimingError(Error):
    def __init__(self, description, details):
        """
        An error with getting the availability time of an account

        :param description: The description of the error
        :param details: Technical details of the error
        """

        super().__init__("TIMING ERROR", description, details)


class InputTypeError(Error):
    def __init__(self, description, details):
        """
        An error with an input's type

        :param description: The description of the error
        :param details: Technical details of the error
        """

        super().__init__("INPUT TYPE ERROR", description, details)


class UsernameUnavailableError(TimingError):
    def __init__(self, details):
        """
        An error when the username you're trying to snipe is unavailable for any reason

        :param details: Technical details of the error
        """
        super().__init__("Name is unavailable.", details)


class UnavailableTimerError(TimingError):
    def __init__(self, details):
        """
        An error when the timing system you use you doesn't work

        :param details: Technical details of the error
        """
        super().__init__("The timing system you use is unavailable.", details)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, details):
        """
        An error when the account credentials you provided are invalid. Either the username, password or both are wrong

        :param details: Technical details of the error
        """

        super().__init__("Invalid credentials.", details)


class SecurityAnswerError(AuthenticationError):
    def __init__(self, details):
        """
        An error when you fail to answer the security questions of an account

        :param details: Technical details of the error
        """
        super().__init__("Answers supplied incorrect, exact number unknown.", details)
