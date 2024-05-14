import sqlite3

# Connect to the SQLite database file
connection = sqlite3.connect('database.db')

try:
    # Show the table before delete
    print("Show the table before delete")
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM User')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    print('\n' * 3)

    # Retrieve the name from the User table based on the provided row ID
    row_id_to_delete = input('Enter the ID of the row you want to delete: ')
    cursor.execute('SELECT username FROM User WHERE id = ?', (row_id_to_delete,))
    user_name = cursor.fetchone()[0]

    # Delete the row from the Performance table based on the retrieved name
    cursor.execute('DELETE FROM Performance WHERE employee_name = ?', (user_name,))
    connection.commit()

    # Delete the row from the User table
    cursor.execute('DELETE FROM User WHERE id = ?', (row_id_to_delete,))
    connection.commit()

    # Show the table after delete
    print("Show the table after delete")
    cursor.execute('SELECT * FROM User')
    rows = cursor.fetchall()
    for row in rows:
        print(row)

except sqlite3.Error as e:
    print("SQLite error:", e)
finally:
    # Close the cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()
