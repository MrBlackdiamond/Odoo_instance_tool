import subprocess
import os

# Directory to start searching
search_directory = '/opt/odoo_echopx/addons/web/views/'

# Your custom logo path (update with the actual path or URL)
custom_logo_path = '/opt/odoo_echopx/addons/web/static/img/mycitybazaar-logo.png'

# File to store logs (optional)
log_file = 'replacement_log.txt'

# Function to run grep command to find files containing 'logo.png'
def find_logo_files(search_directory, search_term='favicon.ico'):
    try:
        # Run the grep command to find files that contain 'logo.png'
        result = subprocess.run(
            ['grep', '-rl', search_term, search_directory],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        files = result.stdout.splitlines()
        return files
    except Exception as e:
        print(f"Error running grep: {e}")
        return []

# Function to replace logo reference in a file
def replace_logo_reference(file_path, old_logo, new_logo):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if old_logo in content:
            content = content.replace(old_logo, new_logo)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            return True
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

# Function to replace logo in all files found by grep
def replace_in_files(files, old_logo, new_logo):
    replaced_files = 0
    for file_path in files:
        if replace_logo_reference(file_path, old_logo, new_logo):
            replaced_files += 1
            with open(log_file, 'a') as log:
                log.write(f"Replaced logo in: {file_path}\n")

    return replaced_files

# Old and new logo names (adjust as needed)
old_logo = 'favicon.ico'
new_logo = custom_logo_path

# Step 1: Find all files that reference the old logo
files_with_logo = find_logo_files(search_directory, old_logo)

# Step 2: Replace the logo in all found files
replaced_files_count = replace_in_files(files_with_logo, old_logo, new_logo)

print(f"Total files replaced: {replaced_files_count}")

