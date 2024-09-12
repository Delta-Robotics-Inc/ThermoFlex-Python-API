import pandas as pd
import numpy as np

filepath = 'C:/Users/School/Delta/Obsidian/Python-Serial/python-serial/test/Log folder/log.csv'

logdata = "58649 47.003586 11111111 -1141.061157 M1 3 14 0 0 0.000000 0.00 0.000000 0.000000 10000000000.000000 -1.000000 0.000000 0 M2 6 15 0 0 0.000000 0.00 0.000000 0.000000 10000000000.000000 -1.000000 0.000000 0"


#splitbuff = {"Node":[0.52,0.025,57895,354,None,None,None],
             #"M1":[15.2,4512,46.15,25.0,25,77.5,69],
                 #"M2":[15.2,4512,46.15,25.0,25,77.5,69]}

nodedict = {"A":[],"B":[],"C":[],"D":[]}
m1dict = {"A":[],"B":[],"C":[],"D":[],"E":[],"F":[],"G":[],"H":[],"I":[],"J":[],"K":[],"L":[]}
m2dict = {"A":[],"B":[],"C":[],"D":[],"E":[],"F":[],"G":[],"H":[],"I":[],"J":[],"K":[],"L":[]}

#buff = pd.DataFrame(splitbuff)
def data(logdata = logdata):
    
    try: #fix data splitting and parsing
            splitbuff = logdata.split(' ')
            splitnode = splitbuff[:splitbuff.index('M1')]
            splitm1 = splitbuff[splitbuff.index('M1') + 1:splitbuff.index('M2')]
            splitm2 = splitbuff[splitbuff.index('M2') + 1:]
    except IndexError:
            pass
    nodelist = list(nodedict.keys())
    m1list = list(m1dict.keys())
    m2list = list(m2dict.keys())
    
    
    
    for x in nodelist:
        nodedict[x].append(splitnode[nodelist.index(x)])
    
    for x in m1list:
        m1dict[x].append(splitm1[m1list.index(x)])
    
    for x in m2list:
        m2dict[x].append(splitm2[m2list.index(x)])
    
data(logdata)
data(logdata)
data(logdata)

    
df = pd.DataFrame(nodedict)
df1 = pd.DataFrame(m1dict)
df2 = pd.DataFrame(m2dict)


    
print(df,'\n')
print(df1,'\n')
print(df2,'\n')