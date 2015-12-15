from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from subprocess import Popen, PIPE


def send_mail(from_, to, subject, content, attachments=[]):
    if attachments:
        msg = MIMEMultipart(content)
    else:
        msg = MIMEText(content)
    msg["From"] = from_
    msg["To"] = to
    msg["Subject"] = subject
    msg.preamble = content
    for contenttype, name, data in attachments:
        maintype, subtype = contenttype.split("/")
        att = MIMEBase(maintype, subtype)
        att.set_payload(data)
        encoders.encode_base64(att)
        att.add_header('Content-Disposition', 'attachment', filename=name)
        msg.attach(att)
    res = msg.as_string()
    try:
        p = Popen(["/usr/bin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(res)
    except OSError:
        print res

