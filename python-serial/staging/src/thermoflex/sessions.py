'''
Comments
'''
import threading as thr
import multiprocessing as mp
import os
import shutil as sh
import venv
from .tools.packet import deconstructor
base_path = os.getcwd().replace("\\","/") + '/ThermoflexSessions'
sess_filepath = os.getcwd().replace("\\","/") #set base filepath


COMSPATH = 'scripts/commands.py'
CONTPATH = 'scripts/controls.py' #TODO filepaths of installing scripts

def threaded(func):
    global threadlist
    threadlist = []
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        threadlist.append(thread)
        return thread

    return wrapper

def logTo(node:object, logdata, dt:int):
    '''
    
    Sends log data to terminal output, directory or file.
    Writes log data to a file.
    
    '''
    filepath = sess_filepath + f'\logs\node{node.idnum}logdata'
    
    
    
    nodelist = list(node.nodedict.keys())
    m1list = list(node.m1dict.keys())
    m2list = list(node.m2dict.keys())
    nodedict2 = node.nodedict.copy()
    m1dict2 = node.m1dict.copy()
    m2dict2 = node.m2dict.copy()
    
    try:
        logdata  # Properly decode and strip the data
        if not logdata:
            pass #does nothing statement upon being empty

        else:   
            
            try: 
                if dt == 0:
                    readlog = deconstructor(logdata)
                    splitbuff = readlog.split(' ')
                    splitnode = splitbuff[:splitbuff.index('M1')]
                    splitm1 = splitbuff[splitbuff.index('M1') + 1:splitbuff.index('M2')]
                    splitm2 = splitbuff[splitbuff.index('M2') + 1:]
                
                    if node.logstate['printlog'] == True:
                        print(str(readlog))
                    
                    if node.logstate['dictlog'] == True: #checks log data         
                        
                        for x in nodelist:
                            if x == 'A' or x == 'C':
                                node.nodedict[x].append(int(splitnode[nodelist.index(x)]))
                            elif x == 'B' or x == 'D':
                                node.nodedict[x].append(float(splitnode[nodelist.index(x)]))
            
                        for x in m1list:
                            if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                                node.m1dict[x].append(int(splitm1[m1list.index(x)]))
                            else:    
                                node.m1dict[x].append(float(splitm1[m1list.index(x)]))
            
                        for x in m2list:
                            if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                                node.m2dict[x].append(int(splitm2[m2list.index(x)]))
                            else:
                                node.m2dict[x].append(float(splitm2[m2list.index(x)]))
                                
                    if node.logstate['binarylog'] == True:
                        with open('{filepath}\binary\logdata.ses', 'a') as f:
                            f.write(logdata)
                    
                    if node.logstate['filelog'] == True: 
                        
                        for x in nodelist: 
                            if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                                nodedict2[x] = int(splitnode[nodelist.index(x)])
                            else:
                                nodedict2[x] = float(splitnode[nodelist.index(x)])
                        
                        for x in m1list:
                            if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                                m1dict2[x] = int(splitm1[m1list.index(x)])
                            else:
                                m1dict2[x] = float(splitm1[m1list.index(x)])
                        
                        for x in m2list:
                            if x == 'A' or x == 'B' or x == 'C' or x == 'D' or x == 'L':
                                m2dict2[x] = int(splitm2[m2list.index(x)])
                            else:
                                m2dict2[x] = float(splitm2[m2list.index(x)])
                            #pandas write to .csv
                            
                        pd.DataFrame(nodedict2).to_csv(path = filepath + '\node.csv', mode = 'a')
                        pd.DataFrame(m1dict2).to_csv(path = filepath + '\M1.csv', mode = 'a')
                        pd.DataFrame(m2dict2).to_csv(path = filepath + '\M2.csv', mode = 'a')
            
                elif dt == 1:
                    readlog = deconstructor(logdata)
                    if node.logstate['printlog'] == True:
                        print(str(readlog))
                    if node.logstate['binarylog'] == True:
                        with open(f'{filepath}\binary\logdata.ses', 'a') as f:
                            f.write(logdata)
                    if node.logstate['dictlog'] == True:
                        pass
                    if node.logstate['filelog'] == True:
                        with open(f'{filepath}\sendlog.txt', 'wt') as f:
                            f.write(readlog)
            except IndexError:
                pass
            except ValueError:
                pass  

    finally:
        pass


   
class session(venv.EnvBuilder): 
    sessionl = []
    sescount = len(sessionl)    
    
    def __init__(self, network,iden = sescount+1): #venv directory, scripts, 
        
        super().__init__(system_site_packages=True)
        self.id = iden
        self.scripts = []#[COMSPATH,CONTPATH]; using system site packages until further notice
        session.sessionl.append(self)
        self.networks = []
        self.networks.append(network)
        self.environment = None #setup by launch; path dir string
        self.running = False
        #self.launch()
        #self.setlogpath()
        
    
    def launch(self): #opens all files and folders for sessions
        
        try:
            fpath = os.path.exists(f'{base_path}/session{self.id}')
            if fpath == False:            
                super().create(f'{base_path}/session{self.id}')
                os.makedirs(f'{base_path}/Session{self.id} log')
                for x in self.scripts:
                    super().setup_scripts(x) 
        finally:
            self.connode.logstate['binarylog'] = True
            self.environment = super().ensure_directories(f'{base_path}/session{self.id}').env_dir   
            os.chdir(self.environment)
            

    @threaded
    def run(self): #runs the session
        self.running = True
        while self.running == True:
            controls.update()
            logTo(self.connode, self.connode.buffer, dt=1)
            for x in self.connode.lastcmd:
                logTo(self.connode, x, dt=0)    
    def stop(self):#stops the session
        self.running = False
    
    
    def switch(self,sess:object): #switches the session
        session.sessionl[sess].stop()
        os.chdir(self.environment)
        session.sessionl[self].run()        
        
    
    
    def end(self): #ends the session
        
        sh.copytree(f'{self.environment}/logs' , f'{base_path}/Session{self.id} log', dirs_exist_ok = True)
        os.remove(self.environment)
        self.connode.closePort()
    
    def logging(self,cmd,tp): #logs the session
        print(cmd,tp)
        if tp == 0:
            for net in self.networks:
                for node in net.nodenet:
                    print(node.addr)
                    print(cmd[0])
                    if cmd[0] == node.addr:
                        print(node,cmd[1],tp)
                        logTo(node,cmd[1],tp)  
        elif tp == 1:
            logTo(cmd.destnode,cmd.construct,tp)
                
    def setlogpath(self): #creates logpath
        
        os.makedirs(f'{self.environment}/logs/node{self.connode.idnum}logdata/binary')
        BINARYDATA = f'{self.environment}/logs/node{self.connode.idnum}logdata/binary/logdata.ses'
        NODEDATA = f'{self.environment}/logs/node{self.connode.idnum}logdata/node.csv'
        with open(BINARYDATA, 'xb') as f:
            pass
        with open(NODEDATA, 'xt') as f:
            pass
        for x in range(0,self.connode.mosports):
            MUSCLEDATA = f'{self.environment}/logs/node{self.connode.idnum}logdata/M{x+1}.csv'
            with open(MUSCLEDATA, 'xt') as f:
                pass
            
        
        
def activesession(session:object):
    session.run()
    
def sessionswitch(oldsess:object,newsess:object):
    newsess.switch(oldsess)
    
def endsession(session:object):
    session.end()
    del session
            

for th in threadlist:
        th.join()

