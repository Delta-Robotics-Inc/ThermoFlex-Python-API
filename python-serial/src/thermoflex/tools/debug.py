DEBUG_LEVELS = {
    'NONE': 0,
    'ERROR': 1,
    'WARNING': 2,
    'INFO': 3,
    'DEBUG': 4
}

TF_DEBUG_LEVEL = DEBUG_LEVELS['ERROR']

# Set the debug level
def set_debug_level(level):
    global TF_DEBUG_LEVEL
    TF_DEBUG_LEVEL = DEBUG_LEVELS[level]

# Debug to console based on level
def debug(level, process_name ,message):
    if TF_DEBUG_LEVEL >= level:
        level_name = [key for key, value in DEBUG_LEVELS.items() if value == level][0]
        print(message) # For now, just print the message.  If you want the level displayed, use the line below
        #print(f"{message}  | {level_name}: [{process_name}]")

# Debug to console based on level without newline
def debug_raw(level, message):
    if TF_DEBUG_LEVEL >= level:
        print(message, end='')