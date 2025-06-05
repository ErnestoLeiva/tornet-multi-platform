#!/usr/bin/env python3
# tornet-mp - Automate IP address changes using Tor
# Author: Ernesto Leiva
# Copyright (c) 2025 Ernesto Leiva All rights reserved.
import argparse
import os
import random
import signal
import subprocess
import sys
import time

import requests

from tornet_mp.utils import (
    install_pip,
    install_requests,
    install_tor,
    is_arch_linux,
    is_macos,
    is_windows,
)

from .banner import print_banner
from .log import configure as _log_configure
from .log import (
    log_change,
    log_error,
    log_info,
    log_minor,
    log_notice,
    log_success,
    log_warn,
)
from .version import __version__

# Configure logger
_log_configure()

# Allow overriding Tor SOCKS host/port via environment variables
TOR_SOCKS_HOST = os.getenv("TOR_SOCKS_HOST", "127.0.0.1")
TOR_SOCKS_PORT = int(os.getenv("TOR_SOCKS_PORT", "9050"))

# Globals
TOOL_NAME = "tornet-mp"
VERSION = __version__
_has_cleaned_up = False


# TOR service control
def is_tor_installed() -> bool:
    """
    #### Determines if Tor is installed based on the current operating system\n
    Uses platform-specific detection:
    - **Linux**: `which tor`
    - **Windows**: `where tor`
    - **macOS**: `brew list tor` (only if Homebrew is available)
    ***
    Returns:
        bool: True if Tor is found, False otherwise.
    """
    try:
        if is_windows():
            subprocess.check_output("where tor", shell=True)
        elif is_macos():
            subprocess.check_output("which brew", shell=True)
            subprocess.check_output("brew list tor", shell=True)
        else:
            subprocess.check_output("which tor", shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


def start_tor_service() -> None:
    """
    #### Starts the Tor service using the appropriate system command\n
    - **Linux**: Uses `systemctl` or `service`\n
    - **macOS**: Uses `brew services start tor`\n
    - **Windows**: Runs `tor` from PATH assuming it's installed
    """
    log_info("Starting Tor service...")

    if is_arch_linux():
        subprocess.run(
            ["sudo", "systemctl", "start", "tor"], stdout=subprocess.DEVNULL, check=True
        )
    elif is_windows():
        subprocess.Popen(
            "tor",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            shell=True,
            text=True,
        )
    elif is_macos():
        subprocess.run(
            ["brew", "services", "start", "tor"], stdout=subprocess.DEVNULL, check=True
        )
    else:
        subprocess.run(
            ["sudo", "service", "tor", "start"], stdout=subprocess.DEVNULL, check=True
        )


def reload_tor_service() -> None:
    """
    #### Reloads the Tor service using platform-specific methods\n
    - On **Docker**, uses `pidof` and sends `SIGHUP` directly to the Tor process\n
    - On **Linux**: Uses `systemctl reload` or `service reload`\n
    - On **macOS**: Uses `brew services restart tor`\n
    - On **Windows**: Kills and restarts `tor.exe` using `taskkill` and `tor`
    """
    log_info("Reloading Tor to request new identity...")

    # In Docker environment, send SIGHUP to the Tor process instead of using service commands
    if os.environ.get("DOCKER_ENV"):
        try:
            # Find the Tor process ID
            tor_pid = subprocess.check_output("pidof tor", shell=True).decode().strip()
            if tor_pid:
                # Send SIGHUP signal to reload Tor
                subprocess.run(
                    ["kill", "-HUP", tor_pid], stdout=subprocess.DEVNULL, check=True
                )
        except subprocess.CalledProcessError:
            log_error("Unable to find Tor process. Please check if Tor is running.")
    else:
        if is_arch_linux():
            subprocess.run(
                ["sudo", "systemctl", "reload", "tor"],
                stdout=subprocess.DEVNULL,
                check=True,
            )
        elif is_windows():
            subprocess.run(
                "taskkill /IM tor.exe /F",
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)  # Give time for the port to free up
            proc = subprocess.Popen(
                "tor",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
            )

            # Read only errors in background
            def _log_tor_errors(stream) -> None:
                for line in stream:
                    if line.strip():
                        log_error(f"tor error: {line.strip()}")

            import threading

            threading.Thread(
                target=_log_tor_errors, args=(proc.stderr,), daemon=True
            ).start()
            wait_for_tor(timeout=30)
        elif is_macos():
            subprocess.run(
                ["brew", "services", "restart", "tor"],
                stdout=subprocess.DEVNULL,
                check=True,
            )
        else:
            subprocess.run(
                ["sudo", "service", "tor", "reload"],
                stdout=subprocess.DEVNULL,
                check=True,
            )


def stop_tor_service() -> None:
    """
    #### Stops the Tor service using OS-specific commands\n
    - **Linux**: Uses `systemctl stop` or `service stop`\n
    - **macOS**: Uses `brew services stop tor`\n
    - **Windows**: Uses `taskkill /IM tor.exe /F` to forcefully stop the Tor process
    """
    log_info("Stopping all Tor-related processes...")

    if is_arch_linux():
        subprocess.run(
            ["sudo", "systemctl", "stop", "tor"], stdout=subprocess.DEVNULL, check=True
        )
    elif is_windows():
        subprocess.run(
            "taskkill /IM tor.exe /F",
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    elif is_macos():
        subprocess.run(
            ["brew", "services", "stop", "tor"], stdout=subprocess.DEVNULL, check=True
        )
    else:
        subprocess.run(
            ["sudo", "service", "tor", "stop"], stdout=subprocess.DEVNULL, check=True
        )


# Initialization
def initialize_environment() -> None:
    """
    #### Sets up the runtime environment for TorNet\n
    - Installs required dependencies (`pip`, `requests`, `tor`) based on the current OS.\n
    - If not running in Docker, starts the Tor service.\n
    - Shows the first Tor exit node ip after Tor service starts \n
    - Finally, prints user instructions.
    """
    log_info("Initializing environment and checking dependencies...")

    log_minor("===============================")
    install_pip()
    install_requests()
    install_tor()
    log_minor("===============================\n")

    # Skip starting Tor service if running in Docker
    if not os.environ.get("DOCKER_ENV"):
        start_tor_service()

    # Wait for tor to be fully responsive at the SOCKS5 level
    if not wait_for_tor(timeout=30):
        log_error("Tor did not respond in time. IP retrieval may fail.")

    print_start_message()
    print_ip(ma_ip())


def print_start_message() -> None:
    """
    #### Displays startup guidance for the user\n
    Reminds the user to configure their browser for anonymity.
    """
    log_notice("Make sure to configure your browser to use Tor for anonymity.")


# IP address handling
def ma_ip() -> str | None:
    """
    #### Returns current IP\n
    If `is_tor_running()`, calls `ma_ip_tor()`\n
    Else, calls `ma_ip_normal()`
    """
    log_info("Fetching current IP address...")

    if is_tor_running():
        ip1 = ma_ip_tor()
        time.sleep(5)
        ip2 = ma_ip_tor()

        if ip1 and ip2 and ip1 != ip2:
            pass
            # log_warn(f"Stale Tor circuit detected: {ip1} → {ip2}")
        return ip2 or ip1
    else:
        return ma_ip_normal()


def is_tor_running() -> bool:
    """
    #### Checks if the Tor process is currently running
    - On **Linux/macOS**: uses `pgrep -x tor`
    - On **Windows**: uses `tasklist` to search for `tor.exe`
    ***
    Returns:
        bool: True if Tor is running, False otherwise.
    """
    try:
        if is_windows():
            output = subprocess.check_output("tasklist", shell=True).decode().lower()
            return "tor.exe" in output
        else:
            subprocess.check_output("pgrep -x tor", shell=True)
            return True
    except subprocess.CalledProcessError:
        return False


def ma_ip_tor() -> str | None:
    """
    #### Returns current Tor IP using SOCKS5 proxy at `{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}`\n
    Uses the official Tor Project API to verify exit node and IP.\n
    ***
    Returns:
        str: The Tor-exit IP address, or None if the check fails.
    """
    proxies = {
        "http": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
        "https": f"socks5h://{TOR_SOCKS_HOST}:{TOR_SOCKS_PORT}",
    }

    service = "https://check.torproject.org/api/ip"
    try:
        response = requests.get(service, proxies=proxies, timeout=10)
        response.raise_for_status()

        data = response.json()
        ip = data.get("IP")
        is_tor = data.get("IsTor", False)

        if not is_tor:
            log_warn(f"The IP {ip} is not recognized as a Tor exit node.")
        return ip

    except requests.RequestException as e:
        log_error(f"Failed to fetch Tor IP from {service}: {e}")
        return None


def ma_ip_normal() -> str | None:
    """
    #### Returns the current public IP address without using Tor\n
    Makes a direct request to `https://api.ipify.org` and returns the response.\n
    ***
    Returns:
        str: The detected public IP address, or None on failure.
    """
    try:
        response = requests.get("https://api.ipify.org")
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException:
        log_error(
            "Having trouble fetching the IP address. Please check your internet connection."
        )
        return None


# IP Rotation Functions
def change_ip() -> str | None:
    """
    #### Forces a new Tor identity and fetches a new IP address\n
    Calls `reload_tor_service()` and then retrieves the new IP via `ma_ip()`.\n
    ***
    Returns:
        str: The new Tor-exit IP address, or None if unreachable.
    """
    log_info("Requesting new IP address via Tor...")

    reload_tor_service()

    return ma_ip()


def change_ip_repeatedly(interval: str, count: int) -> None:
    """
    #### Changes IP repeatedly at a given interval
    - `interval` (str): Can be a single number `"60"` or a range `"60-120"` seconds.
    - `count` (int): Number of times to change IP. If `0`, loop indefinitely.
    """

    def parse_interval(interval_str) -> int:
        interval_str = str(interval_str)
        if "-" in interval_str:
            parts = interval_str.split("-")
            return random.randint(int(parts[0]), int(parts[1]))
        else:
            return int(interval_str)

    def sleep_and_rotate(remaining: int | None = None) -> None:
        sleep_time = parse_interval(interval)
        if remaining is not None:
            log_minor(f"Remaining IP changes: {remaining}")
        log_minor(f"Sleeping for {sleep_time} seconds before refreshing IP...\n")
        time.sleep(sleep_time)
        new_ip = change_ip()
        if new_ip:
            print_ip(new_ip)

    if count == 0:
        while True:
            sleep_and_rotate()
    else:
        for i in range(count):
            sleep_and_rotate(remaining=count - i)

    # Show exit message once rotations are finished
    print("\n", end="")  # Manual newline for clarity
    log_notice("IP rotation complete.")
    log_warn("Tor is still running in the background.")
    log_notice(
        "Press CTRL+C to safely stop the Tor service and clean up tornet-mp processes."
    )
    print("\n", end="")  # Manual newline for clarity

    if hasattr(signal, "pause"):
        signal.pause()
    else:
        while True:
            time.sleep(1)


def print_ip(ip) -> None:
    """
    #### Prints the given IP in a formatted message\n
    - **ip** (str): The IP address to print
    """
    print("\n", end="")  # Manual newline for clarity
    if is_tor_running():
        message = f"Your IP has been changed to: {ip}"
    else:
        message = f"Your IP is: {ip}"
    border = "=" * len(message)

    # This dynamically adjusts '=' character borders to exact lenght of ip change message
    log_change(border)
    log_change(message)
    log_change(border)


# Utility commands
def auto_fix() -> None:
    """
    #### Automatically reinstalls all dependencies and upgrades the tornet package\n
    Equivalent to re-running the environment setup and refreshing the installed version.
    """
    install_pip()
    install_requests()
    install_tor()
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "tornet-mp"],
        stdout=subprocess.DEVNULL,
        check=True,
    )


