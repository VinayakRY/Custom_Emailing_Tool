# # Define the uploads directory
# UPLOADS_DIR = "uploads"

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import smtplib
from email.message import EmailMessage
import time
import datetime
from datetime import datetime
import base64
import urllib.request
import urllib.parse
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # for flashing messages

# Path to store drafts and bin (local storage simulation)
DRAFTS_DIR = "drafts"
BIN_DIR = "bin"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx'}

# VirusTotal API URL and your API key (replace with your actual API key)
VIRUSTOTAL_API_KEY = 'eb012464c1f37d720b66fc29e055515e5f9c1f930b815f9f33e003a366caf141'
VIRUSTOTAL_URL = 'https://www.virustotal.com/api/v3/files/'

@app.route('/')
def index():
    return render_template('index.html')

# Define the uploads directory
UPLOADS_DIR = "uploads"

# Ensure that the uploads directory exists
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Function to handle file uploads
@app.route('/send_email', methods=['POST'])
def send_email_route():
    sender_email = request.form['sender_email']
    sender_password = request.form['sender_password']
    recipient_email = request.form['recipient_email']
    subject = request.form['subject']
    body = request.form['body']
    cc = request.form['cc']
    bcc = request.form['bcc']
    scheduled_time = request.form['scheduled_time']
    
    # Handle file uploads
    files = request.files.getlist('attachments')
    attachments = []
    for file in files:
        if file and allowed_file(file.filename):
            file_path = os.path.join(UPLOADS_DIR, file.filename)
            file.save(file_path)
            attachments.append(file_path)

    # Calculate the delay in seconds if scheduling is enabled
    if 'schedule_email' in request.form and scheduled_time:
        scheduled_time_obj = datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M")
        current_time = datetime.now()
        delay_in_seconds = (scheduled_time_obj - current_time).total_seconds()
        if delay_in_seconds > 0:
            email = create_email(sender_email, recipient_email, subject, body, cc, bcc, attachments)
            schedule_email(sender_email, sender_password, email, delay_in_seconds)
            flash(f"Email has been scheduled for {scheduled_time}.", "success")
        else:
            flash("Selected time is in the past. Please select a future time.", "error")
    else:
        email = create_email(sender_email, recipient_email, subject, body, cc, bcc, attachments)
        send_email(sender_email, sender_password, email)
        flash("Email has been sent successfully!", "success")
    
    return redirect(url_for('index'))


# Function to validate file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to create an email
def create_email(sender_email, recipient_email, subject, body, cc=None, bcc=None, attachments=None):
    message = EmailMessage()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    message.set_content(body)

    # Add CC and BCC
    if cc:
        message['Cc'] = cc
    if bcc:
        recipient_email += f",{bcc}"

    # Add attachments if any
    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                message.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
            except FileNotFoundError:
                print(f"Attachment {file_path} not found. Skipping.")

    return message

# Function to send email
def send_email(sender_email, sender_password, email_message):
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, sender_password)
            server.send_message(email_message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

# Function to check if the email is OTP or junk
def is_junk_email(subject, body):
    junk_keywords = ['OTP', 'Verification', 'Promo', 'One-time password', 'Discount']
    if any(keyword in subject for keyword in junk_keywords) or any(keyword in body for keyword in junk_keywords):
        return True
    return False

# Function to schedule email
def schedule_email(sender_email, sender_password, email_message, delay_in_seconds):
    print(f"Scheduling email to be sent in {delay_in_seconds} seconds...")
    time.sleep(delay_in_seconds)
    print(f"Time to send the email: {datetime.datetime.now()}")
    send_email(sender_email, sender_password, email_message)

# Main program
if __name__ == '__main__':
    app.run(debug=True)
