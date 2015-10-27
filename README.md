# py3bt_tracker
py3bt_tracker.py is an Ultra-low performance and poorly written standalone ephemeral tracker for torrents written in Python3 
with no scrape/statistics/ipv6/private features and runs on port 9000 (hardcoded).  py3bt_tracker.py is a python implementation of
the tracker portions of https://wiki.theory.org/BitTorrentSpecification /BitTorrent_Tracker_Protocol and /beeps using Tornado Web Server
Pick your License: GPL (any) or BSD (any) or MIT/Apache


google_define('ephemeral') #returns: adjective - lasting for a very short time -synonyms: transient, short-lived, brief


Usage guide:
1) double click on the .exe for your os
2) point your torrents to http://127.0.0.1:9000/announce 
where 127.0.0.1 is substituted for your IP obtained from ipconfig (for lans)
