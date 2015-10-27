Current version: 1.0.0-rc1
Note: Although it should work, py3bt_tracker is not currently optimized for performance/security in open WAN enviornments (the internet)

Build guide for the .py script (mainly for linux people):
1) install python from python-3.4.3.amd64.msi (add to path and then relog <-important)
2) administrative command prompt
cmd
3) install tornado web server
>pip install tornado
3) copy script.py to c:\python34\scripts
5) >cd c:\python34\scripts
6) can run using python direclty now 
>python py3bt_tracker.py
or
>start "" python py3bt_tracker.py
or
>RunHiddenConsole.exe python py3bt_tracker.py
or
7) to compile into a .exe -Install the GCC compiler via tdm64-gcc-5.1.0-2.exe, or some other one
8) >pip install pyinstaller
9) >pyinstaller --onefile py3bt_tracker.py
10) look for the output under c:\python34\scripts\dist\
11) continue with the steps in the usage guide above

Questions about licensing:
-If I get any questions, I'm changing this to "beerware" and will refuse to elaborate further. You've been warned.

Motivation/goal:
opentracker is posix only :'(
so this one is a cross platform non-equivalent with an emphasis on reduced performance and 
fewer (end-user) dependencies, as in: compiled already that doesn't need linux/webserver/php/sql/vsredists

Questions about why this is so poorly written:
-my first python program
-my first useful program, as in program that was actually useful at solving a novel problem not solved 
before (standalone tracker for windows)
-emphasis is on working/legibility, not running super fast (not optimized for use on internetz)
-not sure exactly how to reference python class variables
-not sure how to create dynamic variables in py3, py2 method using exec() was a hack
-and not sure how to print/message_pass/append binary, as in native binary, cmd doesn't seem to like it so 
can't rencode back to valid data after using str(binary_data)

Stuff not to spec:
-first announce to tracker must have "started" event item. Why not enforced? this makes sense in order to keep 
server-side statistics, ephemeral ones don't however so enforcing this is pointless
-unoffical official default port for trackers is 6969 not 9000. Why using a different one? default ports are icky, also: qTorrent exists
-neither default numwant of 50 nor client numwant respected, set to 30 instead. Why not respected? 30 is plenty, crazy clients that want 200 are crazy
-scrape option not implemented. Why not? doesn't make sense for ephemeral trackers
-option to enable registered info-hashes only. Why not? cuz ephemeral and also complicated to implement
-option to only return peer list to 'registered' peers. Why not? cuz idea is stupid and also very complicated to implement
-beep31 why not? that's more for web servers in general to respond to clients, non really for actual trackers
-trackerID. Why not? uh... how is this useful? is it like an xsrf token to identify the peer? wouldn't that only be for 
registered peers? that's stupid
-beep6 why not? not sure if it's widely supported enough to bother implementing, and also looks complicated, 
and not sure it even makes sense since anyone sniffing the line could always just do a replay attack and receive the peer list
TLS is a better solution to passive sniffing, mere obfuscation would help only if data is stored in a db for anaysis later, but still
any 'decrypted' obfuscation would be very damning evidence so, if this is important, then it makes more sense to seed the 
db with fake peers to contaminate the evidence preemtively-I could totally code this in maybe somehow

feature/bug Todo list:
-incomplete and complete should increment/decrement -partially done
-text/plain bencoded response -done
-error codes should be -done
1) text/plain -done
2) human readable -done
3) sent back as becoded responses -done
-figure out how to use github
-udp tracker support - beep 15 -Does Tornado even know what UDP is? maybeh
-add ipv6 support at some point -will get around to it eventually...
-Should return a response of peers picked randomly from peer pool for a torrent, will get around to it maybe...
-figure out how to read, store and respond with dns names...somehow. -No idea how to implement that, maybe just resolve first and store ip's? or does spec require sending back dns names...x.x
-will add obfuscation feature if I ever get that bored
-change db key from peer_id to ip/port combination to limit potential for abuse in untrustworthy enviornments
-maybe implement logging, maybe

-command line port/interval options port should be read from command line (with default to 9000), as should common settings
py3bt_tracker --help 
Syntax:
py3bt_tracker [port='9000'] [interval='240'] [obfuscation='off']
Example usage:
py3bt_tracker 
py3bt_tracker 6969
py3bt_tracker 9000 240
py3bt_tracker 6969 240 off
py3bt_tracker 8080 360 on

NOT on todo list:
scrape functionality -cuz ephemeral
private tracker feature - registered infohashes -cuz ephemeral
private tracker feature - registered peers -cuz stupid