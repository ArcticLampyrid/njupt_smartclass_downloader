from textual.widgets import ListItem, Static
from rich.text import Text

from njupt_smartclass_downloader.njupt_smartclass import NjuptSmartclassVideoSummary


class VideoListItem(ListItem):
    def __init__(self, video: NjuptSmartclassVideoSummary, selected: bool = False):
        self.video = video
        self.is_selected = selected
        super().__init__(Static(self._create_content()))

    def _create_content(self) -> Text:
        # Format time string
        time_str = self.video.start_time.strftime('%Y-%m-%d %H:%M') + " - "
        if self.video.start_time.date() != self.video.stop_time.date():
            time_str += self.video.stop_time.strftime('%Y-%m-%d %H:%M')
        else:
            time_str += self.video.stop_time.strftime('%H:%M')

        content = Text()
        if self.is_selected:
            content.append("█ ", style="bold green")
        else:
            content.append("  ", style="")
        content.append(f"{self.video.course_name}", style="bold white")
        content.append(f" | {self.video.teachers}", style="dim white")
        content.append(f" | {self.video.classroom_name}\n", style="yellow")
        if self.is_selected:
            content.append("█ ", style="bold green")
        else:
            content.append("  ", style="")
        content.append(f"  {time_str}", style="dim blue")

        return content

    def toggle_selection(self):
        self.is_selected = not self.is_selected
        self.update_display()

    def set_selection(self, selected: bool):
        self.is_selected = selected
        self.update_display()

    def update_display(self):
        """Update the display content of the video item."""
        static_widget = self.query_one(Static)
        static_widget.update(self._create_content())
