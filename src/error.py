import colorama


# ANSI escape codes for colors
colorama.init()
RED = colorama.Fore.RED
LIGHT_RED = colorama.Fore.LIGHTRED_EX
DARK_GRAY = colorama.Fore.LIGHTBLACK_EX
BLACK = colorama.Fore.BLACK
GRAY = colorama.Fore.WHITE
WHITE = colorama.Fore.LIGHTWHITE_EX
BLUE = colorama.Fore.BLUE
LIGHT_BLUE = colorama.Fore.LIGHTBLUE_EX


# Base error class
class Error:
    def __init__(self, error_type, description, details):
        print(f"\n{RED}{error_type.upper()}\n{'=' * len(error_type)}\n{GRAY}{description}\n\n{DARK_GRAY}{details}")
        exit(1)


# An error with authenticating a minecraft account
class AuthenticationError(Error):
    def __init__(self, description, details):
        super().__init__("AUTHENTICATION ERROR", description, details)


# An error with getting the availability time of an account
class TimingError(Error):
    def __init__(self, description, details):
        super().__init__("TIMING ERROR", description, details)


# An error with an input's type
class InputTypeError(Error):
    def __init__(self, description, details):
        super().__init__("INPUT TYPE ERROR", description, details)


# An error with an input's type
class ShadowingError(Error):
    def __init__(self, description, details):
        super().__init__("SHADOWING ERROR", description, details)


class UsernameUnavailableError(TimingError):
    def __init__(self, details):
        super().__init__("Name is unavailable.", details)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self, details):
        super().__init__("Invalid credentials.", details)


class SecurityAnswerError(AuthenticationError):
    def __init__(self, details):
        super().__init__("Answers supplied incorrect, exact number unknown.", details)
