import sqlite3

def save_to_db(question, user_input, gpt_response):
    conn = sqlite3.connect("responses.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS responses
                 (question TEXT, user_input TEXT, gpt_response TEXT)''')
    c.execute("INSERT INTO responses VALUES (?, ?, ?)", (question, user_input, gpt_response))
    conn.commit()
    conn.close()
