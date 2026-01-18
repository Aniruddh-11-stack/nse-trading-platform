from dotenv import load_dotenv
import os
import smtplib

load_dotenv()

user = os.getenv("EMAIL_USER")
password = os.getenv("EMAIL_PASS")
server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
port = int(os.getenv("SMTP_PORT", 587))

print(f"Testing SMTP connection to {server}:{port} for {user}")

try:
    s = smtplib.SMTP(server, port)
    s.starttls()
    s.login(user, password)
    print("SMTP Login Successful!")
    s.quit()
except Exception as e:
    print(f"SMTP Login Failed: {e}")
