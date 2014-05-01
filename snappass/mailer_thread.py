import smtplib

from email.mime.text import MIMEText

from threading import Thread

class MailerThread(Thread):

  def __init__(self, app, url, email):
    Thread.__init__(self)
    self.url = url
    self.email = email
    self.app = app

  def run(self):
    errors = []
    try:
      if self.email and self.url:
        SERVER = self.app.smtp_server

        FROM = self.app.from_email
        TO = [self.email]

        SUBJECT = "SnapPass - Someone has shared a password with you"

        TEXT = self.url

        message = 'Subject: %s\n\n%s' % (SUBJECT, TEXT)

        server = smtplib.SMTP(SERVER)
        server.sendmail(FROM, TO, message)
        server.quit()

    except Exception, e:
      return e
