'''
Comments
'''
import threading as thr
import multiprocessing as mp
import os
import shutil as sh
import venv
from .controls import *

base_path = os.getcwd().replace("\\","/") + '/ThermoflexSessions'



COMSPATH = 'scripts/commands.py'
CONTPATH = 'scripts/controls.py' #TODO filepaths of installing scripts

#session controller class?

def threaded(func):
    global threadlist
    threadlist = []
    
    def wrapper(*args, **kwargs):
        thread = thr.Thread(target=func, args=args, kwargs = kwargs)
        thread.start()
        threadlist.append(thread)
        return thread

    return wrapper


   
class session(venv.EnvBuilder): 
    sessionl = []
    sescount = len(session.sessionl)
    
    
    def __init__(self, connode:object,iden = sescount+1): #venv directory, scripts, 
        
        super().__init__(system_site_packages=True)
        self.id = iden
        self.scripts = []#[COMSPATH,CONTPATH]; using system site packages until further notice
        session.sessionl.append(self)
        self.connode = connode
        self.environment = None #setup by launch; path dir string
        self.running = False
        self.launch()
        self.setlogpath()
        
    
    def launch(self):
        
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
    def run(self):
        self.running = True
        while self.running == True:
            self.connode.update()
            logTo(self.connode, self.connode.buffer, dt=1)
            for x in self.connode.lastcmd:
                logTo(self.connode, x, dt=0)    
    def stop(self):
        self.running = False
    
    
    def switch(self,sess:object):
        session.sessionl[sess].stop()
        os.chdir(self.environment)
        session.sessionl[self].run()        
        
        #switch cwd to new sess
    
    def end(self): 
        
        sh.copytree(f'{self.environment}/logs' , f'{base_path}/Session{self.id} log', dirs_exist_ok = True)
        os.remove(self.environment)
        self.connode.closePort()
    
    def logging(self):
        pass
        
    
        
    def setlogpath(self):
        
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

