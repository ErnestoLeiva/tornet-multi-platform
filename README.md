<img src = "https://i.imgur.com/Mo2HtCS.png" alt="Tor logo">**NET-MP**

[![PyPI version](https://img.shields.io/pypi/v/tornet-mp)](https://pypi.org/project/tornet-mp)
[![Python](https://img.shields.io/pypi/pyversions/tornet-mp)](https://pypi.org/project/tornet-mp)

---

Automate public-IP rotation through the Tor network on **Windows, macOS and Linux**.

* 🛡️  Hide your real IP behind Tor exit nodes  
* 🔄  Rotate on a timer or on demand  
* ⚙️  Self-installs missing prerequisites (`pip`, `requests[socks]`, `Tor`)  
* 📜  Clear, color-coded logs (all levels shown by default)  
* 🐍  Tiny Python API for scripting

---

## Installation

```bash
pip install tornet-mp
```

Tor binary required - if `tor` is not on your `PATH`, run
`tornet-mp --auto-fix` and the tool will install it where possible.

## Development / editable install

```bash
git clone https://github.com/ErnestoLeiva/tornet-mp.git
cd tornet-mp

# optional but recommended: create and activate a virtual-env
python -m venv .venv           # use  py -m venv .venv  on Windows
# macOS/Linux:  source .venv/bin/activate
# Windows CMD:  .venv\Scripts\activate.bat
# Win PowerShell: .venv\Scripts\Activate.ps1

# install in editable (“-e”) mode
python -m pip install -e .
```

## Quick start

```bash
# show current (Tor/non-Tor) exit IP and exit
tornet-mp --ip

# rotate every 60 seconds, 10 times (default)
tornet-mp

# rotate every 90 seconds, 5 times
tornet-mp --interval 90 --count 5

# rotate on a random interval between 60-120 seconds, forever
tornet-mp --interval "60-120" --count 0
```

## CLI options

| Flag                 | Description                                      | Default |
| -------------------- | ------------------------------------------------ | ------- |
| `--interval SECONDS` | Delay (or range e.g. `60-120`) between rotations | `60`    |
| `--count N`          | Rotation cycles; `0` = infinite                  | `10`    |
| `--ip`               | Show current exit IP and quit                    | —       |
| `--auto-fix`         | Re-install/upgrade dependencies and Tor          | —       |
| `--stop`             | Stop Tor services and TorNet-MP processes        | —       |
| `-V / --version`     | Print version                                    | —       |

### Environment variables

| Variable         | Purpose                     | Default     |
| ---------------- | --------------------------- | ----------- |
| `TOR_SOCKS_HOST` | Hostname of Tor SOCKS proxy | `127.0.0.1` |
| `TOR_SOCKS_PORT` | Port of Tor SOCKS proxy     | `9050`      |

## Configuring Your Browser to Use TorNet

### To ensure your browser uses the Tor network for anonymity, you need to configure it to use TorNet's proxy settings

#### ⚠️ Chrome and Chromium-based browsers do not support SOCKS proxies natively without command-line flags or extensions. Use `FoxyProxy` or similar tools for full control

### **Firefox**

* Go to `Preferences` > `General` > `Network Settings`.
* Select `Manual proxy configuration`.
* Enter `127.0.0.1` for `SOCKS Host` and `9050` for the `Port` (or your specified values if different).
* Ensure the checkbox `Proxy DNS when using SOCKS v5` is checked.
* Click `OK`.

<img src="https://i.imgur.com/jDLV6BZ.png" alt="Firefox Configuration Example">

## Python use

```python
from tornet_mp import initialize_environment, ma_ip, change_ip

initialize_environment()
print("Current IP:", ma_ip())
print("Switching…")
print("New Tor IP:", change_ip())
```

If Tor is already installed and running you can skip `initialize_environment()` and call `ma_ip()` / `change_ip()` directly.

## How it works

1. Ensures Tor, requests[socks] and PySocks are present

2. Starts the Tor background service (systemd, Brew, or raw binary)

3. Retrieves current exit IP via [https://check.torproject.org/api/ip](https://check.torproject.org/api/ip)

4. Sends SIGHUP / service reload to request a new circuit on schedule

5. Logs every step with colored categories (INFO, WARN, ERROR, etc.)

## Contributing

Bug reports and PRs are welcome!
Style is enforced with [pre-commit](https://pre-commit.com).  
After cloning, run:

```bash
pip install pre-commit
pre-commit install
```

## Lineage & Credits

This project began life as [tornet](https://github.com/ByteBreach/tornet) by Mr Fidal.  
It was later reimagined and extended independently by [Ayad Seghairi](https://github.com/ayadseghairi/tornet).

**TorNet‑MP** builds on both prior versions, refactoring the codebase, adding cross‑platform support (Windows, macOS, Linux), modern packaging, richer logging, automatic dependency management, and a polished CLI/UI.

## License

MIT © 2025 Ernesto Leiva