def stop_services() -> None:
    """
    #### Stops the Tor service and any active tornet processes\n
    Ensures this runs only once per session.
    """
    global _has_cleaned_up
    if _has_cleaned_up:
        return
    _has_cleaned_up = True

    if os.environ.get("DOCKER_ENV"):
        try:
            tor_pid = subprocess.check_output("pidof tor", shell=True).decode().strip()
            if tor_pid:
                subprocess.run(["kill", tor_pid], stdout=subprocess.DEVNULL, check=True)
                log_success("Tor process stopped.")
        except subprocess.CalledProcessError:
            log_error("No Tor process found to stop.")
    else:
        stop_tor_service()

    if not is_windows():
        subprocess.run(
            ["pkill", "-f", TOOL_NAME],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    log_success(f"Tor services and {TOOL_NAME} processes stopped.")


def signal_handler(sig, frame) -> None:
    """
    #### Gracefully handles termination signals\n
    Stops services and exits cleanly when user interrupts with `Ctrl+C` or `SIGQUIT/SIGBREAK`.
    """
    stop_services()
    print("\n", end="")  # Manual newline for clarity
    log_error("Program terminated by user.")
    exit(0)


def check_internet_connection() -> bool:
    """
    #### Continuously checks if the internet connection is active\n
    ##### Tries to connect to Google every second. Prints a warning if offline.\n
    ***
    Returns:
        bool: False when connection fails, otherwise loop continues.
    """
    while True:
        time.sleep(1)
        try:
            requests.get("http://www.google.com", timeout=1)
        except requests.RequestException:
            log_error(
                "Internet connection lost. Please check your internet connection."
            )
            return False


def wait_for_tor(timeout=60) -> bool:
    """
    #### Waits until the Tor SOCKS proxy is responsive or times out\n
    ##### Attempts multiple connections via SOCKS5 until one succeeds or time runs out.\n
    ***
    Returns:
        bool: True if Tor responded, False if timeout occurred.
    """
    import socks

    log_minor(
        f"Waiting for Tor SOCKS proxy to become responsive... (timeout: {timeout}s)"
    )
    start = time.time()

    while time.time() - start < timeout:
        try:
            # Try connecting to api.ipify.org via SOCKS5
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, TOR_SOCKS_HOST, TOR_SOCKS_PORT)
            s.settimeout(5)
            s.connect(("check.torproject.org", 443))
            s.close()
            log_success("Tor SOCKS5 proxy is responding.")
            return True
        except Exception:
            time.sleep(2)

    log_error("Timed out waiting for Tor SOCKS5 proxy.")
    return False


