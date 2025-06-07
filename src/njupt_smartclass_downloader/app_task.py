from dataclasses import dataclass, field
from enum import StrEnum
from io import BytesIO
import json
import os
from pathlib import Path
from queue import Queue
import subprocess
import sys
import threading
import time
from typing import Generator, List, Literal, Optional, Protocol, Tuple
from urllib import request
from lxml import etree
import requests
from urllib.parse import urljoin


from njupt_smartclass_downloader.njupt_smartclass import NjuptSmartclass


class PoolKind(StrEnum):
    INDEX = "index"
    DOWNLOAD = "download"
    EXTRACT_SLIDES = "extract_slides"


@dataclass
class DownloadOptions:
    type_filter: List[str] = field(
        default_factory=lambda: ["VGA", "Video1", "Video2", "Video3"]
    )
    extract_slides: bool = True


POOL_WORKER_COUNT = {
    PoolKind.INDEX: 2,
    PoolKind.DOWNLOAD: 4,
    PoolKind.EXTRACT_SLIDES: 4,
}


class TaskReporter:
    def __init__(self, task_manager: "TaskManager", task_id: str) -> None:
        self.task_manager = task_manager
        self.task_id = task_id

    def report_progress(
        self, step_name: Optional[str] = None, step_progress: Optional[float] = None
    ) -> None:
        self.task_manager.report_progress(self.task_id, step_name, step_progress)


class Task:
    def pool_kind(self) -> PoolKind: ...
    def display(self) -> str: ...
    def run(self, reporter: TaskReporter) -> Generator["Task", None, None]: ...


class IndexTask(Task):
    def __init__(
        self,
        title: str,
        video_id: str,
        local_path: str,
        cookies,
        options: DownloadOptions,
    ) -> None:
        super().__init__()
        self.title = title
        self.video_id = video_id
        self.local_path = local_path
        self.cookies = cookies
        self.options = options

    def pool_kind(self) -> PoolKind:
        return PoolKind.INDEX

    def display(self) -> str:
        return f"{self.title} - Index"

    def run(self, reporter: TaskReporter) -> Generator[Task, None, None]:
        session = requests.Session()
        session.cookies.update(self.cookies)
        smartclass = NjuptSmartclass(session)
        video_info = smartclass.get_video_info_by_id(self.video_id)
        if video_info is None:
            raise ValueError(f"Video info not found for ID: {self.video_id}")
        if len(video_info.segments) == 0:
            raise ValueError(f"No segments found for video ID: {self.video_id}")
        single_segment = len(video_info.segments) == 1
        for segment_index, segment in enumerate(video_info.segments):
            index_xml = session.get(segment.index_file_uri).content

            segment_path = (
                os.path.join(self.local_path, f"Seg{segment_index + 1}")
                if not single_segment
                else self.local_path
            )
            os.makedirs(segment_path, exist_ok=True)

            # save index.xml
            metadata_path = os.path.join(segment_path, "index.xml")
            os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
            with open(metadata_path, "wb") as f:
                f.write(index_xml)

            # extract video sources from index.xml
            index_tree = etree.parse(BytesIO(index_xml), parser=etree.XMLParser())
            src_extractor_xpath: List[Tuple[str, str]] = [
                # (VideoType, XPath)
                ("VGA", "/Info/VGA[@Src != '']/@Src"),
                ("Video1", "/Info/Video1[@Src != '']/@Src"),
                ("Video2", "/Info/Video2[@Src != '']/@Src"),
                ("Video3", "/Info/Video3[@Src != '']/@Src"),
            ]
            sources: List[Tuple[str, str]] = [
                # (VideoType, Remote URL)
            ]
            for video_type, xpath in src_extractor_xpath:
                if video_type not in self.options.type_filter:
                    continue

                src_elements = index_tree.xpath(xpath)
                if not src_elements:
                    continue
                for src in src_elements:
                    if src:
                        remote_url = urljoin(segment.index_file_uri, src)
                        sources.append((video_type, remote_url))

            # submit download tasks for each video
            for video_type, remote_url in sources:
                local_path = os.path.join(segment_path, video_type + ".mp4")
                yield DownloadTask(
                    title=self.title,
                    video_type=video_type,
                    segment_seq=segment_index + 1 if not single_segment else None,
                    remote_url=remote_url,
                    local_path=local_path,
                    options=self.options,
                )


class DownloadTask(Task):
    def __init__(
        self,
        title: str,
        video_type: str,
        segment_seq: Optional[int],
        remote_url: str,
        local_path: str,
        options: DownloadOptions,
    ) -> None:
        super().__init__()
        self.title = title
        self.video_type = video_type
        self.segment_seq = segment_seq
        self.remote_url = remote_url
        self.local_path = local_path
        self.options = options

    def pool_kind(self) -> PoolKind:
        return PoolKind.DOWNLOAD

    def display(self) -> str:
        if self.segment_seq is not None:
            return f"{self.title} - Seg{self.segment_seq} - {self.video_type})"
        return f"{self.title} - {self.video_type}"

    def run(self, reporter: TaskReporter) -> Generator[Task, None, None]:
        os.makedirs(os.path.dirname(self.local_path), exist_ok=True)

        if not os.path.exists(self.local_path):
            if os.path.exists(self.local_path + ".part"):
                os.remove(self.local_path + ".part")

            def reporthook(block_num: int, block_size: int, total_size: int) -> None:
                if total_size > 0:
                    downloaded = block_num * block_size
                    progress = downloaded / total_size
                    reporter.report_progress(step_progress=progress)

            request.urlretrieve(self.remote_url, self.local_path + ".part", reporthook)

            os.rename(self.local_path + ".part", self.local_path)

        if self.video_type == "VGA" and self.options.extract_slides:
            # If it's VGA video, extract slides
            yield ExtractSlidesTask(
                title=self.title,
                video_path=self.local_path,
                segment_seq=self.segment_seq,
            )


