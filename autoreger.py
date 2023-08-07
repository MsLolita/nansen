import time
from concurrent.futures import ThreadPoolExecutor

from utils import shift_file, logger
from utils.file_to_list import file_to_list
from nansen import Nansen


class AutoReger:
    def __init__(self):
        self.emails_path: str = "data\\inputs\\emails.txt"
        self.proxies_path: str = "data\\inputs\\proxies.txt"
        # self.wallets_path: str = "data\\inputs\\wallets.txt"

        self.success = 0
        self.custom_user_delay = None

    def get_accounts(self):
        emails = file_to_list(self.emails_path)
        # wallets = file_to_list(self.wallets_path)
        proxies = file_to_list(self.proxies_path)

        min_accounts_len = len(emails)

        # if not emails:
        #     logger.info(f"Generated random emails!")
        #     emails = generate_random_emails(100)

        # if not wallets:
        #     logger.info(f"Generated random wallets!")
        #     wallets = [wallet[0] for wallet in generate_random_wallets(len(emails))]

        accounts = []

        for i in range(min_accounts_len):
            accounts.append((*emails[i].split(":")[:2], proxies[i] if len(proxies) > i else None))

        return accounts

    def remove_account(self):
        return shift_file(self.emails_path), shift_file(self.proxies_path)

    def start(self):
        referral_link = input("Referral link(https://nansen.ai/early-access/?ref=pWPZj2): ")

        Nansen.referral = referral_link.split('ref=')[-1]

        threads = int(input("Enter amount of threads: "))

        self.custom_user_delay = float(input("Delay in seconds: "))

        accounts = self.get_accounts()

        with ThreadPoolExecutor(max_workers=threads) as executor:
            executor.map(self.register, accounts)

        if self.success:
            logger.success(f"Successfully registered {self.success} accounts :)")
        else:
            logger.warning(f"No accounts registered :(")

    def register(self, account: tuple):
        nansen = Nansen(*account)
        is_ok = False
        res_msg: str = ""

        try:
            time.sleep(self.custom_user_delay)

            if nansen.send_approve_link():
                is_ok = nansen.verify_email()
        except Exception as e:
            logger.error(f"Error {e}")

        self.remove_account()

        if is_ok:
            nansen.logs()
            self.success += 1
        else:
            nansen.logs_fail(res_msg)

    @staticmethod
    def is_file_empty(path: str):
        return not open(path).read().strip()
