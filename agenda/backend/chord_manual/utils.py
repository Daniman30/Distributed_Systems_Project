table = {}
id = 240
for i in range(8):
    table[(id + 2**i) % 256] = id

print(table)

for row in table.items():
    id, owner = row
    print(id)
    print(owner)
    

