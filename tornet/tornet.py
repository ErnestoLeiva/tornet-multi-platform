#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# tornet - Automate IP address changes using Tor
# Author: Fidal
# Copyright (c) 2024 Fidal. All rights reserved.
import os
import time
import argparse
import requests
import subprocess
import signal
import platform
import random
from .utils import install_pip, install_requests, install_tor
from .banner import print_banner
from .log import (
    log_success, log_info, log_notice, log_minor,
    log_warn, log_error, log_change
)


# Globals
TOOL_NAME = "tornet"
VERSION = "2.1.0"



# OS determination
def is_arch_linux():
    return os.path.exists("/etc/arch-release") or os.path.exists("/etc/manjaro-release")
def is_macos():
    return platform.system().lower() == 'darwin'
def is_windows():
    return platform.system().lower() == 'windows'

# TOR service control
def is_tor_installed():
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
            subprocess.check_output('where tor', shell=True)
        elif is_macos():
            subprocess.check_output('which brew', shell=True)
            subprocess.check_output('brew list tor', shell=True)
        else:
            subprocess.check_output('which tor', shell=True)
        return True
    except subprocess.CalledProcessError:
        return False
def start_tor_service():
    """
    #### Starts the Tor service using the appropriate system command\n
    - **Linux**: Uses `systemctl` or `service`\n
    - **macOS**: Uses `brew services start tor`\n
    - **Windows**: Runs `tor` from PATH assuming it's installed
    """
    log_info("Starting Tor service...")
    
    if is_arch_linux():
        os.system("sudo systemctl start tor")
    elif is_windows():
        subprocess.Popen(
            "tor",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            shell=True,
            text=True
        )
    elif is_macos():
        os.system("brew services start tor")
    else:
        os.system("sudo service tor start")
