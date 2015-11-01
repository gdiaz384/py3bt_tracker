# py3bt_tracker

py3bt_tracker is a cross-platform standalone ephemeral tracker for torrents written in Python3.

The development emphasis is on zero-configuration "just works" software.

Currently implemented using a multidimentional array in memory and the Tornado Web Server (http).

google_define('ephemeral') #returns: adjective - lasting for a very short time -synonyms: transient, short-lived, brief

## Key Features:

- Works
- Prebuilt binaries
- No external dependencies or configuration required
- Permissive license
- Standards compliant (including IPv6 support)
- Easy to rebuild from source if so inclined (check release_notes.txt for detailed instructions)

## Download:

```
Latest Release: 1.0.0-rc.1
In Development: 1.0.0-rc.2
```
Click [here](https://github.com/gdiaz384/py3bt_tracker/releases) or on "releases" at the top to download the latest version.

## Typical Usage Guide:

1. double click on the .exe for your os
2. point your torrents to http://192.168.1.50:6969/announce where 192.168.1.50 gets substituted for your IP obtained from ipconfig (for lans)
3. Note: If the firewall annoyance pops up, add as an exception.

## Important Release Notes:

- Runs on port 6969, with a requested check-in interval of 4 minutes by default (change via command line)
- Currently no scrape/statistics/private/logging/obfuscation features
- Intended use case is in a LAN enviornment, will also work on the internet, but not currently optimized for it.
- I'll do a version 2.0.0 for optimized use on the internetwork system, with UDP support and obfuscation if there's any interest in doing so. That's the natural extension to this project after all. Just message me over git.

## Advanced Usage Guide:
```
Syntax: py3bt_tracker {--port=6969} {--client_request_interval=4} {--enable_obfuscation}
Syntax: py3bt_tracker {-p=9000} {-i=30} {-o}
>py3bt_tracker --help
>py3bt_tracker
>py3bt_tracker -p=6969
>py3bt_tracker -p=9000 -i=4
>py3bt_tracker -p=6969 --client_request_interval=16
Windows (binary): >start "" C:\Users\User\Downloads\py3bt_tracker.exe
Windows (pyscript): >start "" python C:\Users\User\Downloads\py3bt_tracker.py --port=6969 -i=30
```

Notes: obfuscation not currently implemented, planned for v2.0 if there's enough interest

## License:
Pick your License: GPL (any) or BSD (any) or MIT/Apache

If I get any questions, I'm changing this to "beerware" and will refuse to elaborate further. You have been warned.
