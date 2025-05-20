# log.py
white   = "\033[97m"
green   = "\033[92m"
red     = "\033[91m"
yellow  = "\033[93m"
blue    = "\033[94m"
magenta = "\033[95m"
cyan    = "\033[36m"
gray    = "\033[90m"
reset   = "\033[0m"

def log(message, tag="+", color=white):
    print(f"{white} [{color}{tag}{white}] {color}{message}{reset}")

def log_success(message):      log(message, tag="+", color=green)
def log_info(message):         log(message, tag="~", color=blue)
def log_notice(message):       log(message, tag="*", color=cyan)
def log_minor(message):        log(message, tag="~", color=gray)
def log_warn(message):         log(message, tag="!", color=yellow)
def log_error(message):        log(message, tag="!", color=red)
def log_change(message):       log(message, tag="+", color=magenta)