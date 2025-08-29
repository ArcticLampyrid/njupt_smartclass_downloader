import datetime
import logging
import urllib.parse
import requests
from Crypto.Cipher import AES
from Crypto.Util import Padding

logger = logging.getLogger(__name__)


class NjuptSsoException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class NjuptSso:
    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = "https://i.njupt.edu.cn"

    def login(self, username: str, password: str) -> None:
        checkKey = str(int(datetime.datetime.now().timestamp() * 1000))

        url = f"{self.base_url}/ssoLogin/login"
        data = {
            "username": NjuptSso._encrypt(username, checkKey),
            "password": NjuptSso._encrypt(password, checkKey),
            # Captcha verification is not enabled in NJUPT SSO (2025.08)
            "captchaVerification": None,
            "checkKey": checkKey,
            "appId": "common",
            "mode": "none",
        }

        response = self.session.post(url, json=data).json()
        if not response["success"]:
            raise NjuptSsoException(response["code"], response["message"])

    def grant_service(self, service: str) -> None:
        url = f"{self.base_url}/cas/login?service={urllib.parse.quote(service)}"
        response = self.session.get(url)
        if not response.ok:
            raise Exception(
                f"Failed to grant service '{service}', code: {response.status_code}"
            )

    @staticmethod
    def _encrypt(data: str, key: str) -> str:
        cipher_key = b"iam" + key.encode()
        cipher_iv = cipher_key
        cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
        return cipher.encrypt(Padding.pad(data.encode(), AES.block_size)).hex()
