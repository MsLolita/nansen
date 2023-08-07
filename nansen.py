import json
import time
from random import choice

import requests
import pyuseragents
from bs4 import BeautifulSoup

from anticaptchaofficial.recaptchav2proxyless import recaptchaV2Proxyless

from data.captcha import ANTICAPTCHA_API_KEY, SITE_KEY, URL
from utils import str_to_file, logger
from string import ascii_lowercase, digits

from utils import MailUtils


class Nansen(MailUtils):
    referral = None

    def __init__(self, email: str, imap_pass: str, proxy: str = None):
        super().__init__(email, imap_pass)
        self.address = None  # address
        self.proxy = f"http://{proxy}" if proxy else None

        self.password = Nansen.generate_password(7)

        self.headers = {
            'authority': 'getlaunchlist.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,uk',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.nansen.ai',
            'referer': 'https://www.nansen.ai/',
            'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': pyuseragents.random(),
        }

        self.session = requests.Session()

        self.session.headers.update(self.headers)
        self.session.proxies.update({'https': self.proxy, 'http': self.proxy})

    def send_approve_link(self):
        url = 'https://getlaunchlist.com/s/yeywGr'

        params = {
            'ref': Nansen.referral,
        }

        data = {
            '_gotcha': '',
            'email': self.email,
            'captcha_settings': json.dumps(
                {"keyname": "google_recaptcha_classic", "fallback": "true", "orgId": "00D5i0000088WA3",
                 "ts": int(time.time() * 10 ** 3)}),
            'g-recaptcha-response': Nansen.__bypass_captcha(),
            'submit': 'Join Waitlist',
        }

        response = self.session.post(url, params=params, data=data,
                                     allow_redirects=False)

        return '<script data-cfasync="false"' in response.text

    def verify_email(self):
        verify_link = self.get_verify_link()
        return self.approve_email(verify_link)

    def get_verify_link(self):
        result = self.get_msg(from_="hello@getlaunchlist.com", limit=1)
        html = result["msg"]
        soup = BeautifulSoup(html, 'lxml')
        a = soup.select_one('a[rel="noopener noreferrer"]')
        return a.text.strip()

    def approve_email(self, verify_link: str):
        response = self.session.get(verify_link, allow_redirects=False)

        return '<script data-cfasync="false"' in response.text

    def logs(self):
        file_msg = f"{self.email}|{self.address}|{self.proxy}"
        str_to_file(f"data\\logs\\success.txt", file_msg)
        logger.success(f"Register {self.email}")

    def logs_fail(self, msg: str = ""):
        file_msg = f"{self.email}|{self.address}|{self.proxy}"
        str_to_file(f"data\\logs\\failed.txt", file_msg)
        logger.error(f"Failed {self.email} {msg}")

    @staticmethod
    def __bypass_captcha():
        solver = recaptchaV2Proxyless()
        # solver.set_verbose(1)
        solver.set_key(ANTICAPTCHA_API_KEY)
        solver.set_website_url(URL)
        solver.set_website_key(SITE_KEY)

        token = solver.solve_and_return_solution()

        if not token:
            logger.error(f"{token} Failed to solve captcha! Please put your API key in data/captcha/__init__.py")
            exit()

        return token

    @staticmethod
    def generate_password(k=10):
        return ''.join([choice(ascii_lowercase + digits) for i in range(k)])
