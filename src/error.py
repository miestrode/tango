# ANSI escape codes for colors
RED = "\033[0;38;2;199;47;49m"
LIGHT_RED = "\033[0;38;2;199;67;69"
DARK_GRAY = "\033[0;38;2;88;88;88m"
GRAY = "\033[0;38;2;148;148;148m"
BLUE = "\033[0;38;2;87;89;199m"
LIGHT_BLUE = "\033[0;38;2;127;129;199m"
ITALIC = "\033[3m"
BOLD = "\033[1m"


# Base error class
class Error:
    def __init__(self, error_type, description, details):
        print(f"\n{RED}{error_type.upper()}\n{'=' * len(error_type)}\n{GRAY}{description}\n\n{DARK_GRAY}{ITALIC}{details}")
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
