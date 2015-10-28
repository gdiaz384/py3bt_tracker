For .py to .exe conversion:

A) to install python (3.4.3 msi) -> add to path -> log out -> log back in
B) Install the GCC compiler via tdm64-gcc-5.1.0-2.exe
C) A python to exe compiler (pyinstaller) and software specific dependencies
-pip is a package manager for python

start->cmd
>cd py3bt_tracker
>pip install pyinstaller
>pyinstaller --version (to confirm it works)
>pip install Tornado
>pyinstaller --onefile py3bt_tracker.py
look for the output exe under dist\