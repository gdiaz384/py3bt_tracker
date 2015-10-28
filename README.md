Click on the hyperlink at the top or "release" to download the latest version.

Description:
py3bt_tracker.py is a cross-platform standalone ephemeral tracker for torrents written in Python3.
The development emphasis is on zero-configuration "just works" software.
Currently implemented using a multidimentional array in memory and the Tornado Web Server.

Key Features:
-Works
-Prebuilt binaries
-No external dependencies or configuration required
-Permissive license
-easy to rebuild from source if so inclined (detailed instructions provided in dont_readme.txt)
-Standards Compliant

Usage guide:
1) double click on the .exe for your os
2) point your torrents to http://127.0.0.1:9000/announce 
where 127.0.0.1 is substituted for your IP obtained from ipconfig (for lans)
Note: If the firewall annoyance pops up, add as an exception.

google_define('ephemeral') #returns: adjective - lasting for a very short time -synonyms: transient, short-lived, brief

Important Release Notes:
-Runs on port 9000, with a requested check-in interval of 4 minutes by default (change via command line)
-Intended use case is in a LAN enviornment, will also work on the internet, but not currently optimized for it.
-currently no scrape/statistics/ipv6/private/logging features
-IPv6, UDP support and obfuscation features might be added at some point

"API" - Syntax:
py3bt_tracker --help
py3bt_tracker {port='9000'} {interval='4'} {obfuscation='off'}

"API" - Example usage:
py3bt_tracker --help
py3bt_tracker
py3bt_tracker 6969
py3bt_tracker 9000 4
py3bt_tracker 6969 16 off
py3bt_tracker 8080 30 on
Windows (binary):  start "" C:\Users\User\Downloads\py3bt_tracker.exe 9000 10
Windows (pyscript): start "" python C:\Users\User\Downloads\py3bt_tracker.py 6969

Notes: obfuscation not currently implemented, planned for v2.0 (maybe)

License:
Pick your License: GPL (any) or BSD (any) or MIT/Apache
-If I get any questions, I'm changing this to "beerware" and will refuse to elaborate further. You've been warned.
