import os
import smtplib
import time
import imaplib
import email
import requests
from datetime import datetime
from email.message import EmailMessage
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from googletrans import Translator

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Path to upload directory
UPLOADS_DIR = "uploads"
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'jpg', 'jpeg', 'png', 'docx', 'xlsx'}

# VirusTotal API Key
VIRUSTOTAL_API_KEY = "eb012464c1f37d720b66fc29e055515e5f9c1f930b815f9f33e003a366caf141"

# Ensure the uploads directory exists
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

translator = Translator()


@app.route('/')
def index():
    # Pass current time for scheduling in ISO format
    current_time = datetime.now().strftime('%Y-%m-%dT%H:%M')
    scan_notification = request.args.get('scan_notification', '')  # Get scan notification message from URL
    return render_template('index.html', current_time=current_time, scan_notification=scan_notification)


@app.route('/send_email', methods=['POST'])
def send_email_route():
    try:
        sender_email = request.form['sender_email']
        sender_password = request.form['sender_password']
        recipient_email = request.form['recipient_email']
        subject = request.form['subject']
        body = request.form['body']
        cc = request.form.get('cc', '')
        bcc = request.form.get('bcc', '')
        scheduled_time = request.form.get('scheduled_time')

        files = request.files.getlist('attachments')
        attachments = []
        scan_notification = ""

        for file in files:
            if file and allowed_file(file.filename):
                file_path = os.path.join(UPLOADS_DIR, file.filename)
                file.save(file_path)

                # Perform malware scan on the file using VirusTotal
                scan_result = scan_with_virustotal(file_path)
                if scan_result == "File is safe":
                    attachments.append(file_path)
                    scan_notification = f"File {file.filename} is safe to attach."
                else:
                    scan_notification = f"Malware detected in file {file.filename}. Email not sent."
                    flash(scan_notification, "error")
                    return redirect(url_for('index', scan_notification=scan_notification))

        # Construct the email message
        email_msg = create_email(sender_email, recipient_email, subject, body, cc, bcc, attachments)

        # Handle email scheduling
        if 'schedule_email' in request.form and scheduled_time:
            scheduled_time_obj = datetime.strptime(scheduled_time, "%Y-%m-%dT%H:%M")
            current_time = datetime.now()
            delay_in_seconds = (scheduled_time_obj - current_time).total_seconds()
            if delay_in_seconds > 0:
                flash(f"Email has been scheduled for {scheduled_time}.", "success")
                schedule_email(sender_email, sender_password, email_msg, delay_in_seconds)
            else:
                flash("Scheduled time must be in the future.", "error")
        else:
            send_email(sender_email, sender_password, email_msg)
            flash("Email sent successfully!", "success")

        return redirect(url_for('index', scan_notification=scan_notification))

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('index'))




@app.route('/check_grammar', methods=['POST'])
def check_grammar():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'status': 'error', 'message': 'No text provided'}), 400

    # Use LanguageTool API
    response = requests.post(
        'https://api.languagetoolplus.com/v2/check',
        data={'text': text, 'language': 'en-US'}
    )

    if response.status_code == 200:
        result = response.json()
        corrections = []

        for match in result.get('matches', []):
            original = text[match['offset']:match['offset'] + match['length']]
            replacements = match.get('replacements', [])
            corrected = [r['value'] for r in replacements]  # Extract corrected words
            if corrected:
                corrections.append({'original': original, 'corrected': corrected})

        return jsonify({'status': 'success', 'corrections': corrections})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to check grammar'}), 500




@app.route('/fetch_emails', methods=['POST'])
def fetch_emails():
    try:
        email_address = request.form['email_address']
        password = request.form['password']

        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_address, password)
        mail.select('inbox')

        # Fetch emails
        _, data = mail.search(None, 'ALL')
        email_ids = data[0].split()
        emails = []

        for email_id in email_ids[-10:]:  # Fetch the last 10 emails
            _, msg_data = mail.fetch(email_id, '(RFC822)')
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract email details
            email_subject = msg.get('Subject')
            email_from = msg.get('From')
            email_body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        email_body = part.get_payload(decode=True).decode()
                        break
            else:
                email_body = msg.get_payload(decode=True).decode()

            emails.append({
                'from': email_from,
                'subject': email_subject,
                'body': email_body
            })

        return jsonify({'status': 'success', 'emails': emails})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


def translate_text(text, target_lang):
    try:
        translated = translator.translate(text, dest=target_lang)
        return translated.text
    except Exception as e:
        return str(e)


def check_virustotal_report(file_id):
    """
    Retrieves the scan report for a file uploaded to VirusTotal and returns a result.
    """
    url = f"https://www.virustotal.com/api/v3/analyses/{file_id}"
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY
    }
    try:
        time.sleep(10)  # Allow some time for the scan to complete
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            stats = response.json().get('data', {}).get('attributes', {}).get('stats', {})
            malicious_count = stats.get('malicious', 0)
            if malicious_count == 0:
                return "File is safe"
            else:
                return f"File contains {malicious_count} malicious detections!"
        else:
            print(f"Error fetching VirusTotal report: {response.json()}")
            return "Error checking file"
    except Exception as e:
        print(f"Error during VirusTotal report check: {e}")
        return "Error during scan"

# Route to handle file upload and scanning
@app.route('/send_file', methods=['POST'])
def scan_with_virustotal(file_path):
    """
    Upload the file to VirusTotal for scanning and return the result.
    """
    url = "https://www.virustotal.com/api/v3/files"
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY
    }

    # Read the file and upload it to VirusTotal
    with open(file_path, 'rb') as file:
        files = {"file": file.read()}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        # Get the file ID and fetch the scan report
        file_id = response.json().get("data", {}).get("id")
        return check_virustotal_report(file_id)
    else:
        return "Error uploading file to VirusTotal."

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        message['Bcc'] = bcc

    # Add attachments
    if attachments:
        for file_path in attachments:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)
                message.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

    return message


def send_email(sender_email, sender_password, email_message):
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.send_message(email_message)


def schedule_email(sender_email, sender_password, email_message, delay_in_seconds):
    time.sleep(delay_in_seconds)
    send_email(sender_email, sender_password, email_message)


if __name__ == '__main__':
    app.run(debug=True)
