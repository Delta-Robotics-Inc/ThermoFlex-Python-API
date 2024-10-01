# Look into Marlin printer software
"""
Created on Fri Sep 13 17:57:09 2024

@author: School
"""
import threading as thr
import multiprocessing as mp
import os
import shutil as sh
import venv
from thermoflex.controls import *

base_path = os.getcwd().replace("\\","/") + '/ThermoflexSessions'
sessionl = []


COMSPATH = '/path/to/commands.py'
CONTPATH = '/path/to/controls.py' #TODO filepaths of installing scripts

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

def multiprocess(func):
    pass

   
class session(venv.EnvBuilder): 
    sescount = len(sessionl)
    
    
    def __init__(self, connode:object,iden = sescount+1): #venv directory, scripts, 
        
        super().__init__()
        self.id = iden
        self.scripts = ['commands.py','controls.py']
        sessionl.append(self)
        self.connode = connode
        self.launch()
        self.environment = super().ensure_directories(f'{base_path}/session{self.id}').env_dir #environment object use
        self.running = False
       
        
    
    def launch(self):
        
        super().create(f'{base_path}/session{self.id}')
        self.setlogpath()
        os.makedirs(f'{base_path}/Session{self.id} log')
        for x in self.scripts:
            super().setup_scripts(x)    
    

    def run(self):#thread&multiprocessing
        self.running = True
        self.connode.logstate['binarylog'] = state        
        while self.running == True:
            logTo(self.connode, self.connode.buffer)
            self.connode.update() #terminal
    
    def stop(self):
        self.running = False
    
    
    def switch(self,sess:object):
        sessionl[sess].stop()
        sessionl[self].run()        
        
        pass #switch cwd to new sess
    
    def end(self): 
        
        sh.copytree(f'{self.environment}/logs' , f'{base_path}/Session{self.id} log', dirs_exist_ok = True)
        os.remove(self.environment.env_dir) #remove path w/ string, self.environment is an object
        
    
    def logging(self):
        from .controls import logTo
        
    
        
    def setlogpath(self):
        BINARYDATA = f'{self.environment}/logs/node{self.connode.idnum}logdata/binary/logdata.ses'
        NODEDATA = f'{self.environment}/logs/node{self.connode.idnum}logdata/node.csv'
        with open(BINARYDATA, 'w') as f:
            pass
        with open(NODEDATA, 'w') as f:
            pass
        for x in range(0,self.connode.mosports):
            MUSCLEDATA = f'{self.environment}/logs/node{self.connode.idnum}logdata/M{x+1}.csv'
            with open(MUSCLEDATA, 'w') as f:
                pass

        
        
def activesession(session:object):
    session.run()
    
def sessionswitch(oldsess:object,newsess:object):
    newsess.switch(oldsess)
    
def endsession(session:object):
    session.end()
            

for th in threadlist:
        th.join()
#node and can bus id
#nodenetwork and node
#pc asks fro can ids
#double id system
#[sendr address][dest address][can id][port][info]