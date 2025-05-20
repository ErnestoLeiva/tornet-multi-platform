import signal
import atexit
from tornet import (
    ma_ip, change_ip, initialize_environment,
    change_ip_repeatedly, signal_handler, stop_services, is_windows
)

# Register signal and cleanup handlers
signal.signal(signal.SIGINT, signal_handler)
if is_windows() and hasattr(signal, 'SIGBREAK'):
    signal.signal(signal.SIGBREAK, signal_handler)
atexit.register(stop_services)


# Initialize the environment (install dependencies and start Tor)
initialize_environment()

# Get the current IP
#current_ip = ma_ip()
#print("Current IP:", current_ip)

# Change the IP once
#new_ip = change_ip()
#print("New IP:", new_ip)

# Change the IP repeatedly
change_ip_repeatedly("60", 0)
