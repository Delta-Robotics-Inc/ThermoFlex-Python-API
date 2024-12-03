a = 'all m2'
b = 'm1 m3'
c = 'M2 m1 m4'


inta = a.split(' ')
intb = b.split('m')
intc = c.strip().lower().split('m')

print(inta, intb, intc)

