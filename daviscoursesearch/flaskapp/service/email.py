import sendgrid
from ...common import config

sg = sendgrid.SendGridClient(config.sendgrid_api_key)
def send(name, email, subject, html):
  message = sendgrid.Mail()
  message.add_to('{}'.format(email))
  message.set_subject(subject)
  message.set_html(html)
  message.set_from(config.from_header)
  status, msg = sg.send(message)