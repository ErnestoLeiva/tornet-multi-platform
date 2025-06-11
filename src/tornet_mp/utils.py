import importlib
import os
import platform
import subprocess

from .log import log_error, log_minor


# Platform determination
def is_arch_linux() -> bool:
    return os.path.exists("/etc/arch-release") or os.path.exists("/etc/manjaro-release")


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def is_macos() -> bool:
    return platform.system().lower() == "darwin"


def brew_exists() -> bool:
    """Checks whether Homebrew is installed on macOS."""
    try:
        subprocess.check_output("which brew", shell=True)
        return True
    except subprocess.CalledProcessError:
        return False


# Installation functions
def install_pip() -> None:
    """
    #### Installs pip (Python package manager) based on the current OS.\n
    """
    if is_arch_linux():
        try:
            subprocess.check_output("pacman -Qi python-pip", shell=True)
            log_minor("pip is already installed.")
        except subprocess.CalledProcessError:
            log_minor("pip not found, installing...")
            subprocess.check_output(
                "sudo pacman -Sy python-pip --noconfirm", shell=True
            )
            log_minor("pip installed successfully.")
    elif is_windows():
        try:
            subprocess.check_output("where pip", shell=True)
            log_minor("pip is already installed.")
        except subprocess.CalledProcessError:
            log_minor(
                "pip not found. Please install Python from https://python.org and ensure pip is added to PATH."
            )
    elif is_macos():
        try:
            subprocess.check_output("which pip3", shell=True)
            log_minor("pip is already installed.")
        except subprocess.CalledProcessError:
            log_minor("pip not found, installing...")
            subprocess.run(
                ["brew", "install", "python3"], stdout=subprocess.DEVNULL, check=True
            )
            log_minor("pip installed successfully.")
    else:
        try:
            subprocess.check_output("dpkg -s python3-pip", shell=True)
            log_minor("pip is already installed.")
        except subprocess.CalledProcessError:
            log_minor("pip not found, installing...")
            subprocess.check_output("sudo apt update", shell=True)
            subprocess.check_output("sudo apt install python3-pip -y", shell=True)
            log_minor("pip installed successfully.")


def install_requests() -> None:
    """
    #### Installs the `requests` and `requests[socks]` Python packages if not already installed.\n
    """
    try:
        importlib.import_module("requests")
        importlib.import_module("socks")
        log_minor("requests is already installed.")
    except ImportError:
        log_minor("requests not found, installing...")
        pip_cmd = "pip install requests requests[socks]"
        if is_windows():
            subprocess.run(
                ["py", "-m", *pip_cmd.split()], stdout=subprocess.DEVNULL, check=True
            )
        else:
            subprocess.run(pip_cmd.split(), stdout=subprocess.DEVNULL, check=True)
        log_minor("requests installed successfully.")


def install_tor() -> None:
    """
    #### Installs the Tor binary using the appropriate method for the current OS.\n
    ***
    On:
    - **Linux**: Uses `pacman`
    - **macOS**: Uses `Homebrew`
    - **Windows**: Uses `Chocolatey` (installs it if needed)
    """
    if is_arch_linux():
        try:
            subprocess.check_output("which tor", shell=True)
            log_minor("tor is already installed.")
        except subprocess.CalledProcessError:
            log_minor("tor not found, installing...")
            subprocess.check_output("sudo pacman -Sy tor --noconfirm", shell=True)
            log_minor("tor installed successfully.")
    elif is_windows():
        try:
            subprocess.check_output("where tor", shell=True)
            log_minor("tor is already installed.")
        except subprocess.CalledProcessError:
            log_minor("tor not found.")

            if ensure_chocolatey_installed():
                log_minor("Installing Tor using Chocolatey...")
                try:
                    subprocess.check_call("choco install tor -y", shell=True)
                    log_minor("tor installed successfully.")
                except subprocess.CalledProcessError:
                    log_error(
                        "Failed to install Tor via Chocolatey. Please install it manually from https://www.torproject.org/download/"
                    )
    elif is_macos():
        try:
            subprocess.check_output("brew list tor", shell=True)
            log_minor("tor is already installed.")
        except subprocess.CalledProcessError:
            log_minor("tor not found, installing...")
            if not brew_exists():
                log_error(
                    "Brew not installed, install it from https://brew.sh/ then retry"
                )
            else:
                subprocess.run(
                    ["brew", "install", "tor"], stdout=subprocess.DEVNULL, check=True
                )
                log_minor("tor installed successfully.")
    else:
        try:
            subprocess.check_output("which tor", shell=True)
            log_minor("tor is already installed.")
        except subprocess.CalledProcessError:
            log_minor("tor not found, installing...")
            subprocess.check_output("sudo apt update", shell=True)
            subprocess.check_output("sudo apt install tor -y", shell=True)
            log_minor("tor installed successfully.")


def ensure_chocolatey_installed() -> bool:
    """
    #### Ensures that `Chocolatey` is installed on Windows.
    ##### If not found, attempts to install it via PowerShell.
    ***
    Returns:
        bool: True if Chocolatey is installed or was installed successfully, False otherwise.
    """
    try:
        subprocess.check_output("where choco", shell=True)
        log_minor("Chocolatey is already installed.")
        return True
    except subprocess.CalledProcessError:
        log_minor("Chocolatey not found. Attempting to install...")

        try:
            subprocess.check_call(
                "powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass "
                '-Command "Set-ExecutionPolicy Bypass -Scope Process -Force; '
                "[System.Net.ServicePointManager]::SecurityProtocol = "
                "[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))\"",
                shell=True,
            )
            log_minor("Chocolatey installed successfully.")
            return True
        except subprocess.CalledProcessError:
            log_error(
                "Failed to install Chocolatey. Please install it manually from https://chocolatey.org/install."
            )
            return False


# Manual execution
if __name__ == "__main__":
    install_pip()
    install_requests()
    install_tor()
