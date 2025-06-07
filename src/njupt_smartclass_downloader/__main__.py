import json


def main():
    # if `export-slides` (subcommand) is in the first argument,
    # then parse and get `--input` and `--output` arguments
    # if `export-slides` is not in the first argument, then run the app normally
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "export-slides":
        from njupt_smartclass_downloader.slides_extractor.extractor import (
            extract_slides,
        )
        from argparse import ArgumentParser

        parser = ArgumentParser(description="Export slides from VGA video")
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)
        args = parser.parse_args(sys.argv[2:])

        def progress_callback(step: str, current: int, total: int):
            print(
                json.dumps({"step": step, "current": current, "total": total}),
                flush=True,
            )

        extract_slides(args.input, args.output, report_progress=progress_callback)
        return

    from njupt_smartclass_downloader.app import NjuptSmartclassDownloaderApp

    app = NjuptSmartclassDownloaderApp()
    app.run()


if __name__ == "__main__":
    main()
