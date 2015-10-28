Current version: 1.0.0-rc1

Release Notes:
-Requires Python and Tornado web server (for python), see How To Build section in dont_readme.txt for more details
-Runs on port 9000, with a requested check-in interval of 4 minutes by default (change via command line)
-Intended use case is in a LAN enviornment, will also work on the internet, but not currently optimized for it.
-currently no scrape/statistics/ipv6/private/logging features 
-IPv6 and UDP support might be added at some point

Notice: Although it should work, py3bt_tracker is not currently optimized for performance/security in open/untrusted WAN enviornments (the internet) and extremely heavy loads. Should work well otherwise. For linux enviornments, consider building OpenTracker from source over at http://erdgeist.org/arts/software/opentracker

Read the "Stuff Not To Spec" section and "Todo List" to determine if this is suitable for your enviornment.

How To Build 
-For Windows: Stop reading this and go get binaries available under "releases"
-Windows build enviornment provided as an example 
-Use this example to understand the process when building under a gnu linux/bsd distro

1) install python
https://www.python.org/downloads/windows/  and 
For 64-bit systems "Download Windows x86-64 MSI installer"  -> from python-3.4.3.amd64.msi 
For 32-bit systems "Download Windows x86 MSI installer" ->Download python-3.4.3.msi
Required: add to path
Recommended: select "Advanced"->compile .py into binary files
Required: Relog <-important
2) open an administrative command prompt
cmd
3) install tornado web server
>pip install tornado
or  
C:\Users\User>pip install tornado
3) copy py3bt_tracker.py to c:\python34\scripts\py3bt_tracker.py
5) >cd c:\python34\scripts
6) can run using python direclty now 
c:\python34\scripts>python py3bt_tracker.py
or
>start "" python py3bt_tracker.py
or
>RunHiddenConsole.exe python py3bt_tracker.py
(available from the internets)
or
7) to compile into a .exe -Install the GCC compiler via tdm64-gcc-5.1.0-2.exe, or some other one
http://tdm-gcc.tdragon.net/download
8) >pip install pyinstaller
9) >pyinstaller --onefile py3bt_tracker.py
10) look for the output under c:\python34\scripts\dist\

Post Compilation Usage:
To run: double click on it
Detailed Usage: see usage section in the readme.md or run py3bt_tracker.exe --help
To close/stop it: ctrl+c or ctrl+z or click on the little x at the top right of the command prompt window
To log output: py3bt_tracker.exe > %userprofile%\desktop\py3bt_tracker.log.txt

Motivation/goal:
-opentracker is posix only due to fat library dependency :'(  
-same with and all other trackers I've found, either non-functional or dependencies everywhere or both why x.x
-This one is a cross platform non-equivalent with an emphasis on reduced performance and fewer (end-user) dependencies, as in: compiled already that doesn't need linux/webserver/php/sql/vsredists/boost/ides/vstudio/knowinghowtocompilesoftware/webengine etc

Questions about why this is so poorly written:
-my first python program
-my first useful program, as in program that was actually useful at solving a novel problem not solved before (standalone tracker for windows)
-emphasis is on working/legibility, not running super fast (not optimized for use on internetz)
-not sure exactly how to reference python class variables
-not sure how to create dynamic variables in py3, and py2 method using exec() was a hack
-and not sure how to print/message_pass/append binary, as in native binary, cmd doesn't seem to like it so can't rencode back to valid data after using str(binary_data)

Spec available at:
https://wiki.theory.org/BitTorrentSpecification 
https://wiki.theory.org/BitTorrent_Tracker_Protocol
http://bittorrent.org ->developers

Stuff Not To Spec:
-first announce to tracker must have "started" event item. Why not enforced? this makes sense in order to keep server-side statistics, ephemeral ones don't however so enforcing this is pointless
-unoffical official default port for trackers is 6969 not 9000. Why using a different one? default ports are icky, also: qTorrent exists
-neither default numwant of 50 nor client numwant respected, set to 30 instead. Why not respected? 30 is plenty according to implementation notes in spec, crazy clients that want 200 are crazy
-scrape option not implemented. Why not? doesn't make sense for ephemeral trackers
-option to enable registered info-hashes only. Why not? cuz ephemeral and also complicated to implement
-option to only return peer list to 'registered' peers. Why not? cuz idea is stupid and also very complicated to implement
-beep31 why not? that's more for web servers in general to respond to clients, non really for actual trackers
-trackerID. Why not? uh... how is this useful? is it like an xsrf token to identify the peer? wouldn't that only be for registered peers? that's stupid
-beep6 why not? not sure if it's widely supported enough to bother implementing, and also looks complicated, and not sure it even makes sense since anyone sniffing the line could always just do a replay attack and receive the peer list right? And anyway, TLS is a better solution to passive sniffing. Mere obfuscation would help only if data is stored in a db for anaysis later, but still any 'decrypted' obfuscation would be very damning evidence so... If this is important, then it makes more sense to seed the db with fake peers to contaminate the evidence preemtively. I could totally code this in maybe somehow if bored enough one day.

Todo list for features/bug:
-incomplete and complete should increment/decrement -partially done, need to improve "update" code still
-text/plain bencoded response -done
-error codes should be -done
1) text/plain -done
2) human readable -done
3) sent back as becoded responses -done
-figure out how to use github -partially done
-add ipv6 support at some point -will get around to it eventually...
-Should return a response of peers picked randomly from peer pool for a torrent, will get around to it eventually...
-figure out how to read, store and respond with dns names...somehow. -No idea how to implement that, maybe just resolve first and store ip's? or does spec require sending back dns names...x.x
-change db key from peer_id to ip/port combination to limit potential for abuse in untrustworthy enviornments
-udp tracker support - beep 15 -Does Tornado even know what UDP is? maybeh
-will also add obfuscation feature if I ever get that bored
-improve performance for use in WANs (production quality code optimizations + fully async web server)
-maybe implement logging, maybe

NOT on todo list:
scrape functionality -cuz ephemeral
private tracker feature - registered infohashes -cuz ephemeral
private tracker feature - registered peers -cuz stupid
separating the code into multiple files -cuz would increase end-user dependencies (2+ files instead of just 1)
