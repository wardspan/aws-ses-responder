#!/usr/bin/env python
# encoding: utf-8

from cortexutils.responder import Responder
import smtplib
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class Mailer(Responder):
    def __init__(self):
        Responder.__init__(self)
        self.smtp_host = self.get_param('config.smtp_host', 'localhost')
        self.smtp_port = self.get_param('config.smtp_port', '25')
        self.mail_from = self.get_param('config.from', None, 'Missing sender email address')
        self.sender_name = self.get_param('config.sender_name', 'bubba@bubba.com')
        self.smtp_username = self.get_param('config.smtp_username', None, 'Missing SMTP username')
        self.smtp_password = self.get_param('config.smtp_password', None, 'Missing AWS SES password')

    def run(self):
        Responder.run(self)

        title = self.get_param('data.title', None, 'title is missing')
        title = title.encode('utf-8')

        description = self.get_param('data.description', None, 'description is missing')
        description = description.encode('utf-8')

        mail_to = None
        if self.data_type == 'thehive:case':
            # Search recipient address in tags
            tags = self.get_param('data.tags', None, 'recipient address not found in tags')
            mail_tags = [t[5:] for t in tags if t.startswith('mail:')]
            if mail_tags:
                mail_to = mail_tags.pop()
            else:
                self.error('recipient address not found in observables')
        elif self.data_type == 'thehive:alert':
            # Search recipient address in artifacts
            artifacts = self.get_param('data.artifacts', None, 'recipient address not found in observables')
            mail_artifacts = [a['data'] for a in artifacts if a.get('dataType') == 'mail' and 'data' in a]
            if mail_artifacts:
                mail_to = mail_artifacts.pop()
            else:
                self.error('recipient address not found in observables')
        else:
            self.error('Invalid dataType')

        msg = MIMEMultipart()
        msg['Subject'] = title
        msg['From'] = email.utils.formataddr((self.sender_name, self.mail_from))
        msg['To'] = mail_to
        msg['Reply-To'] = 'mss-soc@obsglobal.com'
        msg.attach(MIMEText(description, 'plain'))

        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.smtp_username, self.smtp_password)
        server.sendmail(self.mail_from, [mail_to], msg.as_string())
        server.close()
        self.report({'message': 'message sent'})

    def operations(self, raw):
        return [self.build_operation('AddTagToCase', tag='mail sent')]


if __name__ == '__main__':
    Mailer().run()
