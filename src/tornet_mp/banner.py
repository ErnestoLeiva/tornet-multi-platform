from .version import __version__

green = "\033[92m"
red = "\033[91m"
white = "\033[97m"
reset = "\033[0m"
cyan = "\033[36m"


def print_banner() -> None:
    version_str = f"Version {__version__}"

    # Dynamic version formatting
    padding = (55 - len(version_str)) // 2
    version_line = f"{white} │{cyan}{' ' * padding}{version_str}{' ' * (54 - len(version_str) - padding)}{white} │"

    banner = f"""
{white} ┌───────────────────────────────────────────────────────┐
{white} │{green} ████████╗ ██████╗ ██████╗ ███╗   ██╗███████╗████████╗{white} │
{white} │{green} ╚══██╔══╝██╔═══██╗██╔══██╗████╗  ██║██╔════╝╚══██╔══╝{white} │
{white} │{green}    ██║   ██║   ██║██████╔╝██╔██╗ ██║█████╗     ██║   {white} │
{white} │{green}    ██║   ██║   ██║██╔══██╗██║╚██╗██║██╔══╝     ██║   {white} │
{white} │{green}    ██║   ╚██████╔╝██║  ██║██║ ╚████║███████╗   ██║   {white} │
{white} │{green}    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   {white} │
{version_line}
{white} └───────────────────────────────────────────────────────┘{reset}

"""
    print(banner)