class ExtractSlidesTask(Task):
    def __init__(self, title: str, video_path: str, segment_seq: Optional[int]) -> None:
        super().__init__()
        self.title = title
        self.video_path = video_path
        self.segment_seq = segment_seq

    def pool_kind(self) -> PoolKind:
        return PoolKind.EXTRACT_SLIDES

    def display(self) -> str:
        if self.segment_seq is not None:
            return f"{self.title} - Seg{self.segment_seq} - Slides"
        return f"{self.title} - Slides"

    def run(self, reporter: TaskReporter) -> Generator[Task, None, None]:
        slides_file = os.path.realpath(
            os.path.join(os.path.dirname(self.video_path), "Slides.pdf")
        )
        if os.path.exists(slides_file):
            return
        slides_file_part = slides_file + ".part"
        if os.path.exists(slides_file_part):
            os.remove(slides_file_part)

        process = None
        try:
            args = []
            if getattr(sys, "frozen", False):
                args.append(sys.executable)
            else:
                args.append(sys.executable)
                args.append(os.path.dirname(os.path.realpath(__file__)))
            args.extend(
                [
                    "export-slides",
                    "--input",
                    os.path.realpath(self.video_path),
                    "--output",
                    slides_file_part,
                ]
            )
            process = subprocess.Popen(
                args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            assert process.stdout is not None, "subprocess stdout is None"

            while True:
                line = process.stdout.readline()
                if not line:
                    break
                try:
                    json_data = json.loads(line)
                    reporter.report_progress(
                        step_name=json_data.get("step"),
                        step_progress=(
                            json_data.get("current") / json_data.get("total")
                            if json_data.get("total") > 0
                            else None
                        ),
                    )
                except json.JSONDecodeError as e:
                    continue
            return_code = process.wait()
            if return_code != 0:
                raise RuntimeError(f"Script failed with return code {return_code}.")
        except Exception as e:
            raise
        finally:
            if process and process.poll() is None:
                process.terminate()

        os.rename(slides_file_part, slides_file)
        yield from ()


class TaskStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskInnerState:
    id: str
    task: Task
    status: TaskStatus = TaskStatus.QUEUED
    error: Optional[str] = None
    step_name: Optional[str] = None
    step_progress: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class TaskInfo:
    id: str
    display_name: str
    status: TaskStatus
    error: Optional[str] = None
    step_name: Optional[str] = None
    step_progress: Optional[float] = None
    elapsed_time: float = 0


class TaskManager:
    def __init__(self) -> None:
        self.__info_mutex = threading.Lock()
        self.__tasks: dict[str, TaskInnerState] = {}

        # Using Queue for thread-safe task management
        self.__pools: dict[PoolKind, Queue[str]] = {kind: Queue() for kind in PoolKind}

        for kind, count in POOL_WORKER_COUNT.items():
            for i in range(count):
                threading.Thread(
                    target=self.__worker,
                    args=(kind,),
                    daemon=True,
                    name=f"TaskWorker-{kind}-{i}",
                ).start()

    def __worker(self, kind: PoolKind) -> None:
        pool = self.__pools[kind]
        while True:
            task_id = pool.get()
            if task_id is None:
                break
            with self.__info_mutex:
                inner_state = self.__tasks[task_id]
                inner_state.status = TaskStatus.RUNNING
                inner_state.start_time = time.monotonic()
                task = inner_state.task
                del inner_state
            try:
                for new_task in task.run(TaskReporter(self, task_id)):
                    self.submit_task(new_task)
                with self.__info_mutex:
                    inner_state = self.__tasks[task_id]
                    inner_state.status = TaskStatus.COMPLETED
                    inner_state.end_time = time.monotonic()
            except Exception as e:
                with self.__info_mutex:
                    inner_state = self.__tasks[task_id]
                    inner_state.status = TaskStatus.FAILED
                    inner_state.end_time = time.monotonic()
                    inner_state.error = str(e)
            finally:
                pool.task_done()

    def submit_task(self, task: Task) -> None:
        kind = task.pool_kind()
        id = f"t{len(self.__tasks) + 1}"
        with self.__info_mutex:
            self.__tasks[id] = TaskInnerState(
                id=id, task=task, status=TaskStatus.QUEUED
            )
        self.__pools[kind].put(id)

    def report_progress(
        self, task_id: str, step_name: Optional[str], step_progress: Optional[float]
    ) -> None:
        with self.__info_mutex:
            if task_id in self.__tasks:
                self.__tasks[task_id].step_name = step_name
                self.__tasks[task_id].step_progress = step_progress

    def get_task_info(self) -> list[TaskInfo]:
        result = []
        with self.__info_mutex:
            for id, state in self.__tasks.items():
                elapsed_time = 0
                if state.start_time is not None and state.end_time is not None:
                    elapsed_time = state.end_time - state.start_time
                elif state.start_time is not None:
                    elapsed_time = time.monotonic() - state.start_time
                result.append(
                    TaskInfo(
                        id=id,
                        display_name=state.task.display(),
                        status=state.status,
                        error=state.error,
                        step_name=state.step_name,
                        step_progress=state.step_progress,
                        elapsed_time=elapsed_time,
                    )
                )
        return result