# CLI entry point
def main() -> None:
    signal.signal(signal.SIGINT, signal_handler)
    # Use SIGBREAK for Windows, SIGQUIT for Unix-like systems.
    if is_windows():
        if hasattr(signal, "SIGBREAK"):
            signal.signal(signal.SIGBREAK, signal_handler)
    elif hasattr(signal, "SIGQUIT"):
        signal.signal(signal.SIGQUIT, signal_handler)

    # Argument parsing
    parser = argparse.ArgumentParser(
        description="TorNet - Automate IP address changes using Tor (https://github.com/ErnestoLeiva/tornet-multi-platform)"
    )
    parser.add_argument(
        "--interval",
        metavar="<seconds>",
        type=str,
        default=60,
        help="Time in seconds between IP changes",
    )
    parser.add_argument(
        "--count",
        metavar="<count>",
        type=int,
        default=10,
        help="Number of times to change the IP. If 0, change IP indefinitely",
    )
    parser.add_argument(
        "--ip", action="store_true", help="Display the current IP address and exit"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically fix issues (install/upgrade packages)",
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop all Tor services and tornet processes and exit",
    )
    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {VERSION}"
    )
    args = parser.parse_args()

    if args.ip:
        ip = ma_ip()
        if ip:
            print_ip(ip)
        return

    if not is_tor_installed():
        log_error("Tor is not installed. Please install Tor and try again.")
        return

    if args.auto_fix:
        auto_fix()
        log_success("Auto-fix complete.")
        return

    if args.stop:
        stop_services()
        return

    print_banner()
    initialize_environment()
    change_ip_repeatedly(args.interval, args.count)


if __name__ == "__main__":
    check_internet_connection()
    main()
