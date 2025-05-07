## 
# Fetch all the instance 
# display the data in the dashboard
# Then add a button as Remove Instance 
# when they click on the Remove Instance  
# remove the instance file 
# remove config file 
# remove service file
# remove nginx file 
# remove ssl certificate
# remove database user
# remove the DNS record from hostiger
# remove the database from database 

import os
import subprocess
import sys
import psycopg2
from psycopg2 import sql


def delete_postgres_database(db_name, master_password):
    db_params = {
        "host": "localhost",
        "database": "postgres",
        "user": "postgres",
        "password": master_password
    }
    try:
        # Establish connection to the PostgreSQL server
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True  # Ensure changes are committed immediately
        cur = conn.cursor()

        try:
            # Check if the database exists by listing all databases
            cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
            db_exists = cur.fetchone() is not None

            if db_exists:
                # Drop the database if it exists
                cur.execute(f"DROP DATABASE IF EXISTS {db_name};")
                print(f"Database {db_name} has been deleted successfully.")
            else:
                print(f"No such database found: {db_name}")

        except Exception as e:
            print(f"Error occurred while checking or deleting the database: {str(e)}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error connecting to PostgreSQL: {str(e)}")



def delete_postgres_user(db_user, master_password):
    db_params = {
        "host": "localhost",
        "database": "postgres",
        "user": "postgres",
        "password": master_password
    }
    try:
        # Establish connection to the PostgreSQL server
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True  # Ensure changes are committed immediately
        cur = conn.cursor()

        # First, check if the user exists
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (db_user,))
        user_exists = cur.fetchone() is not None

        if user_exists:
            # Drop the user if it exists
            cur.execute(f"DROP USER IF EXISTS {db_user};")
            print(f"User {db_user} has been deleted successfully.")
        else:
            print(f"No such user found: {db_user}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error connecting to PostgreSQL: {str(e)}")




def remove_instance(instance_name,domain_name):
    print(f"Removing the Odooo Instance: {instance_name}")
    commands = [
        ["sudo", "rm", "-rf", f"/opt/{instance_name}"],
        ["sudo", "rm", f"/etc/odoo/{instance_name}.conf"],
        ["sudo", "systemctl", "stop", instance_name],
        ["sudo", "systemctl", "disable", instance_name],
        ["sudo", "rm", f"/etc/systemd/system/{instance_name}.service"],
        ["sudo", "rm", f"/etc/nginx/sites-available/{domain_name}"],
        ["sudo", "rm", f"/etc/nginx/sites-enabled/{domain_name}"],
        ["sudo", "systemctl", "restart", "nginx"],
        ["sudo", "certbot", "delete", "--cert-name", domain_name, "--non-interactive"],
        ["sudo", "systemctl", "daemon-reload"],  # Important step after systemd file removal
    ]

    for command in commands:
        try:
            run_command(command)
        except Exception as e:
            print(f"There was an error while excecution : {e}")

    print(f"Odoo instance '{instance_name}' removed successfully!")

def run_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        sys.exit(1)


def main():
    instance_name = input("Enter the instance name to remove: ")
    domain_name = input("Enter the Domain name to remove: ")
    db_user = input("Enter the database user to remove: ")
    db_name = input("Enter the database name to remove: ")
    master_password = input("Enter the database master password: ")

    remove_instance(instance_name,domain_name)
    delete_postgres_user(db_user,master_password)

if __name__ == "__main__":
    main()



 
