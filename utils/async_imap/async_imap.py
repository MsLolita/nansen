import re
import ssl
from datetime import datetime

import certifi

from collections import namedtuple
from email.message import Message
from email.parser import BytesParser

import aioimaplib

# ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Cc', 'Bcc', 'Date', 'Subject',
#                                    'Message-ID', 'In-Reply-To', 'References'}
ID_HEADER_SET = {'Content-Type', 'From', 'To', 'Subject'}
FETCH_MESSAGE_DATA_UID = re.compile(rb'.*UID (?P<uid>\d+).*')
FETCH_MESSAGE_DATA_SEQNUM = re.compile(rb'(?P<seqnum>\d+) FETCH.*')
FETCH_MESSAGE_DATA_FLAGS = re.compile(rb'.*FLAGS \((?P<flags>.*?)\).*')
MessageAttributes = namedtuple('MessageAttributes', 'uid flags sequence_number')


class AsyncIMAPClient(aioimaplib.IMAP4_SSL):
    def __init__(self, user: str, password: str, host: str = None):
        self.user = user
        self.password = password
        self.host = self.parse_host() if host is None else host

        super().__init__(host=self.host, timeout=30, ssl_context=ssl.create_default_context(cafile=certifi.where()))

    async def __aenter__(self):
        await self.wait_hello_from_server()
        await self.login(self.user, self.password)
        await self.select('INBOX')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.logout()

    async def fetch_messages_headers(self, max_uid: int) -> int:
        # result, data = await self.uid('fetch', None, "UNSEEN")  # (ALL/UNSEEN)
        # i = len(data[0].split())
        # latest_email_uid = data[0].split()[0]
        # print(i, latest_email_uid)
        # return latest_email_uid
        response = await self.uid('fetch', '%d:*' % (max_uid + 1),
                                         '(UID FLAGS BODY.PEEK[HEADER.FIELDS (%s)])' % ' '.join(ID_HEADER_SET))
        new_max_uid = max_uid
        if response.result == 'OK':
            for i in range(0, len(response.lines) - 1, 3):
                fetch_command_without_literal = b'%s %s' % (response.lines[i], response.lines[i + 2])
                uid = int(FETCH_MESSAGE_DATA_UID.match(fetch_command_without_literal).group('uid'))
                if uid > max_uid:
                    new_max_uid = uid
        else:
            print('error %s' % response)
        return new_max_uid

    async def fetch_message_body(self, uid: int) -> Message:
        dwnld_resp = await self.uid('fetch', str(uid), 'BODY.PEEK[]')
        return BytesParser().parsebytes(dwnld_resp.lines[1])

    async def get_last_msg(self, subject: str = None, sender: str = None, receiver: str = None):
        persistent_max_uid = await self.fetch_messages_headers(1)
        # print(persistent_max_uid)
        msg = await self.fetch_message_body(persistent_max_uid)

        if subject.lower() in msg['subject'].lower() and sender.lower() in msg['from'].lower() \
                and receiver.lower() == msg['to'].lower():
            if AsyncIMAPClient.is_fresh(msg['date']):
                return msg

    def parse_host(self):
        domain = self.user.split("@")[-1]
        if "hotmail" in domain or "live" in domain:
            domain = "outlook.com"
        return f"imap.{domain}"

    @staticmethod
    def is_fresh(timestamp_str, time_sec: int = 30):
        # Convert the timestamp string to a datetime object
        dt_object = datetime.strptime(timestamp_str, "%a, %d %b %Y %H:%M:%S %z (%Z)")

        # Calculate the current timestamp
        current_time = datetime.now(dt_object.tzinfo)

        # Calculate the difference between the current time and the provided timestamp
        time_difference = current_time - dt_object

        # Check if the time difference is less than a minute (60 seconds)
        return time_difference.total_seconds() < time_sec


# import user
# async def main():
#     login = 'sienkie_kirsten@hotmail.com'
#     password = 'Kirsten19831983'
#     host = 'imap.outlook.com'
#     async with IMAPClient(host, login, password) as client:
#         msg = await client.get_last_msg(subject='Arkham Email Verification', sender='faralechko@gmail.com',
#                                         receiver='sienkie_kirsten@hotmail.com')
#         print(str(msg.get_payload()[1]).split("signup process:<br><br>")[1].split("<br>")[0])
#         # print(user.message_from_bytes(a.as_bytes()))
#
#
# # if __name__ == '__main__':
# #     asyncio.run(main())

