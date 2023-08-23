import pyodbc

server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver = '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect(
    f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')
cursor = conn.cursor()
cursor.execute(
    f"""DELETE FROM history WHERE email = 'thien.tran@nois.vn';""")
conn.commit()
# cursor.execute("select * from history")
# row = cursor.fetchone()
# while row:
#     print(str(row[0]) + " " + str(row[1]))
#     row = cursor.fetchone()
cursor.close()
conn.close()
