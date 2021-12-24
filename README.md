# gSheetUpdater
 
## REMEMBER TO CHECK PROGRAM_DATA AND LOGS FOR WEIRDNESS BEFORE PUSHING.

Compile to .exe and supporting files:
```bash
pyinstaller --clean -n gSheetUpdater -i assets/icon.ico --upx-dir C:\Users\lafft\Downloads\upx-3.96-win64\ --hidden-import colorama --hidden-import pywin32 --hidden-import win32file --onefile main.py
```

Pull on server:
```bash
git clone https://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@github.com/lafftar/gSheetUpdater.git
```