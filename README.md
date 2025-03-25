# Odoo 18 Instance Deployment Tool

This script automates the deployment of a new Odoo 18 instance on a Linux server. It sets up the necessary configurations, PostgreSQL database, Odoo source code, systemd service, and Nginx reverse proxy with SSL support.

## Prerequisites
Ensure your system has the following installed:
- Python 3
- PostgreSQL
- Git
- Nginx
- Certbot (for SSL)
- Required Python libraries: `psycopg2`

You can install the required packages using:
```sh
sudo apt update && sudo apt install -y python3 python3-pip postgresql git nginx certbot python3-certbot-nginx
pip install psycopg2
```

## Usage
Run the script with:
```sh
python3 new_instance_tool.py
```

The script will prompt you for:
- **Instance Name** (e.g., `odoo_hms`)
- **Database User**
- **Database Password**
- **Odoo Port** (e.g., `8070`)
- **Domain Name** (e.g., `hms.erpbangalore.org`)

## Features
- **Creates necessary directories** under `/opt/`
- **Creates a PostgreSQL user** with required privileges
- **Clones Odoo 18 source code** into the instance directory
- **Generates an Odoo configuration file**
- **Creates a systemd service** to manage the Odoo instance
- **Configures Nginx as a reverse proxy**
- **Enables SSL using Certbot**

## Logs & Management
- Logs are stored in `/var/log/odoo/`
- Start/stop the instance using:
  ```sh
  sudo systemctl start <instance_name>
  sudo systemctl stop <instance_name>
  ```
- Check logs using:
  ```sh
  sudo journalctl -u <instance_name> --no-pager
  ```

## Notes
- Ensure PostgreSQL is running before executing the script.
- Nginx configuration is applied under `/etc/nginx/sites-available/`.
- SSL is enabled using Certbot; ensure your domain is pointed to the server.

## Troubleshooting
If you encounter issues:
1. Check PostgreSQL logs: `sudo systemctl status postgresql`
2. Verify Nginx configuration: `sudo nginx -t`
3. Check Odoo logs: `sudo journalctl -u <instance_name> --no-pager`

## License
This script is open-source and available for modification.

