import sys


def update_title(terminal_title):
    bot_name = 'gSheetUpdater'
    if sys.platform == 'linux':
        print(f'\33]0;[{bot_name}] | {terminal_title}\a', end='', flush=True)
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f'[{bot_name}] | {terminal_title}')