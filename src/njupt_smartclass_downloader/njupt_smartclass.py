import copy
import dataclasses
from datetime import datetime
from io import BytesIO
import json
import time
from typing import Generator
import pytz
import requests
from Crypto.Cipher import AES
from Crypto.Util import Padding

TZ_CST = pytz.timezone("Asia/Shanghai")


@dataclasses.dataclass
class NjuptSmartclassVideoSearchCondition:
    title_key: str = ""
    page_size: int = 12
    page_number: int = 1
    sort: str = "StartTime"
    order: int = 0
    start_date: str = ""
    end_date: str = ""


@dataclasses.dataclass
class NjuptSmartclassVideoSummary:
    id: str
    title: str
    start_time: datetime
    stop_time: datetime
    course_name: str
    teachers: str
    classroom_name: str
    cover_url: str


@dataclasses.dataclass
class NjuptSmartclassVideoSegmentInfo:
    index_file_uri: str


@dataclasses.dataclass
class NjuptSmartclassVideoInfo:
    id: str
    title: str
    start_time: datetime
    stop_time: datetime
    course_name: str
    segments: list[NjuptSmartclassVideoSegmentInfo]


@dataclasses.dataclass
class NjuptSmartclassVideoSearchResult:
    total_count: int
    videos: list[NjuptSmartclassVideoSummary]


class NjuptSmartclass:
    def __init__(self, session: requests.Session):
        self.session = session
        self.base_url = "https://njupt.smartclass.cn"

        self.cached_csrk_key = ""
        self.csrk_expiration = time.monotonic()

    def fetch_domain_config(self):
        url = f"{self.base_url}/config.json"
        response = self.session.get(url)
        response.raise_for_status()

        # Let requests guess the encoding, so that BOM is handled correctly
        response.encoding = None
        config = response.json()

        encrypted_domain_config = config["domainConfig"]
        encrypted_domain_config = bytes.fromhex(encrypted_domain_config)
        cipher_key = b"80bdbdbaf7494add99198960d715d41b"
        cipher_iv = b"bdbaf7494add9919"
        cipher = AES.new(cipher_key, AES.MODE_CBC, cipher_iv)
        decrypted_data = Padding.unpad(
            cipher.decrypt(encrypted_domain_config), AES.block_size
        )
        domain_config = json.load(BytesIO(decrypted_data))
        return domain_config

    def get_csrk_key(self) -> str:
        if time.monotonic() < self.csrk_expiration:
            return self.cached_csrk_key
        domain_config = self.fetch_domain_config()
        csrk_key = domain_config.get("csrkKey")
        if not csrk_key:
            raise ValueError("CSRK key not found in domain config")
        self.csrk_expiration = time.monotonic() + 1800
        self.cached_csrk_key = csrk_key
        return csrk_key

    def get_csrk_token(self) -> str:
        csrk_key = self.get_csrk_key()
        current_time = str(int(datetime.now().timestamp() * 1000))
        csrk_token = "".join(csrk_key[int(digit)] for digit in current_time)
        return csrk_token

    def search_video(self, condition: NjuptSmartclassVideoSearchCondition):
        url = f"{self.base_url}/Webapi/V1/Video/GetMyVideoList"
        params = {
            "csrkToken": self.get_csrk_token(),
            "Sort": condition.sort,
            "Order": condition.order,
            "PageSize": condition.page_size,
            "PageNumber": condition.page_number,
            "StartDate": condition.start_date,
            "EndDate": condition.end_date,
            "TitleKey": condition.title_key,
        }
        response = self.session.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        if not result["Success"]:
            raise ValueError(f"Search failed: {result['Message']}")
        if (
            "Value" not in result
            or "Data" not in result["Value"]
            or "TotalCount" not in result["Value"]
        ):
            raise ValueError("Unexpected response format")
        data = result["Value"]["Data"]
        total_count = result["Value"]["TotalCount"]
        video_summaries = [
            NjuptSmartclassVideoSummary(
                id=video["NewID"],
                title=video["Title"],
                start_time=TZ_CST.localize(
                    datetime.strptime(video["StartTime"], "%Y-%m-%d %H:%M:%S")
                ),
                stop_time=TZ_CST.localize(
                    datetime.strptime(video["StopTime"], "%Y-%m-%d %H:%M:%S")
                ),
                course_name=video["CourseName"],
                teachers=video["Teachers"],
                classroom_name=video["ClassRoomName"],
                cover_url=video["Cover"],
            )
            for video in data
        ]
        return NjuptSmartclassVideoSearchResult(
            total_count=total_count, videos=video_summaries
        )

    def search_video_all(
        self, condition: NjuptSmartclassVideoSearchCondition
    ) -> Generator[NjuptSmartclassVideoSummary, None, None]:
        yielded_count = 0
        my_condition = copy.copy(condition)
        my_condition.page_number = 1
        while True:
            result = self.search_video(my_condition)
            yield from result.videos
            yielded_count += len(result.videos)
            if yielded_count >= result.total_count or len(result.videos) == 0:
                break
            my_condition.page_number += 1

    def get_video_info_by_id(self, video_id: str) -> NjuptSmartclassVideoInfo:
        url = f"{self.base_url}/Video/GetVideoInfoDtoByID"
        params = {"csrkToken": self.get_csrk_token(), "NewId": video_id}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        result = response.json()
        if not result["Success"]:
            raise ValueError(f"Get video info failed: {result['Message']}")
        if "Value" not in result:
            raise ValueError("Unexpected response format")
        data = result["Value"]
        segments = [
            NjuptSmartclassVideoSegmentInfo(index_file_uri=segment["IndexFileUri"])
            for segment in data["VideoSegmentInfo"]
        ]
        return NjuptSmartclassVideoInfo(
            id=data["NewID"],
            title=data["Title"],
            start_time=TZ_CST.localize(
                datetime.strptime(data["StartTime"], "%Y-%m-%d %H:%M:%S")
            ),
            stop_time=TZ_CST.localize(
                datetime.strptime(data["StopTime"], "%Y-%m-%d %H:%M:%S")
            ),
            course_name=data["CourseName"],
            segments=segments,
        )
