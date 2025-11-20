import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configure aqui o e-mail e senha do remetente (use app password do Gmail ou SMTP seguro)
EMAIL_REMETENTE = 'comicsultimate@gmail.com'
SENHA_REMETENTE = 'ultimatecomics'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

def enviar_email(destinatario, assunto, corpo):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_REMETENTE, SENHA_REMETENTE)
        server.sendmail(EMAIL_REMETENTE, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f'Erro ao enviar e-mail: {e}')
        return False
