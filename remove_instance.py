import os
import subprocess
import sys



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
        run_command(command)    
    
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
    remove_instance(instance_name,domain_name) 

if __name__ == "__main__":
    main()

