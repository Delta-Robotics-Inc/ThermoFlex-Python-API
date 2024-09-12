import pandas as pd


logdata = "58649 47.003586 11111111 -1141.061157 M1 3 14 0 0 0.000000 0.00 0.000000 0.000000 10000000000.000000 -1.000000 0.000000 0 M2 6 15 0 0 0.000000 0.00 0.000000 0.000000 10000000000.000000 -1.000000 0.000000 0"

try: #fix data splitting and parsing
        splitbuff = logdata.split(' ')
        splitnode = splitbuff[:splitbuff.index('M1')]
        splitm1 = splitbuff[splitbuff.index('M1') + 1:splitbuff.index('M2')]
        splitm2 = splitbuff[splitbuff.index('M2') + 1:]
except IndexError:
        pass
    

print(len(splitnode))
df = pd.DataFrame(splitnode)
 
print(df)