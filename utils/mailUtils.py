import random
import time
import string

from imap_tools import MailBox, AND
from loguru import logger


class MailUtils:
    def __init__(self, email: str, imap_pass: str):
        self.email = email
        self.imap_pass = imap_pass

        self.domain = self.parse_domain()

    def get_msg(self, to=None, subject=None, from_=None, seen=False, limit=None, reverse=True, delay=60):
        time.sleep(5)
        with MailBox(self.domain).login(self.email, self.imap_pass) as mailbox:
            for _ in range(delay // 3):
                try:
                    time.sleep(3)
                    # mailbox.folder.subscribe('JUNK', True)
                    for msg in mailbox.fetch(AND(to=to, subject=subject, from_=from_,
                                                 seen=seen), limit=limit, reverse=reverse):

                        logger.success(f'{self.email} | Successfully received msg: {msg.subject}')
                        return {"success": True, "msg": msg.html}
                except Exception as error:
                    logger.error(f'{self.email} | Unexpected error when getting code: {str(error)}')
                else:
                    logger.error(f'{self.email} | No message received')
        return {"success": False, "msg": "Didn't find msg"}

    def parse_domain(self):
        domain = self.email.split("@")[-1]
        if "hotmail" in domain or "live" in domain:
            domain = "outlook.com"
        return f"imap.{domain}"
