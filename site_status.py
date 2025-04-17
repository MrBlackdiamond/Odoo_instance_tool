import requests
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from concurrent.futures import ThreadPoolExecutor
import time
import os

os.environ['PATH'] = '/usr/bin:/bin:/usr/sbin:/sbin'

# Setup logging
logging.basicConfig(filename='/root/tools/website_monitoring.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class EmailServer:
    def __init__(self):
        self.sender_email = "googleteam2@echopx.com"
        self.receiver_email = "rajurebel199@gmail.com"
        self.password = "qalx zbfb raci umkj"
        self.subject = "Website Monitoring Report"

    def set_body(self, body):
        self.body = body

    def get_body(self):
        return self.body

    def send_email(self):
        self.msg = MIMEMultipart()
        self.msg['From'] = self.sender_email
        self.msg['To'] = self.receiver_email
        self.msg['Subject'] = self.subject
        self.msg.attach(MIMEText(self.get_body(), 'html'))

        try:
            # Connect to the Gmail SMTP server
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()  # Secure the connection using TLS
            server.login(self.sender_email, self.password)
            server.sendmail(self.sender_email, self.receiver_email, self.msg.as_string())
            server.quit()
            logging.info(f"Email sent successfully to {self.receiver_email}")
        except Exception as e:
            logging.error(f"Error sending email: {e}")


class WebsiteStatusChecker:
    def __init__(self):
        self.status = []
        self.timeout = 10  # Timeout in seconds for HTTP requests
        self.retry_attempts = 3  # Retry attempts for failed requests
        self.table_started = False  # Track if the table has started

    def set_urls(self, urls):
        self.urls = urls

    def get_status_code(self, url):
        try:
            response = requests.get(url, timeout=self.timeout, verify=True)
            return response.status_code
        except requests.exceptions.RequestException as e:
            logging.error(f"Error with website {url}: {e}")
            return None  # Return None if there's an error

    def check_website_status(self):
        logging.info("Cron job started at: " + str(time.time()))
        email_body = ""  # Initialize an empty string to accumulate results
        send_email = False  # Flag to determine if we should send an email

        # Use ThreadPoolExecutor to check the websites concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(self.check_url_status, self.urls))

        # Collect the results and only send an email if the status code is not 200
        for result in results:
            if result:  # Only include errors or warnings
                email_body += result + "\n"
                send_email = True  # Set the flag to send email if there's an issue

        # If we have any errors or status codes not equal to 200, send the email
        if send_email:
            email = EmailServer()
            email.set_body(email_body)
            email.send_email()

    def check_url_status(self, url):
        logging.info(f"Starting site status check for: {url}")
        status = self.get_status_code(url)
        logging.info(f"Checked URL: {url} with status code: {status}")

        email_body = ""

        # Start the HTML table once
        if not self.table_started:
            self.table_started = True  # Mark that the table has started
            email_body += """
            <html>
            <head>
                <style>
                    table {
                        width: 100%;
                        border-collapse: collapse;
                        margin-bottom: 20px;
                    }
                    table, th, td {
                        border: 1px solid #ddd;
                    }
                    th, td {
                        padding: 12px 15px;
                        text-align: left;
                        vertical-align: top;
                    }
                    th {
                        background-color: #4CAF50;
                        color: white;
                    }
                    tr:nth-child(even) {
                        background-color: #f2f2f2;
                    }
                    .status-success {
                        background-color: #d4edda;
                        color: #155724;
                    }
                    .status-error {
                        background-color: #f8d7da;
                        color: #721c24;
                    }
                    .status-warning {
                        background-color: #fff3cd;
                        color: #856404;
                    }
                    .status-header {
                        font-size: 18px;
                        font-weight: bold;
                        margin-bottom: 10px;
                    }
                </style>
            </head>
            <body>
                <h2>Website Status Report</h2>
                <p class="status-header">Below is the status report for your monitored websites:</p>
                <table>
                    <tr>
                        <th>URL</th>
                        <th>Status</th>
                        <th>Status Code</th>
                        <th>Description</th>
                    </tr>
            """

        # Check the status and add the corresponding row in the table
        if status is not None:
            if status == 200:
                return ""  # No need to include this website in the email (it's working fine)
            elif status == 404:
                email_body += f"""
                <tr class="status-error">
                    <td>{url}</td>
                    <td>❌ Broken</td>
                    <td>{status}</td>
                    <td>The URL '{url}' is broken or the page does not exist.</td>
                </tr>
                """
            elif status == 500:
                email_body += f"""
                <tr class="status-error">
                    <td>{url}</td>
                    <td>❌ Internal Server Error</td>
                    <td>{status}</td>
                    <td>The URL '{url}' encountered an internal issue. Please check the server logs.</td>
                </tr>
                """
            elif status == 502:
                email_body += f"""
                <tr class="status-error">
                    <td>{url}</td>
                    <td>❌ Gateway Issue</td>
                    <td>{status}</td>
                    <td>The URL '{url}' has a gateway issue. Please ensure the web server is running and active.</td>
                </tr>
                """
            elif status == 503:
                email_body += f"""
                <tr class="status-error">
                    <td>{url}</td>
                    <td>❌ Service Unavailable</td>
                    <td>{status}</td>
                    <td>The URL '{url}' has a service unavailable issue. The server might be undergoing maintenance or overloaded.</td>
                </tr>
                """
            else:
                email_body += f"""
                <tr class="status-warning">
                    <td>{url}</td>
                    <td>⚠️ Issue</td>
                    <td>{status}</td>
                    <td>The URL '{url}' has an unknown issue. Further investigation needed.</td>
                </tr>
                """
        else:
            email_body += f"""
            <tr class="status-error">
                <td>{url}</td>
                <td>🚨 Error</td>
                <td>Unknown</td>
                <td>Unable to fetch status code after the attempt. Please check the URL or network connectivity.</td>
            </tr>
            """

        # Ensure the email body gets properly closed with the table and HTML tags
        email_body += """
            </table>
        </body>
        </html>
        """
        
        return email_body

    def read_urls_from_file(self, filename):
        """
        This function will read URLs from a file and return them as a list.
        """
        urls = []
        try:
            with open(filename, 'r') as file:
                urls = file.readlines()
                urls = [url.strip() for url in urls if url.strip()]  # Remove any extra whitespace
            logging.info(f"Read {len(urls)} URLs from the file.")
        except Exception as e:
            logging.error(f"Error reading the URL file: {e}")
        return urls

# Example usage
site = WebsiteStatusChecker()

# Read URLs from a file called 'text.txt'
urls_from_file = site.read_urls_from_file('/root/tools/text.txt')

# Set the URLs from the file (pass the list as a single argument)
site.set_urls(urls_from_file)

# Check the website status
site.check_website_status()
