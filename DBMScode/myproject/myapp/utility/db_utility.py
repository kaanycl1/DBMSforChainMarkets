from django.db import connection

def execute_query(sql, params=None):
    """
    Executes a raw SQL query and fetches results if applicable.

    :param sql: The raw SQL query string.
    :param params: Optional parameters for the SQL query.
    :return: Query result rows if the query returns data; otherwise, None.
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        if cursor.description:  # If the query returns rows (e.g., SELECT)
            return cursor.fetchall()
        
def execute_sql_file(file_path, params=None):
    with open(file_path, 'r') as file:
        sql = file.read()
    return execute_query(sql, params)