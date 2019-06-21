DEBUG = True

CRED = '\033[91m'
CGREEN = '\033[92m'
CYELLOW = '\033[93m'
CMAGENTA = '\033[95m'
CCYAN = '\033[96m'
CEND = '\033[0m'

def info(*args):
  print(*args)

def debug(*args, color=CYELLOW):
  if DEBUG:
    print(color, *args, CEND)

def error(*args):
  print(CRED, *args, CEND)