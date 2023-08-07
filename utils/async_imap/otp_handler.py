import asyncio
from datetime import datetime

from .async_imap import AsyncIMAPClient
from utils import logger
from data.exceptions import OtpCodeException


class OtpHandler:
    def __init__(self, email: str, imap_pass: str):
        self.email = email
        self.imap_pass = imap_pass

    async def get_otp_code(self):
        for _ in range(3):
            async with AsyncIMAPClient(self.email, self.imap_pass) as client:
                try:
                    for _ in range(5):
                        await asyncio.sleep(5)
                        msg = await client.get_last_msg(subject='Arkham Email Verification',
                                                        sender='accounts@arkhamintelligence.com',
                                                        receiver=self.email)

                        if msg is not None:
                            return str(msg).split("signup process:")[1].strip().split("If you did not")[0].strip()
                except Exception as e:
                    logger.warning(f"Otp code getting {e}")

        raise OtpCodeException("No verify msg found")
