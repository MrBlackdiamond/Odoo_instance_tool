import os
import subprocess
import sys

# Function to print an error message and exit the program
def error_message(message):
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)

# Function to run a command in the shell
def run_command(command, shell=False, env=None):
    try:
        subprocess.run(command, check=True, shell=shell, env=env)
    except subprocess.CalledProcessError as e:
        error_message(f"Command '{' '.join(e.cmd)}' failed with return code {e.returncode}")

# Function to get user input for creating a new Odoo instance
def get_user_input():
    instance_name = input("Enter the name of the new Odoo instance (e.g., odoo_hms): ")
    db_user = input("Enter the user for database: ")  # Use the existing 'odoo' user
    db_password = input("Enter the PostgreSQL password for the db_user: ")
    odoo_port = input("Enter the Odoo port number (e.g., 8070): ")
    domain_name = input("Enter the domain name or IP address (e.g., hms.erpbangalore.org): ")

    if not all([instance_name, db_user, db_password, odoo_port, domain_name]):
        error_message("All fields are required. Please try again.")

    try:
        odoo_port = int(odoo_port)  # Validate port number
    except ValueError:
        error_message("Port number must be an integer.")

    return instance_name, db_user, db_password, odoo_port, domain_name

# Function to create a new directory for the Odoo instance
def create_instance_directory(instance_name):
    print("Creating directory for the new Odoo instance...")
    run_command(["sudo", "mkdir", "-p", f"/opt/{instance_name}"])
    run_command(["sudo", "chown", "-R", "odoo:odoo", f"/opt/{instance_name}"])

# Function to clone the Odoo source code
def clone_odoo_source(instance_name):
    print("Cloning Odoo 18.0 source code...")
    run_command(["sudo", "git", "clone", "https://github.com/odoo/odoo.git", "-b", "18.0", "--single-branch", f"/opt/{instance_name}"])

# Function to create the Odoo configuration file
def create_odoo_config(instance_name, db_user, db_password, odoo_port):
    print("Creating Odoo configuration file...")
    config_content = f"""
[options]
proxy_mode = True
admin_passwd = admin@12345
db_host = localhost
db_port = 5432
db_user = {db_user}
db_password = {db_password}
xmlrpc_port = {odoo_port}
addons_path = /usr/lib/python3/dist-packages/odoo/addons
logfile = /var/log/odoo/{instance_name}.log
"""
    with open(f"/etc/odoo/{instance_name}.conf", "w") as f:
        f.write(config_content.strip())
    run_command(["sudo", "chown", "odoo:odoo", f"/etc/odoo/{instance_name}.conf"])
    run_command(["sudo", "chmod", "755", f"/etc/odoo/{instance_name}.conf"])

# Function to create a Systemd service for the Odoo instance
def create_systemd_service(instance_name):
    print("Creating Systemd service file...")
    service_content = f"""
[Unit]
Description=Odoo {instance_name} Instance
After=postgresql.service

[Service]
Type=simple
User=odoo
Group=odoo
ExecStart=/usr/bin/odoo --config /etc/odoo/{instance_name}.conf --logfile /var/log/odoo/{instance_name}.log
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    with open(f"/etc/systemd/system/{instance_name}.service", "w") as f:
        f.write(service_content.strip())
    run_command(["sudo", "systemctl", "daemon-reload"])
    run_command(["sudo", "systemctl", "enable", instance_name])
    run_command(["sudo", "systemctl", "start", instance_name])

# Function to configure Nginx as a reverse proxy
def configure_nginx(domain_name, odoo_port):
    print("Configuring Nginx...")
    nginx_config = f"""
server {{
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
}}
"""
    with open(f"/etc/nginx/sites-available/{domain_name}", "w") as f:
        f.write(nginx_config.strip())
    run_command(["sudo", "ln", "-s", f"/etc/nginx/sites-available/{domain_name}", "/etc/nginx/sites-enabled/"])
    run_command(["sudo","certbot","--nginx","-d",domain_name])
    run_command(["sudo", "nginx", "-t"])
    run_command(["sudo", "systemctl", "restart", "nginx"])

# Main function
def main():
    # Get user inputs
    instance_name, db_user, db_password, odoo_port, domain_name = get_user_input()

    # Step 1: Create instance directory
    create_instance_directory(instance_name)

    # Step 2: Clone Odoo source code
    clone_odoo_source(instance_name)

    # Step 3: Create Odoo configuration file
    create_odoo_config(instance_name, db_user, db_password, odoo_port)

    # Step 4: Create Systemd service file
    create_systemd_service(instance_name)

    # Step 5: Configure Nginx
    configure_nginx(domain_name, odoo_port)

    # Final message
    print(f"\nOdoo instance '{instance_name}' has been successfully created!")
    print(f"Access your Odoo instance at: http://{domain_name}")
    print(f"PostgreSQL User: {db_user}")
    print(f"Odoo Port: {odoo_port}")

if __name__ == "__main__":
    main()
