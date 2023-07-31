import pyodbc
server = 'sql-chatbot-server.database.windows.net'
database = 'sql-chatbot'
username = 'test-chatbot'
password = 'bMp{]nzt1'
driver= '{ODBC Driver 17 for SQL Server}'

conn = pyodbc.connect(f'DRIVER={driver};SERVER=tcp:{server};PORT=1433;DATABASE={database};UID={username};PWD={password}')

cursor = conn.cursor()

# Current database sql-chatbot has 1 table history which contains 4 columns
# email: user's email, as the primary key
# chat: chat history between the user and the bot
# post_leave: placeholder
# del_leave: placeholder

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


def add_to_history_sql(query, response, email):
    n = 3
    cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
    hist = cursor.fetchone()[0].split('<sep>')

    hist.append(f"{query}||{response}")
    if len(hist) > n:
        hist = hist[len(hist) - n:]

    res = "<sep>".join(hist)
    cursor.execute(f"""UPDATE history
SET chat = '{res}' WHERE email = '{email}';""")
    conn.commit()


def get_history_as_txt_sql(email):
    cursor.execute(f"""SELECT chat FROM history WHERE email = '{email}';""")
    hist = cursor.fetchone()[0].split('<sep>')

    txt = ""
    for row in hist:
        i = row.split('||')

        try:
            txt += f"\n<|im_start|>user\n{i[0]}\n<|im_end|>\n"
            txt += f"<|im_start|>assistant\n{i[1]}\n<|im_end|>"
        except IndexError:
            return ""

    return txt


# print(get_history_as_txt_sql('bao.ho@nois.vn'))
# cursor.execute("""UPDATE history
# SET chat = ''
# WHERE email = 'bao.ho@nois.vn';""")
#
# conn.commit()

# cursor.execute("""ALTER TABLE history
# charset=utf8;""")
#
# conn.commit()

# cursor.execute("""UPDATE history
# SET chat = N''
# WHERE email = 'bao.ho@nois.vn';""")
#
# conn.commit()
#
# cursor.execute("""SELECT chat FROM history;""")
# rows = cursor.fetchall()
#
# for i in rows:
#     print(i[0])

cursor.execute("SELECT chat from history where email = 'thien.tran@nois.vn';")
print(cursor.fetchone())
