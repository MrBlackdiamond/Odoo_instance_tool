import psycopg2
from psycopg2 import sql

# Database connection parameters
db_params = {
    "host": "localhost",
    "database": "postgres",  # Default database
    "user": "postgres",  # PostgreSQL admin user
    "password": "admin@12345"  # Admin user's password
}

# New user details
new_user = "test_user"
new_password = "admin@12345"

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**db_params)
    conn.autocommit = True  # Required for creating users
    
    # Create a cursor object
    cur = conn.cursor()

    # SQL to create a new user
    create_user_sql = f"CREATE USER {new_user} WITH PASSWORD %s;"
    alter_user_superusr = f"ALTER USER {new_user} WITH SUPERUSER;"
    alter_user_createdb = f"ALTER USER {new_user} WITH CREATEDB;"
    
    # Execute the SQL queries
    cur.execute(create_user_sql, (new_password,))  # Use tuple for parameters
    cur.execute(alter_user_superusr)
    cur.execute(alter_user_createdb)

    print(f"User '{new_user}' created successfully!")

    # Close cursor and connection
    cur.close()
    conn.close()

except Exception as e:
    print(f"Error: {e}")