def reload_tor_service():
    """
    #### Reloads the Tor service using platform-specific methods\n
    - On **Docker**, uses `pidof` and sends `SIGHUP` directly to the Tor process\n
    - On **Linux**: Uses `systemctl reload` or `service reload`\n
    - On **macOS**: Uses `brew services restart tor`\n
    - On **Windows**: Kills and restarts `tor.exe` using `taskkill` and `tor`
    """
    log_info("Reloading Tor to request new identity...")

    # In Docker environment, send SIGHUP to the Tor process instead of using service commands
    if os.environ.get('DOCKER_ENV'):
        try:
            # Find the Tor process ID
            tor_pid = subprocess.check_output("pidof tor", shell=True).decode().strip()
            if tor_pid:
                # Send SIGHUP signal to reload Tor
                os.system(f"kill -HUP {tor_pid}")
        except subprocess.CalledProcessError:
            log_error("Unable to find Tor process. Please check if Tor is running.")
    else:
        if is_arch_linux():
            os.system("sudo systemctl reload tor")
        elif is_windows():
            subprocess.run("taskkill /IM tor.exe /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(1)  # Give time for the port to free up
            proc = subprocess.Popen(
                "tor",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                shell=True,
                text=True
            )
            # Read only errors in background
            def _log_tor_errors(stream):
                for line in stream:
                    if line.strip():
                        log_error(f"tor error: {line.strip()}")
            import threading
            threading.Thread(target=_log_tor_errors, args=(proc.stderr,), daemon=True).start()
            wait_for_tor(timeout=30)
        elif is_macos():
            os.system("brew services restart tor")
        else:
            os.system("sudo service tor reload")
def stop_tor_service():
    """
    #### Stops the Tor service using OS-specific commands\n
    - **Linux**: Uses `systemctl stop` or `service stop`\n
    - **macOS**: Uses `brew services stop tor`\n
    - **Windows**: Uses `taskkill /IM tor.exe /F` to forcefully stop the Tor process
    """
    log_info("Stopping all Tor-related processes...")

    if is_arch_linux():
        os.system("sudo systemctl stop tor")
    elif is_windows():
        subprocess.run("taskkill /IM tor.exe /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif is_macos():
        os.system("brew services stop tor")
    else:
        os.system("sudo service tor stop")

# Initialization
def initialize_environment():
    """
    #### Sets up the runtime environment for TorNet\n
    Installs required dependencies (`pip`, `requests`, `tor`) based on the current OS.\n
    If not running in Docker, starts the Tor service.\n
    Finally, prints user instructions.
    """
    log_info("Initializing environment and checking dependencies...")

    install_pip()
    install_requests()
    install_tor()
    # Skip starting Tor service if running in Docker
    if not os.environ.get('DOCKER_ENV'):
        start_tor_service()
    
    # Wait for tor to be fully responsive at the SOCKS5 level
    if not wait_for_tor(timeout=30):
        log_error("Tor did not respond in time. IP retrieval may fail.")

    print_start_message()
    print_ip(ma_ip())
def print_start_message():
    """
    #### Displays startup guidance for the user\n
    Informs the user that Tor is running and reminds them to configure their browser for anonymity.
    """
    log_success("Tor service started. Please wait a minute for Tor to connect.")
    log_notice("Make sure to configure your browser to use Tor for anonymity.")

# IP address handling
def ma_ip():
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
            log_warn(f"Stale Tor circuit detected: {ip1} → {ip2}")
        return ip2 or ip1
    else:
        return ma_ip_normal()
def is_tor_running():
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
            output = subprocess.check_output('tasklist', shell=True).decode().lower()
            return 'tor.exe' in output
        else:
            subprocess.check_output('pgrep -x tor', shell=True)
            return True
    except subprocess.CalledProcessError:
        return False
def ma_ip_tor():
    """
    #### Returns current Tor IP using SOCKS5 proxy at `127.0.0.1:9050`\n
    Uses the official Tor Project API to verify exit node and IP.\n
    ***
    Returns:
        str: The Tor-exit IP address, or None if the check fails.
    """
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

    service = 'https://check.torproject.org/api/ip'
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
def ma_ip_normal():
    """
    #### Returns the current public IP address without using Tor\n
    Makes a direct request to `https://api.ipify.org` and returns the response.\n
    ***
    Returns:
        str: The detected public IP address, or None on failure.
    """
    try:
        response = requests.get('https://api.ipify.org')
        response.raise_for_status()
        return response.text.strip()
    except requests.RequestException:
        log_error("Having trouble fetching the IP address. Please check your internet connection.")
        return None

# IP Rotation Functions
def change_ip():
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
def change_ip_repeatedly(interval: str, count):
    """
    #### Changes IP repeatedly at a given interval\n
    - **interval** (str): Can be a single number `"60"` or a range `"60-120"` seconds.\n
    - **count** (int): Number of times to change IP. If `0`, loop indefinitely.
    """

    if count == 0:  # Loop forever
        while True:
            try:
                inte = interval.split("-")
                sleep_time = random.randint(int(inte[0]), int(inte[1]))
            except IndexError:
                sleep_time = int(interval)

            log_minor(f"Sleeping for {sleep_time} seconds before refreshing IP...")
            time.sleep(sleep_time)

            new_ip = change_ip()
            if new_ip:
                print_ip(new_ip)
    else:
        for _ in range(count):
            try:
                inte = interval.split("-")
                sleep_time = random.randint(int(inte[0]), int(inte[1]))
            except IndexError:
                sleep_time = int(interval)

            log_minor(f"Sleeping for {sleep_time} seconds before refreshing IP...")
            time.sleep(sleep_time)

            new_ip = change_ip()
            if new_ip:
                print_ip(new_ip)
def print_ip(ip):
    """
    #### Prints the given IP in a formatted message\n
    - **ip** (str): The IP address to print
    """
    print("\n", end="")  # Manual newline for clarity
    message = f"Your IP has been changed to: {ip}"
    border = "=" * len(message)

    # This dynamically adjusts '=' character borders to exact lenght of ip change message
    log_change(border)
    log_change(message)
    log_change(border + "\n")

# Utility commands
def auto_fix():
    """
    #### Automatically reinstalls all dependencies and upgrades the tornet package\n
    Equivalent to re-running the environment setup and refreshing the installed version.
    """
    install_pip()
    install_requests()
    install_tor()
    os.system("pip install --upgrade tornet")
def stop_services():
    """
    #### Stops the Tor service and any active tornet processes\n
    In Docker, uses `pidof`; otherwise uses platform-specific service commands.
    """
    # In Docker environment, find and kill the Tor process directly
    if os.environ.get('DOCKER_ENV'):
        try:
            # Find the Tor process ID
            tor_pid = subprocess.check_output("pidof tor", shell=True).decode().strip()
            if tor_pid:
                # Kill the Tor process
                os.system(f"kill {tor_pid}")
                log_success("Tor process stopped.")
        except subprocess.CalledProcessError:
            log_error("No Tor process found to stop.")
    else:
        stop_tor_service()
    
    if not is_windows():
        os.system(f"pkill -f {TOOL_NAME} > /dev/null 2>&1")

    log_success(f"Tor services and {TOOL_NAME} processes stopped.")
def signal_handler(sig, frame):
    """
    #### Gracefully handles termination signals\n
    Stops services and exits cleanly when user interrupts with `Ctrl+C` or `SIGQUIT/SIGBREAK`.
    """
    stop_services()
    print("\n", end="") # Manual newline for clarity
    log_error("Program terminated by user.")
    exit(0)
def check_internet_connection():
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
            requests.get('http://www.google.com', timeout=1)
        except requests.RequestException:
            log_error("Internet connection lost. Please check your internet connection.")
            return False
def wait_for_tor(timeout=60):
    """
    #### Waits until the Tor SOCKS proxy is responsive or times out\n
    Attempts multiple connections via SOCKS5 until one succeeds or time runs out.
    ***
    Returns:
        bool: True if Tor responded, False if timeout occurred.
    """
    import socket
    import socks

    log_info(f"Waiting for Tor SOCKS proxy to become responsive... (timeout: {timeout}s)")
    start = time.time()

    while time.time() - start < timeout:
        try:
            # Try connecting to api.ipify.org via SOCKS5
            s = socks.socksocket()
            s.set_proxy(socks.SOCKS5, "127.0.0.1", 9050)
            s.settimeout(5)
            s.connect(("api.ipify.org", 80))
            s.close()
            log_success("Tor SOCKS5 proxy is responding.")
            return True
        except Exception as e:
            time.sleep(2)

    log_error("Timed out waiting for Tor SOCKS5 proxy.")
    return False



# CLI entry point
def main():
    signal.signal(signal.SIGINT, signal_handler)
    # Use SIGBREAK for Windows, SIGQUIT for Unix-like systems.
    if is_windows():
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, signal_handler)
    elif hasattr(signal, 'SIGQUIT'):
        signal.signal(signal.SIGQUIT, signal_handler)
    
    # Argument parsing
    parser = argparse.ArgumentParser(description="TorNet - Automate IP address changes using Tor")
    parser.add_argument('--interval', type=str, default=60, help='Time in seconds between IP changes')
    parser.add_argument('--count', type=int, default=10, help='Number of times to change the IP. If 0, change IP indefinitely')
    parser.add_argument('--ip', action='store_true', help='Display the current IP address and exit')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically fix issues (install/upgrade packages)')
    parser.add_argument('--stop', action='store_true', help='Stop all Tor services and tornet processes and exit')
    parser.add_argument('--version', action='version', version=f'%(prog)s {VERSION}')
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
