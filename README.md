# Custom Emailing Tool

This repository contains the **Custom Emailing Tool**, a Python-based project designed to simplify sending personalized emails to multiple recipients. It's ideal for automating bulk email tasks while maintaining a personal touch.

---

## Features
- **Personalized Emails**: Send tailored emails to each recipient using dynamic placeholders.
- **CSV Integration**: Load recipient data directly from a CSV file.
- **HTML Support**: Compose rich-text emails using HTML.
- **Error Handling**: Robust handling of email delivery failures.
- **Log Management**: Keep track of sent emails with detailed logs.

---

## Prerequisites
Ensure you have the following installed:
- Python 3.8+
- An email account (e.g., Gmail, Outlook) with SMTP access enabled.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/VinayakRY/Custom_Emailing_Tool.git
   cd Custom_Emailing_Tool
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

1. **Setup SMTP Configuration:**
   - Edit the `config.json` file to include your SMTP server, email address, and password.
   ```json
   {
       "smtp_server": "smtp.gmail.com",
       "port": 587,
       "email": "your_email@gmail.com",
       "password": "your_password"
   }
   ```

2. **Prepare the Recipient List:**
   - Create a CSV file with recipient details. Example format:
     ```csv
     name,email,message
     John,john@example.com,"Hello John, hope you're doing well!"
     Jane,jane@example.com,"Hi Jane, here's your personalized message."
     ```

3. **Run the Script:**
   ```bash
   python send_email.py
   ```

4. **Monitor Logs:**
   - Sent email logs are stored in `logs/sent_emails.log`.

---

## Configuration

- **Email Templates:**
  Customize the email content in the `templates/email_template.html` file for consistent branding and design.

- **Environment Variables:**
  For better security, you can set your email credentials as environment variables:
  ```bash
  export EMAIL_USER="your_email@gmail.com"
  export EMAIL_PASS="your_password"
  ```

---

## Roadmap
- [ ] Add support for email attachments.
- [ ] Implement OAuth2 for secure authentication.
- [ ] Include an interactive GUI for non-technical users.

---

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-name`.
3. Commit your changes: `git commit -m 'Add some feature'`.
4. Push to the branch: `git push origin feature-name`.
5. Open a pull request.

---

## License
This project is licensed under the MIT License.

---

## Contact
For questions or support, feel free to contact **Vinayak Rathore**:
- Email: [socialcontact121@gmail.com](mailto:socialcontact121@gmail.com)
- LinkedIn: [Vinayak Rathore](https://www.linkedin.com/in/vinayak-rathore)

---

## Acknowledgments
- Inspired by automation enthusiasts.
- Thanks to the Python community for their incredible libraries.

---

Happy Emailing!
