from sys import getsizeof
DEBUG_LEVELS = {
    'NONE': 0,
    'DEVICE': 1,
    'ERROR': 2,
    'WARNING': 3,
    'INFO': 4,
    'DEBUG': 5
}

class Debugger:
    TF_DEBUG_LEVEL = DEBUG_LEVELS['ERROR']
    DEBUG_LOG = False
    DEBUG_PRINT = True
    DEBUG_SESSION = None
    ROLLING_LOG = []  

    # Set the debug level
    def set_debug_level(level):
        
        Debugger.TF_DEBUG_LEVEL = DEBUG_LEVELS[level]

    # Debug to console based on level
    def debug(level, process_name ,message):
        if Debugger.TF_DEBUG_LEVEL >= level:
            level_name = [key for key, value in DEBUG_LEVELS.items() if value == level][0]
            if Debugger.DEBUG_PRINT == True:    
                print(message) # For now, just print the message.  If you want the level displayed, use the line below
                #print(f"{level_name}: [{process_name}] | {message}")

            if Debugger.DEBUG_LOG == True: Debugger.DEBUG_SESSION.logging((level_name,message.replace('\n','|')),3)
    
    #debugger keeps a rolling log            
    def ROLL(data):
        log = Debugger.ROLLING_LOG
        if getsizeof(log) >= 32000:
            log.pop(0)
        log.append(data)
    
    # Debug to console based on level without newline
    def debug_raw(level, message):
        if Debugger.TF_DEBUG_LEVEL >= level:
            Debugger.ROLL((level,message))
            if Debugger.DEBUG_PRINT == True: 
                print(message, end='')
            if Debugger.DEBUG_LOG == True: Debugger.DEBUG_SESSION.logging((level,message.replace('\n','|')),3)



