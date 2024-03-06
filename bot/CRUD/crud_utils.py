from bot.CRUD.db_util import get_connection


def save(phone, chat_id):
    try:
        with get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute('INSERT INTO users (phone, chat_id) VALUES (%s,%s) RETURNING phone', (phone, chat_id))
            connection.commit()
            inserted_phone = cursor.fetchone()
            return inserted_phone[0]
    except (Exception) as error:
        print(error)


def get_phone(chat_id):
    try:
        with get_connection().cursor() as cursor:
            cursor.execute('SELECT phone FROM USERS WHERE chat_id=%s', (chat_id,))
            data = cursor.fetchone()

    except (Exception) as error:
        print(error)
    return data


# def get_table(table_name):
#     query = sql.SQL(GET_TABLE).format(sql.Identifier(table_name))
#     try:
#         connection = get_connection()
#         cursor = connection.cursor()
#         cursor.execute(query)
#         data = cursor.fetchall()
#         cursor.close()
#         connection.close()
#     except (Exception) as error:
#         print(error)

#     return data



# def get_column(column_name, table_name, where, value):
#     query = sql.SQL(GET_COLUMN).format(sql.Identifier(column_name),
#                                        sql.Identifier(table_name),
#                                        sql.Identifier(where))
#     try:
#         connection = get_connection()
#         cursor = connection.cursor()
#         cursor.execute(query, (value,))
#         data = cursor.fetchall()
#         cursor.close()
#         connection.close()
#     except (Exception) as error:
#         print(error)
#     if data:
#         return data[0][0]

#     return data


# def get_user(table_name, where, value):
#     user_data = {}
#     data = get_field(table_name, where, value)
#     if data:
#         user_data.update({'id': data[0],
#                           'first_name': data[1],
#                           'last_name': data[2],
#                           'password': data[3],
#                           'email': data[4]})

#     return user_data




# def update(table_name, column_name, where, new_value, where_value):
#     query = sql.SQL(UPDATE).format(sql.Identifier(table_name),
#                                    sql.Identifier(column_name),
#                                    sql.Identifier(where))
#     try:
#         connection = get_connection()
#         cursor = connection.cursor()
#         cursor.execute(query, (new_value, where_value))
#         connection.commit()
#         cursor.close()
#         connection.close()
#     except (Exception) as error:
#         print(error)
#         return False

#     return True


# def delete(table_name, where, values):
#     query = sql.SQL(DELETE).format(sql.Identifier(table_name),
#                                    sql.Identifier(where))
#     try:
#         connection = get_connection()
#         cursor = connection.cursor()
#         cursor.execute(query, (values,))
#         connection.commit()
#         cursor.close()
#         connection.close()
#     except (Exception) as error:
#         print(error)
#         return False

#     return True


# def to_string_table(table):
#     users = []
#     data = get_table(table)
#     for user in data:
#         users.append({'id': user[0],
#                       'first_name': user[1],
#                       'last_name': user[2],
#                       'password': user[3],
#                       'email': user[4]})

#     return users
