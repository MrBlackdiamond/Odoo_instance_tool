import os
import subprocess
import sys
import psycopg2
from psycopg2 import sql

def error_message(message):
    print(f"Error: {message}")
    sys.exit(1)

def run_command(command, shell=False):
    try:
        if shell:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                shell=True
            )
        elif command[0] == "sudo":
            command.pop(0)
            result = subprocess.run(
                ["sudo"] + command,
                check=True,
                capture_output=True,
                text=True
            )
        else:
            result = subprocess.run(command, check=True, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        error_message(f"Command failed with return code {e.returncode}\n{e.stderr}")

def get_user_input():
    if len(sys.argv) != 6:
        error_message("Usage: script.py <instance_name> <db_user> <db_password> <odoo_port> <domain_name>")

    instance_name = sys.argv[1]
    db_user = sys.argv[2]
    db_password = sys.argv[3]
    odoo_port = sys.argv[4]
    domain_name = sys.argv[5]

    if not all([instance_name, db_user, db_password, odoo_port, domain_name]):
        error_message("All fields are required. Please try again.")

    try:
        odoo_port = int(odoo_port)
    except ValueError:
        error_message("Port number must be an integer.")

    return instance_name, db_user, db_password, odoo_port, domain_name

def create_instance_directory(instance_name):
    print("Creating directory for the new Odoo instance...")
    run_command(["sudo", "mkdir", "-p", f"/opt/{instance_name}"])
    run_command(["sudo", "chown", "-R", "odoo:odoo", f"/opt/{instance_name}"])

def clone_odoo_source(instance_name):
    print("Cloning Odoo 18.0 source code...")
    run_command(["sudo", "git", "clone", "https://github.com/odoo/odoo.git", "-b", "18.0", "--single-branch", f"/opt/{instance_name}"])

def create_odoo_config(instance_name, db_user, db_password, odoo_port):
    print("Creating Odoo configuration file...")
    config_content = f"""[options]
proxy_mode = True
admin_passwd = admin@12345
db_host = localhost
db_port = 5432
db_user = {db_user}
db_password = {db_password}
xmlrpc_port = {odoo_port}
addons_path = /usr/lib/python3/dist-packages/odoo/addons
logfile = /var/log/odoo/{instance_name}.log"""

    run_command(["sudo", "mkdir", "-p", "/etc/odoo"])
    config_file = f"/etc/odoo/{instance_name}.conf"

    # Write configuration directly using tee
    run_command(f"echo '{config_content}' | sudo tee {config_file}", shell=True)
    run_command(["sudo", "chown", "odoo:odoo", config_file])
    run_command(["sudo", "chmod", "755", config_file])

def create_systemd_service(instance_name):
    print("Creating Systemd service file...")
    service_content = f"""[Unit]
Description=Odoo {instance_name} Instance
After=postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
ExecStart=/usr/bin/odoo --config /etc/odoo/{instance_name}.conf --logfile /var/log/odoo/{instance_name}.log
Restart=on-failure

[Install]
WantedBy=multi-user.target"""

    service_file = f"/etc/systemd/system/{instance_name}.service"
    run_command(f"echo '{service_content}' | sudo tee {service_file}", shell=True)
    run_command(["sudo", "systemctl", "daemon-reload"])
    run_command(["sudo", "systemctl", "enable", instance_name])
    run_command(["sudo", "systemctl", "start", instance_name])

    # Instead of direct systemctl calls:
    #run_command(['sudo', '/usr/local/bin/odoo-service-manager', f'odoo_{instance_name}', 'start'])
    #run_command(['sudo', '/usr/local/bin/odoo-service-manager', f'odoo_{instance_name}', 'enable'])
   # run_command(['sudo', '/usr/local/bin/odoo-service-manager', 'nginx', 'restart'])

def configure_nginx(domain_name, odoo_port):
    print("Configuring Nginx...")
    nginx_config = f"""server {{
    listen 80;
    server_name {domain_name};

    location / {{
        proxy_pass http://127.0.0.1:{odoo_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
    }}
}}"""

    nginx_file = f"/etc/nginx/sites-available/{domain_name}"
    run_command(f"echo '{nginx_config}' | sudo tee {nginx_file}", shell=True)
    run_command(["sudo", "ln", "-sf", nginx_file, "/etc/nginx/sites-enabled/"])
    run_command(["sudo", "certbot", "--nginx", "-d", domain_name])
    run_command(["sudo", "nginx", "-t"])
    run_command(["sudo", "systemctl", "restart", "nginx"])

def create_postgres_user(db_user, db_password):
    db_params = {
        "host": "localhost",
        "database": "postgres",
        "user": "postgres",
        "password": "admin@12345"
    }
    try:
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute(f"CREATE USER {db_user} WITH PASSWORD %s;", (db_password,))
        cur.execute(f"ALTER USER {db_user} WITH SUPERUSER;")
        cur.execute(f"ALTER USER {db_user} WITH CREATEDB;")

        print(f"User '{db_user}' created successfully!")

        cur.close()
        conn.close()
    except Exception as e:
        error_message(f"Database error: {str(e)}")

def main():
    instance_name, db_user, db_password, odoo_port, domain_name = get_user_input()

    try:
        create_instance_directory(instance_name)
    except Exception as e:
        print("Instance directory already exists, continuing...")
        pass

    try:
        create_postgres_user(db_user, db_password)
    except Exception as e:
        print("PostgreSQL user already exists, continuing...")
        pass

    try:
        clone_odoo_source(instance_name)
    except Exception as e:
        print("Odoo source already exists, continuing...")
        pass
    create_odoo_config(instance_name, db_user, db_password, odoo_port)
    create_systemd_service(instance_name)
    configure_nginx(domain_name, odoo_port)

    print(f"\nOdoo instance '{instance_name}' has been successfully created!")
    print(f"Access your Odoo instance at: http://{domain_name}")
    print(f"PostgreSQL User: {db_user}")
    print(f"Odoo Port: {odoo_port}")

if __name__ == "__main__":
    main()
