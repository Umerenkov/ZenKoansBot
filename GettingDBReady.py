import sqlite3
from collections import OrderedDict

koans = OrderedDict()
with open('koans.txt', 'r', encoding='utf-8') as file:
    text = file.read()
    
for i in range(102):
    koans[str(i)] = text[text.find(str(i) + '.')+2+len(str(i)): text.find(str(i+1) + '.')].strip()

conn = sqlite3.connect('koans.db')
cur = conn.cursor()

# cur.execute('CREATE TABLE Koans (Number int, Koan text, Done int)')
# for koan in koans:
#     cur.execute('INSERT INTO Koans VALUES (?,?,0)',(int(koan), koans[koan]))

conn.commit()
conn.close()
