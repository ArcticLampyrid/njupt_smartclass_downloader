from textual.widgets import ListItem, Static
from rich.text import Text

from njupt_smartclass_downloader.app_task import TaskInfo, TaskStatus


def format_duration(duration: float) -> str:
    if duration < 60:
        return f"{int(duration)}s"
    else:
        minutes = duration // 60
        seconds = duration % 60
        return f"{int(minutes)}m{int(seconds)}s"


class TaskListItem(ListItem):
    def __init__(self, task_info):
        content = self._create_content(task_info)
        super().__init__(Static(content))

    def _create_content(self, task_info: TaskInfo) -> Text:
        content = Text()
        content.append(f"{task_info.display_name}", style="bold white")

        if task_info.status == TaskStatus.QUEUED:
            status_display = "Queued"
        elif task_info.status == TaskStatus.RUNNING:
            status_display = "Running"
            if task_info.elapsed_time is not None:
                status_display += " for " + \
                    format_duration(task_info.elapsed_time)
        elif task_info.status == TaskStatus.COMPLETED:
            status_display = "Completed"
            if task_info.elapsed_time is not None:
                status_display += " in " + \
                    format_duration(task_info.elapsed_time)
        elif task_info.status == TaskStatus.FAILED:
            status_display = "Failed"
        else:
            status_display = "Unknown"
        content.append(
            f"\n    Status: {status_display}", style="dim green")

        if task_info.status == "running":
            if task_info.step_name is not None:
                content.append(
                    f" ({task_info.step_name})", style="dim green")

            if task_info.step_progress is not None:
                n_fill_char = int(task_info.step_progress * 20)
                n_remaining_char = 20 - n_fill_char
                content.append("  " + n_fill_char * '━', style="bold yellow")
                content.append(n_remaining_char * '━', style="dim yellow")
                content.append(
                    f" {task_info.step_progress:.2%}", style="yellow")

        if task_info.error:
            content.append(f" ({task_info.error})", style="red")

        return content

    def update_task_info(self, task_info):
        content = self._create_content(task_info)
        static_widget = self.query_one(Static)
        static_widget.update(content)
