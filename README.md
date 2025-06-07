# NJUPT SmartClass Downloader
A command-line application with an interactive TUI (Terminal User Interface) for downloading course recordings from NJUPT SmartClass platform.

## Features
- 🎨 **Interactive TUI**: Beautiful terminal user interface built with Textual
- 🎥 **Batch Video Download**: Download multiple recordings in a batch
- 📊 **Heuristic Slide Extraction**: Extract presentation slides from VGA recordings as PDF files

## Installation
### Using Docker
```bash
git clone https://github.com/ArcticLampyrid/njupt_smartclass_downloader.git
cd njupt_smartclass_downloader
docker buildx build -t njupt-smartclass-downloader .
```

### Using Poetry
```bash
git clone https://github.com/ArcticLampyrid/njupt_smartclass_downloader.git
cd njupt_smartclass_downloader
poetry install
```

## Usage
### Interactive Mode (Default)
If you are using a Docker image, run the following command to start the application:
```bash
docker run -it --rm -v $(pwd):/app njupt-smartclass-downloader
```
If you installed the application using Poetry, run:
```bash
poetry run njupt_smartclass_downloader
```
This will launch the interactive TUI where you can log in and start your downloads.
 
1. **Login**: Enter your NJUPT credentials when prompted
2. **Search**: Type `/` to search for recordings
3. **Select**: Use arrow keys to navigate and spacebar to select recordings
4. **Start Downloading**: Type `d` to start downloading selected recordings; some options may be prompted
5. **Monitor Progress**: View real-time download progress and task status
6. **Completion**: Once downloads are complete, files will be saved in the `SmartclassDownload` directory
   ```
   SmartclassDownload/
   ├── CourseName1/
   │   ├── 20250604 0950_1035/
   │   │   ├── index.xml         # Course metadata
   │   │   ├── VGA.mp4           # Screen recording
   │   │   ├── Video1.mp4        # Camera view 1
   │   │   ├── Video2.mp4        # Camera view 2
   │   │   └── Slides.pdf        # Extracted slides via heuristic algorithm
   │   └── 20250604 1040_1125/
   │       └── ...
   └── CourseName2/
       └── ...
   ```

## Development
### Project Structure
```
src/njupt_smartclass_downloader/
├── __main__.py             # Entry point
├── app.py                  # Main application class
├── app_task.py             # Task management and threading
├── njupt_smartclass.py     # SmartClass API client
├── njupt_sso.py            # NJUPT SSO authentication
├── screens/                # TUI screens
├── slides_extractor/       # Slide extraction modules
├── styles/                 # TUI styling
└── widgets/                # Custom TUI widgets  
```

### Dev Container
This project includes a VS Code Dev Container configuration with all necessary dependencies pre-installed. Open the project in VS Code and select "Reopen in Container" when prompted.

After the container is built, remember to call Poetry to sync dependencies:
```bash
poetry sync
```

### Dependency Management
Dependencies are managed using Poetry. To add a new dependency, run:
```bash
poetry add $package_name
```

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgements
Special thanks to GitHub Copilot and Claude Sonnet 4 for their assistance in developing this project.

## License
Licensed under GNU Affero General Public License v3.0 or later. See [LICENSE](LICENSE.md) for more information.

## Disclaimer
This tool is for educational purposes only. Users are responsible for complying with NJUPT's terms of service and applicable laws. The authors are not responsible for any misuse of this software.
