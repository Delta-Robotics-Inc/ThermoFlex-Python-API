import struct as st
a = 'hunter73'
b = [0x7e,0x8f,0x8f,0x5b,a,0x9d]
print(a,b)
p=b''
for x in b:
            if type(x) == str:
                p += bytes(x,'ascii')
            elif type(x) == int:
                p += st.pack('!B', x)
print(p)


for y in p:
    print(y)