import os
import subprocess
import sys
import psycopg2
from psycopg2 import sql
import pwd
import requests
import json

global site_config
site_config = {}

def error_message(message):
    print(f"Error: {message}")
    sys.exit(1)


def get_data(key,default=None):
    global site_config
    if key in site_config:
        return site_config[key]
    else:
        return default

def load_config():
    global site_config
    path = "/var/www/env.json"
    try:
        with open(path, 'r') as file:
            site_config = json.load(file)
    except Exception as e:
        error_message(f"Failed to load configuration: {str(e)}")


def run_command(command, shell=False):
    try:
        # Get current username
        current_user = pwd.getpwuid(os.getuid()).pw_name
        
        # Allow root user as well
        if current_user not in ['odoo', 'www-data', 'root']:
            error_message(f"Script must be run as 'root', 'odoo' or 'www-data' user. Current user: {current_user}")

        if shell:
            # If it's a shell command, pass it as is
            print(f"Executing command: {command}")  # Add command logging
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        else:
            # If it's a list command and shell=False, join it for execution
            cmd_str = ' '.join(command)
            print(f"Executing command: {cmd_str}")  # Add command logging
            result = subprocess.run(cmd_str, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.stdout:
            print(result.stdout.strip())
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command output: {e.stdout}")  # Add stdout
        print(f"Command error: {e.stderr}")   # Add stderr
        error_message(f"Command failed with return code {e.returncode}\nCommand: {command}\nError: {e.stderr}")

def get_last_port():
    filename = "/var/www/port.txt"
    try:
        with open(filename, 'r') as file:
            # Filter out empty lines and whitespace
            lines = [line.strip() for line in file.readlines() if line.strip()]
            print(f"Debug: Read {len(lines)} lines from port.txt")
            
            if not lines:
                print("Debug: No valid lines found in file")
                return None
                
            last_line = lines[-1]
            print(f"Debug: Last line read: '{last_line}'")
            
            # Additional validation
            if not last_line.isdigit():
                print(f"Debug: Last line is not a valid number: '{last_line}'")
                return None
                
            return int(last_line)
            
    except FileNotFoundError:
        print(f"Debug: File {filename} not found")
        return None
    except ValueError as e:
        print(f"Debug: Value error when parsing port: {e}")
        return None
    except Exception as e:
        print(f"Debug: Unexpected error: {e}")
        return None

def assign_new_port():
    filename = "/var/www/port.txt"
    current_port = get_last_port()
    
    if current_port is None:
        # Initialize with default port if no valid port is found
        current_port = 8069  # Default Odoo port
        print(f"Debug: Using default port: {current_port}")
    
    new_port = current_port + 1
    
    # Append the new port to file
    try:
        # Ensure we're writing a clean number without extra spaces or newlines
        run_command(f"echo -n {new_port} | sudo tee -a {filename}", shell=True)
        # Add a newline after the number
        run_command(f"echo '' | sudo tee -a {filename}", shell=True)
        return new_port
    except Exception as e:
        error_message(f"Failed to write new port: {str(e)}")
def get_user_input():
    if len(sys.argv) != 6:
        error_message("Usage: script.py <master_password> <instance_name> <db_user> <db_password> <domain_name>")

    master_password = sys.argv[1]
    instance_name = sys.argv[2]
    db_user = sys.argv[3]
    db_password = sys.argv[4]
    domain_name = sys.argv[5]

    odoo_port = assign_new_port()
    instance_name = "odoo_"+instance_name 

    if not all([master_password,instance_name, db_user, db_password, odoo_port, domain_name]):
        error_message("All fields are required. Please try again.")

    try:
        odoo_port = int(odoo_port)
    except ValueError:
        error_message("Port number must be an integer.")

    return master_password, instance_name, db_user, db_password, odoo_port, domain_name

def create_instance_directory(instance_name):
    print("Creating directory for the new Odoo instance...")
    try:
        run_command(f"sudo mkdir -p /opt/{instance_name}", shell=True)
        run_command(f"sudo chown -R odoo:odoo /opt/{instance_name}", shell=True)
        print(f"Directory /opt/{instance_name} created successfully")
    except Exception as e:
        error_message(f"Failed to create instance directory: {str(e)}")
    
    

def clone_odoo_source(instance_name):
    print("Cloning Odoo 18.0 source code...")
    #run_command(["sudo", "git", "clone", "https://github.com/odoo/odoo.git", "-b", "18.0", "--single-branch", f"/opt/{instance_name}"])

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

    try:
        # Modified commands to use shell=True consistently
        print("trying to create a config file...")
        run_command("sudo mkdir -p /etc/odoo", shell=True)
        config_file = f"/etc/odoo/{instance_name}.conf"

        # Write configuration using tee
        run_command(f"echo '{config_content}' | sudo tee {config_file}", shell=True)
        run_command(f"sudo chown odoo:odoo {config_file}", shell=True)
        run_command(f"sudo chmod 755 {config_file}", shell=True)
        print("created config file!...\n")
    except Exception as e:
        error_message(f"Failed to create config file: {str(e)}")


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

    try:
        service_file = f"/etc/systemd/system/{instance_name}.service"
        
        # Use tee command to write the service file with sudo
        run_command(f"echo '{service_content}' | sudo tee {service_file}", shell=True)
        
        # Set proper permissions
        run_command(f"sudo chmod 644 {service_file}", shell=True)
        
        # Reload and start service
        run_command("sudo systemctl daemon-reload", shell=True)
        run_command(f"sudo systemctl enable {instance_name}", shell=True)
        run_command(f"sudo systemctl start {instance_name}", shell=True)
        print("created service file")
    except Exception as e:
        error_message(f"Failed to create/start service: {str(e)}")

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

    try:
        # Create nginx config
        print("trying to create nginx file")
        nginx_file = f"/etc/nginx/sites-available/{domain_name}"
        run_command(f"echo '{nginx_config}' | sudo tee {nginx_file}", shell=True)
        run_command(["sudo","ln", "-s", nginx_file, "/etc/nginx/sites-enabled/"])
        print(f"Created a sim-link for the {str(nginx_config)}")
        run_command("sudo nginx -t", shell=True)
        print("Attempting to obtain SSL certificate...")
        try:
            run_command(f"sudo certbot --nginx --non-interactive --agree-tos --email admin@{domain_name} -d {domain_name}", shell=True)
            print("SSL certificate obtained successfully!")
        except Exception as ssl_error:
            print(f"Warning: SSL certificate generation failed: {str(ssl_error)}")
            print("You can manually obtain the SSL certificate later using:")
            print(f"sudo certbot --nginx -d {domain_name}")
            run_command("sudo systemctl restart nginx", shell=True)
    except Exception as e:
        error_message(f"Failed to configure nginx: {str(e)}")

def create_postgres_user(db_user, db_password,master_password):
    db_params = {
        "host": get_data('host'),
        "database": get_data('database'),
        "user": get_data('user'),
        "password": master_password
    }
    try:
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cur = conn.cursor()

        # First check if user exists
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (db_user,))
        user_exists = cur.fetchone() is not None

        if user_exists:
            print(f"User '{db_user}' already exists, updating privileges...")
            # Update privileges for existing user
            cur.execute(f"ALTER USER {db_user} WITH PASSWORD %s;", (db_password,))
            cur.execute(f"ALTER USER {db_user} WITH SUPERUSER;")
            cur.execute(f"ALTER USER {db_user} WITH CREATEDB;")
        else:
            # Create new user
            cur.execute(f"CREATE USER {db_user} WITH PASSWORD %s;", (db_password,))
            cur.execute(f"ALTER USER {db_user} WITH SUPERUSER;")
            cur.execute(f"ALTER USER {db_user} WITH CREATEDB;")
            print(f"User '{db_user}' created successfully!")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Database warning: {str(e)}")
        print("Continuing with existing user...")
