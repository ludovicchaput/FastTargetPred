

def count(input: int):
    s = '{:b}'.format(input)
    count = 0
    for c in s:
        count += int(c, 10)
    return count

s = '['
l = []
for i in range(256):
    ci = count(i)
    s += str(ci) + ','
    l.append(ci)
s = s[:-1] + ']'

print(s)

print(l[0x03])