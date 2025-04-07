"""
Create mail and send
"""

from typing import Union
from os.path import exists as path_exists
from pathlib import Path
from os import getenv as os_getenv
import smtplib
import ssl
import argparse
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

from hashiget import get_vault_secret


class SENDMAILError(Exception):
    pass


class ARGSError(Exception):
    pass


def create_mail(
    sender_email: str,
    recipient_email: str,
    subject: str,
    body: str,
    attachment: Union[MIMEBase, None] = None,
) -> MIMEMultipart:
    message: MIMEMultipart = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))
    if attachment:
        message.attach(attachment)

    return message


def sendmail(
    login: str,
    password: str,
    message: MIMEMultipart,
    smtp_server: str,
    port: int = 587,
) -> None:
    context: ssl.SSLContext = ssl.create_default_context()
    try:
        with smtplib.SMTP(host=smtp_server, port=port, timeout=30) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(login, password)
            server.send_message(message)
    except Exception as e:
        raise SENDMAILError(f"An Error occured while sending the Mail: {e}")


if __name__ == "__main__":
    _login: str
    _password: str
    _body: str
    _attachment: Union[MIMEBase, None] = None

    parser = argparse.ArgumentParser(
        description="Simple Python Program that sends mails over an sasl service"
    )

    parser.add_argument(
        "-S", "--smtp_server", help="url to the smtp server", required=True, type=str
    )

    parser.add_argument(
        "-f", "--from_mail", help="Sender E-Mail", required=True, type=str
    )

    parser.add_argument(
        "-t", "--to_mail", help="Recipient E-Mail", required=True, type=str
    )

    parser.add_argument("-s", "--subject", help="Mail Subject", required=True, type=str)

    parser.add_argument(
        "-m", "--message", help="Message body", required=False, type=str
    )

    parser.add_argument(
        "-M",
        "--message_file",
        help="A file which hold the body of the mail",
        required=False,
        type=Path,
    )
    parser.add_argument(
        "-L",
        "--login_file",
        help="Path to a file which holds the login:password",
        required=False,
        type=Path,
    )

    parser.add_argument(
        "-a",
        "--attach_file",
        help="Path to a file attachment",
        action="append",
        required=False,
        type=Path,
    )

    parser.add_argument(
        "--hashiurl", help="URL to hashivault", required=False, type=str
    )

    parser.add_argument(
        "--hashisecret", help="Path to the hashivault secret", required=False, type=str
    )

    args = parser.parse_args()

    if sasl_login := os_getenv("AWS_SASL_LOGIN"):
        _login, _password = sasl_login.strip().split(sep=":", maxsplit=1)
    elif args.login_file:
        if not args.login_file.is_file():
            raise ARGSError("Could not find file", args.login_file.name)
        try:
            _login, _password = (
                args.login_file.read_text().strip().split(sep=":", maxsplit=1)
            )
        except ValueError:
            raise SENDMAILError(
                "Login file",
                args.login_file.name,
                "does not contain proper loging information",
            )
    elif args.hashiurl and args.hashisecret:
        secret_path, secret = args.hashisecret.rsplit(sep="/", maxsplit=1)
        _login, _password = get_vault_secret(secret_path, args.hashiurl)[secret].split(
            sep=":", maxsplit=1
        )
    else:
        raise ARGSError(
            "--login_file, --hashiurl and --hashisecret or AWS_SASL_LOGIN as env needs to be set"
        )

    if args.message_file:
        if not args.message_file.is_file():
            raise ARGSError("Could not find file", args.login_file.name)
        _body = args.message_file.read_text()
    elif args.message:
        _body = args.message
    else:
        raise ARGSError("--message_file or --message needs to be given")

    if args.attach_file:
        for file in args.attach_file:
            if not file.is_file():
                raise FileNotFoundError(f"Could not find file {file.name}")

            _attachment = MIMEBase("application", "octet-stream")
            _attachment.set_payload(file.read_bytes())
            _attachment.add_header(
                "Content-Disposition",
                f"attachment; filename= {file.name}",
            )

    message = create_mail(
        sender_email=args.from_mail,
        recipient_email=args.to_mail,
        subject=args.subject,
        body=_body,
        attachment=_attachment,
    )

    sendmail(
        login=_login, password=_password, message=message, smtp_server=args.smtp_server
    )