def trim_string_before_character(text, character):
        index = text.find(character)
        if index != -1:
            return text[:index]
        return text

def create_dns_record(domain):
    url = "https://developers.hostinger.com/api/dns/v1/zones/erpbangalore.org"
    subdomain = trim_string_before_character(domain, ".")

    payload = json.dumps({
    "zone": [
        {
        "name": subdomain,
        "type": "CNAME",
        "records": [
            {
            "content": "erpbangalore.org"
            }
        ],
        "ttl": 14400
        }
    ],
    "overwrite": False
    })
    headers = {
        'Authorization': 'Bearer '+get_data('bearer_token'),
        'Content-Type': 'application/json',
        'Content-Length': str(len(payload)),  # Automatically calculated in Postman, but here you can add it manually
        'Host': 'developers.hostinger.com',
        'User-Agent': 'PostmanRuntime/7.43.3',
        'Accept': '*/*',
    }

    # response = requests.request("PUT", url, headers=headers, data=payload)
    response = requests.put(url, headers=headers, data=payload)
    return True

def main():
    load_config()
    master_password, instance_name, db_user, db_password, odoo_port, domain_name = get_user_input()
    db_master = get_data('master_password')
    if master_password != db_master:
        error_message("Error: Invalid master password")
    try:
        create_instance_directory(instance_name)
    except Exception as e:
        print(f"Unable to create a directory {str(e)}")

    try:
        create_systemd_service(instance_name)
    except Exception as e:
        print(f"Odoo systemd service setup had issues, check logs... {str(e)}")
        pass

    try:
        create_postgres_user(db_user, db_password,master_password)
    except Exception as e:
        print(f"Unable to Create PostgreSQL user -> {str(e)}")
        pass

    try:
        clone_odoo_source(instance_name)
    except Exception as e:
        print(f"Unable to clone into the repository -> {str(e)}")
        pass
    try:
        create_odoo_config(instance_name, db_user, db_password, odoo_port)
    except Exception as e:
        print(f"Unable to create config file -> {str(e)}")
        pass
    
    try:
        create_systemd_service(instance_name)
    except Exception as e:
        print(f"Unable to create systemd file -> {str(e)}")
        pass
    try:
        configure_nginx(domain_name, odoo_port)
    except Exception as e :
        print(f"Unabel to create nginx file {str(e)}")
    try:
        create_dns_record(domain_name)
    except Exception as e:
        print("Unable to create a DNS record")

    print(f"\nOdoo instance '{instance_name}' has been successfully created!")
    print(f"Access your Odoo instance at: https://{domain_name}")
    print(f"PostgreSQL User: {db_user}")
    print(f"Odoo Port: {odoo_port}")



if __name__ == "__main__":
    main()