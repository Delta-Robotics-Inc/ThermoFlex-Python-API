import struct as st
a = 'hunter73'
b = [0x7a,0x4d,0x44,0x7e,0x00,12,0x01,0x02,0x03,a,0x9d]
print(a,b)
p=b''
for x in b:
            if type(x) == str:
                p += bytes(x,'ascii')
            elif type(x) == int:
                p += st.pack('!B', x)
print(p)
for x in p:
    print(x)
    if b'\x7e' == x:
        z = p.index(x)
        print(z,z+3)
        l = p[z+1:z+3]
        m = ''
        for y in l:
            m += str(y)
        m = int(m)-4
        print(m)
        msg = (p[z+3:z+6],p[z+6:z+6+m].decode('ascii'))
        print(msg)
        break