import pyodbc
server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver= '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect(f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')

cursor = conn.cursor()

# cursor.execute("""CREATE TABLE history (
#     email varchar(255) PRIMARY KEY,
#     chat TEXT
# );""")
#
# conn.commit()

# cursor.execute("""INSERT INTO history
# values ('bao.ho@nois.vn', 'chungus');""")
#
# conn.commit()

# cursor.execute("""SELECT chat FROM history;""")
# rows = cursor.fetchall()
#
# for i in rows:
#     print(i[0])

def add_to_history(query, response, email, n=3):
    cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
    hist = cursor.fetchone()[0].split('<sep>')

    hist.append(f"{query}||{response}")
    res = "<sep>".join(hist)



    return res

print(add_to_history('Hello', 'dingus', 'bao.ho@nois.vn'))
