import sqlite3
import json

conn = sqlite3.connect('crm.db')
c = conn.cursor()
c.execute('SELECT email, rol, nombre_completo, telefono_whatsapp FROM usuarios')
users = c.fetchall()
print(json.dumps(users, indent=2))
conn.close()
