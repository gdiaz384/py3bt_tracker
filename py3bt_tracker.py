#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
py3bt_tracker.py is an Ultra-low performance and poorly written standalone ephemeral tracker for torrents written in Python3 
with no scrape/statistics/ipv6/private features and runs on port 9000 (hardcoded).  py3bt_tracker.py is a python implementation of
the tracker portions of https://wiki.theory.org/BitTorrentSpecification /BitTorrent_Tracker_Protocol and /beeps using Tornado Web Server
Pick your License: GPL (any) or BSD (any) or MIT/Apache


google_define('ephemeral') #returns: adjective - lasting for a very short time -synonyms: transient, short-lived, brief


Usage guide:
1) double click on the .exe for your os
2) point your torrents to http://127.0.0.1:9000/announce 
where 127.0.0.1 is substituted for your IP obtained from ipconfig (for lans)

3) (if crazy enough to use this on the internets) public ip can be obtained from icanhazip.com, and remember to port forward
^-not intended use case but should still work maybe-^
Also note: Add as firewall exception if nag comes up

###stop reading now###
Current version: 1.0
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
"""

import hashlib
import urllib.parse
import binascii
import time

import os
#import random

#import os.path
#import sys
#import uuid
#import logging
#import math
#import optparse
#from optparse import OptionParser
#import re
#import base64

#import tornado
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httputil
#import tornado.escape
#import tornado.gen
#from tornado.concurrent import Future
from tornado.options import define, options, parse_command_line

define("port", default=9000, help="run on the given port", type=int)
define("debug", default=False, help="run in debug mode")

#configurable settings
tracker_port=9000
request_interval=40
#wipe_database every this many seconds, 3600 seconds = 1 hr
#database_lifespan=3600
database_lifespan=360
max_peers_in_response=30

#internal variables
#clients will receive an error if they request more than this (in seconds)
minimum_interval=int(request_interval/4)
consider_peers_dead_after=int(request_interval*1.8)
#clean_database_every=int(request_interval*200)
clean_database_every=int(request_interval*1.4)
#initalize random number gen
#random.seed()

#error [response] codes
#client query must be an http get request
invalid_http_get_request=100
missing_info_hash=101
missing_peer_id=102
missing_port=103
#must be 20 bytes long
invalid_info_hash=150
#must be 20 bytes long
invalid_peer_id=151
#tracker has a maximum peer response list and client requested more than that (30-50), send back a warning
invalid_num_want=152
#reserved for private trackers that don't auto-add new info_hashes
info_hash_not_found=200
#clients have a minimum interval between requests, return this error if a client asked again before allowed to
request_too_soon=500
unspecified_error=900


def bencode(encodeString,bentype):
    if bentype == 'string':
        return str(len(encodeString))+":"+encodeString
    if bentype == 'int':
        return "i"+str(encodeString)+"e"
    if bentype == 'list':
        return "l"+str(encodeString)+"e"
    if bentype == 'dictionary':
        return "d"+str(encodeString)+"e"
    #raise TypeError("bentype not supported:"+str(bentype))
    return

#bencode the static strings
#could also store these as global variables since they will never need to be rencoded, but w/e
bencoded_failure_string=bencode('failure reason','string')
bencoded_warning_string=bencode('warning message','string')
bencoded_interval_string=bencode('interval','string')
bencoded_min_interval_string=bencode('min interval','string')
bencoded_tracker_id_string=bencode('tracker id','string')
bencoded_complete_string=bencode('complete','string')
bencoded_incomplete_string=bencode('incomplete','string')
bencoded_peers_string=bencode('peers','string')
bencoded_peer_id_string=bencode('peer id','string')
bencoded_ip_string=bencode('ip','string')
bencoded_port_string=bencode('port','string')
bencoded_peers_string=bencode('peers','string')    
bencoded_failure_reason_string=bencode('failure reason','string')
bencoded_failure_code_string=bencode('failure code','string')


#returns a human redable bencoded response
#could implement retry feature here (beep 31), but like why...
def errorHandler(error_code):
    error_code=int(error_code)
    #needs to return
    #d14:failure reason32:invalid info hash and/or peer ide
    #so dictionary with a string object inside of it
    bencoded_specific_error_string='invalid'
    if error_code == 100:
        bencoded_specific_error_string=bencode('invalid_http_get_request','string')
    if error_code == 101:
        bencoded_specific_error_string=bencode('missing_info_hash','string')
    if error_code == 102:
        bencoded_specific_error_string=bencode('missing_peer_id','string')
    if error_code == 103:
        bencoded_specific_error_string=bencode('missing_port','string')
    if error_code == 150:
        bencoded_specific_error_string=bencode('invalid_info_hash','string')
    if error_code == 151:
        bencoded_specific_error_string=bencode('invalid_peer_id','string')
    if error_code == 152:
        bencoded_specific_error_string=bencode('invalid_num_want','string')
    if error_code == 200:
        bencoded_specific_error_string=bencode('info_hash_not_found','string')
    if error_code == 500:
        bencoded_specific_error_string=bencode('silly client is silly','string')
    if error_code == 900:
        bencoded_specific_error_string=bencode('unspecified_error','string')
    response=bencoded_failure_reason_string+bencoded_specific_error_string+bencoded_failure_code_string+bencode(error_code,'int')
    return bencode(response,'dictionary')


#info_hash and peer_id are URL encoded, so need to decode them
#1) if prefix present, seperate, and then decode rest of string into bytes
#2) if prefix not present, then just convert to bytes
#3) stored form is no longer url encoded and in hex ready to get printed to the console
#4) be sure to go from hex->binary again right before transmission
def decodeURL(url_string):
    raw_encoded_url_string=url_string
    #a length of 24 hex digits means 12 bytes, 12 bytes of hex + prefix = 20 bytes if prefix is 8 bytes long
    #35-3 (from hex to string conversion) is 32-8 =24, 24/2 = 12+8 = 20 bytes
    #Note: for peer_ids, the client version could be encoded into the binary form itself instead of shown raw (prefixed) in the url (Aria does this)
    #print("raw_encoded_url_string: "+str(raw_encoded_url_string))
    if raw_encoded_url_string.rfind('-') == -1:
        decoded_url_string=urllib.parse.unquote_to_bytes(raw_encoded_url_string)
        #print(str(decoded_url_string))
        if len(decoded_url_string) != 20:
            print(url_string)
            return 'error'
        temp=str(binascii.b2a_hex(decoded_url_string))
        #temp=str(decoded_url_string)
        #print(temp)
        decoded_url_string=temp[2:len(temp)-1]
    elif raw_encoded_url_string.rfind('-') != -1:
        prefix=raw_encoded_url_string[:raw_encoded_url_string.rfind('-')+1]
        #print(str(len(prefix))+prefix)
        peer_id_part=raw_encoded_url_string[raw_encoded_url_string.rfind('-')+1:]
        decoded_url_string=urllib.parse.unquote_to_bytes(peer_id_part)
        #print(str(decoded_url_string))
        if len(prefix)+len(decoded_url_string) != 20:
            print(url_string)
            return 'error'
        temp=str(binascii.b2a_hex(decoded_url_string))
        #temp=str(decoded_url_string)
        temp=temp[2:len(temp)-1]
        #print(temp)
        decoded_url_string=prefix+temp
    #print("decoded_url_string: "+decoded_url_string)
    return decoded_url_string


#returns a requestObject containing all arguments or a BT error for invalid data
def parseRawRequest(rawquery):
    #raw query
    query=rawquery
    #print("query: " + query)

    #print the number of items in uri
    queryItems=len(query.split("&"))
    #print("queryItems: " + str(queryItems))

    #place each item into a dictionary container
    client_rawRequestContainer=dict({})
    for i in range(queryItems):
        
        #this split will not work with invalid data, will http error 500 the server (internal server error)
        #print (str(i)+": "+(query.split("&")[i]))
        temp=query.split("&")[i]
        client_rawRequestContainer.update([temp.split("=")])

    #initalize temp variables
    client_info_hash="invalid"
    client_peer_id="invalid"
    client_port="invalid"
    client_uploaded="invalid"
    client_downloaded="invalid"
    client_left="invalid"
    client_compact="invalid"
    client_no_peer_id="invalid"
    client_event="invalid"
    client_ip="invalid"
    client_numwant="invalid"
    client_key="invalid"
    client_trackerid="invalid"
    client_corrupt="invalid"

    requestObject=({})

    if ('info_hash' in client_rawRequestContainer) == (True):
        client_info_hash=decodeURL(client_rawRequestContainer["info_hash"])
        if client_info_hash == 'error':
            print("error: info_hash is invalid")
            requestObject['error']=invalid_info_hash
            return requestObject
    else:
        print("error: info_hash not present")
        requestObject['error']=missing_info_hash
        return requestObject

    if ('peer_id' in client_rawRequestContainer) == (True):
        client_peer_id=decodeURL(client_rawRequestContainer["peer_id"])
        if client_peer_id == 'error':
            print("error: peer_id is invalid")
            requestObject['error']=invalid_peer_id
            return requestObject
    else:
        print("error: peer_id not present")
        requestObject['error']=missing_peer_id
        return requestObject

    if ('port' in client_rawRequestContainer) == (True):
        client_port=client_rawRequestContainer["port"]
    else:
        print("error: port not present")
        requestObject['error']=missing_port
        return requestObject

    if ('uploaded' in client_rawRequestContainer) == (True):
        client_uploaded=client_rawRequestContainer["uploaded"]
    else:
        pass
        #print("error: uploaded not present")

    if ('downloaded' in client_rawRequestContainer) == (True):
        client_downloaded=client_rawRequestContainer["downloaded"]
    else:
        pass
        #print("error: downloaded not present")

    if ('left' in client_rawRequestContainer) == (True):
        client_left=client_rawRequestContainer["left"]
    else:
        pass
        #print("error: left not present")

    if ('compact' in client_rawRequestContainer) == (True):
        client_compact=client_rawRequestContainer["compact"]
    else:
        pass
        #print("error: compact not present")

    if ('no_peer_id' in client_rawRequestContainer) == (True):
        client_no_peer_id=client_rawRequestContainer["no_peer_id"]
    else:
        pass
        #print("error: no_peer_id not present")

    if ('event' in client_rawRequestContainer) == (True):
        client_event=client_rawRequestContainer["event"]
    else:
        pass
        #print("error: event not present")

    if ('ip' in client_rawRequestContainer) == (True):
        client_ip=client_rawRequestContainer["ip"]
    else:
        pass
        #print("error: ip not present")
 
    if ('numwant' in client_rawRequestContainer) == (True):
        client_numwant=client_rawRequestContainer["numwant"]
    else:
        pass
        #print("error: numwant not present")

    if ('key' in client_rawRequestContainer) == (True):
        #client_key=decodeURL(client_rawRequestContainer["key"])
        client_key=client_rawRequestContainer["key"]
    else:
        pass
        #print("error: key not present")

    if ('trackerid' in client_rawRequestContainer) == (True):
        client_trackerid=client_rawRequestContainer["trackerid"]
    else:
        pass
        #print("error: trackerid not present")

    if ('corrupt' in client_rawRequestContainer) == (True):
        client_corrupt=client_rawRequestContainer["corrupt"]
    else:
        pass
        #print("error: corrupt not present")

    #print_client_info (debugging code)
    #print("client_info_hash: "+client_info_hash)
    #print("client_peer_id: "+client_peer_id)
    #print("client_port: "+client_port)
    #print("client_uploaded: "+client_uploaded)
    #print("client_downloaded: "+client_downloaded)
    #print("client_left: "+client_left)
    #print("client_compact: "+client_compact)
    #print("client_no_peer_id: "+client_no_peer_id)
    #print("client_event: "+client_event)
    #print("client_ip: "+client_ip)
    #print("client_numwant: "+client_numwant)
    #print("client_key: "+client_key)
    #print("client_trackerid: "+client_trackerid)
    #print("client_corrupt: "+client_corrupt)

    #so now need to return an object the values as keys
    #rebuild the dictionary!
    if client_info_hash != "invalid":
        requestObject["client_info_hash"]=client_info_hash
    if client_peer_id != "invalid":
        requestObject["client_peer_id"]=client_peer_id
    if client_port != "invalid":
        requestObject["client_port"]=client_port
    if client_uploaded != "invalid":
        requestObject["client_uploaded"]=client_uploaded
    if client_downloaded != "invalid":
        requestObject["client_downloaded"]=client_downloaded
    if client_left != "invalid":
        requestObject["client_left"]=client_left
    if client_compact != "invalid":
        requestObject["client_compact"]=client_compact
    if client_no_peer_id != "invalid":
        requestObject["client_no_peer_id"]=client_no_peer_id
    if client_event != "invalid":
        requestObject["client_event"]=client_event
    if client_ip != "invalid":
        requestObject["client_ip"]=client_ip
    if client_numwant != "invalid":
        requestObject["client_numwant"]=client_numwant
    if client_key != "invalid":
        requestObject["client_key"]=client_key
    if client_trackerid != "invalid":
        requestObject["client_trackerid"]=client_trackerid
    if client_corrupt != "invalid":
        requestObject["client_corrupt"]=client_corrupt
    return requestObject


class Database:
    def __init__(self):
        #create table containing global list of all known torrents
        #masterlist is a dictionary mapping md5 hashes of info_hash to table_objects (dictionary)
        #table objects are dictionaries that each contain 3 entries: complete (int), incomplete (int) and another dictionary
        #each dictionary of client data can be contains an md5 key which references a list containing: (peer_id, is_seed,ipv4_dottedstring,client_port,ip_in_hex,port_in_hex)
        global master_info_hash_table
        master_info_hash_table=dict({})
        #the idea is to wipe the database every hour or so for no particular reason
        global initialization_time
        initialization_time=int(time.time())
        #purge the database of stale peers
        global last_database_cleanup
        last_database_cleanup=int(time.time())

    def get_complete(self,info_hash):
        current_query=hashlib.md5()
        current_query.update(info_hash.encode('utf-8'))
        #return the value of complete of the referenced table
        return master_info_hash_table[current_query.hexdigest()]['complete']

    def get_incomplete(self,info_hash):
        current_query=hashlib.md5()
        current_query.update(info_hash.encode('utf-8'))
        #return the value of complete of the referenced table
        return master_info_hash_table[current_query.hexdigest()]['incomplete']

    #possible scenarios are: non-compact, non-compact no seeds, compact, compact no seeds
    #peer_List = tracker_db.get_peerList(current_client_info_hash,clientWantsNormalOrCompactResponse)
    #values are (hash,normal/compact)
    def get_peerList(self,client_info_hash,compactOrNormal='normal'):
        #itterate through that list to create the compact peer list of IPs/ports (in hex)
        #-each torrent_table (linked to an info_hash) contains peers+associated data (named after peer_id), an integer of incomplete (non seed peers), and completed (seeders)
        #create a new table using the table_id and an individual peer of type list containing (a peer_id,is_seed,address,client_port,address_hex, port_hex)

        current_query=hashlib.md5()
        current_query.update(client_info_hash.encode('utf-8'))
        info_hash_table=master_info_hash_table[current_query.hexdigest()]

        #build a peerlist
        #md5 hashes of the peer_id are used as keys
        info_hashes_table_keys=info_hash_table.keys()
        peer_list=[]
        if compactOrNormal.lower() == 'normal':
            for i in (info_hashes_table_keys):
                if (i != 'complete'):
                    if (i != 'incomplete'):
                        peer_list.append(info_hash_table[i][0])
                        peer_list.append(info_hash_table[i][2])
                        peer_list.append(info_hash_table[i][3])
        elif compactOrNormal.lower() == 'compact':
            for i in (info_hashes_table_keys):
                if (i != 'complete'):
                    if (i != 'incomplete'):
                        peer_list.append(info_hash_table[i][4])
                        peer_list.append(info_hash_table[i][5])
        #print(peer_list)
        return peer_list

    def updateClient(self,client_object,client_remote_ip):
        #use the client dictionary along with IP info to create a Peer
        #determine if a client_ip was used in the client_dictionary, if so use it, else use the IP from the connection instead
        #create table containing global list of all known torrents
        #masterlist is a dictionary mapping md5 hashes of info_hash to table_objects (dictionary)
        #table objects are dictionaries that each contain 3 entries: complete (int), incomplete (int) and another dictionary
        #each dictionary of client data can be contains an md5 key which references a list containing: (raw_peer_id, is_seed,ipv4_dottedstring,client_port,ipv4_hex,port_hex)

        global master_info_hash_table
        client_info_hash=hashlib.md5()
        client_info_hash.update(client_object['client_info_hash'].encode('utf-8'))
        client_peer_id=hashlib.md5()
        client_peer_id.update(client_object['client_peer_id'].encode('utf-8'))

        #could prolly handle this in a smarter way
        if 'client_left' in client_object:
            if (client_object['client_left'] == 0):
                is_seed=True
            elif (client_object['client_left'] != 0):
                is_seed=False
        else:
            is_seed=False

        #very easy to abuse this if peer_id.md5 hashes are used as keys, change db key to limit potential abuse
        if 'client_ip' in client_object:
            client_ip=client_object['client_ip']
        elif 'client_ip' not in client_object:
            client_ip=client_remote_ip

        client_port=client_object['client_port']

        #this returns a dictionary object (completed: int, incomplete: int,peer_id.md5 : client_list)
        #master_info_hash_table[client_info_hash.hexdigest()]
        #this returns the client's list (peer_id, is_seed,ipv4_dottedstring,client_port,ipv4_hex,port_hex)
        #master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()]
        #get the ip using master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()][2]

        #possible scenarios
        #if info_hash doesn't exist in master_table, create info_hash_table entry
        #then just always create a new peer (set the specified peer_id.md5 to that newpeer object)

        #if info_hash doesn't exist in master table, create info_hash table entry
        if client_info_hash.hexdigest() not in master_info_hash_table:
            #set the info_hash.md5 as the key to a new dictionary object
            master_info_hash_table[client_info_hash.hexdigest()]=self.createInfoHashTable()
            #if this new client is a seed, increment completes
            if (is_seed==True):
                #Note: this will "taint" the completed pool, so total "finished" now includes the inital seeder
                master_info_hash_table[client_info_hash.hexdigest()]['complete']=master_info_hash_table[client_info_hash.hexdigest()]['complete']+1
            #if the client is a new client and not a seed, increment the incomplete list
            elif (is_seed!=True):
                master_info_hash_table[client_info_hash.hexdigest()]['incomplete']=master_info_hash_table[client_info_hash.hexdigest()]['incomplete']+1

        #if the client has an event, and if that event is completed, increment seeders and decriment incomplete
        if 'client_event' in client_object:
            if (client_object['client_event'].lower()=='Completed'.lower()):
                master_info_hash_table[client_info_hash.hexdigest()]['complete']=master_info_hash_table[client_info_hash.hexdigest()]['complete']+1
                master_info_hash_table[client_info_hash.hexdigest()]['incomplete']=master_info_hash_table[client_info_hash.hexdigest()]['incomplete']-1

        #this has potential for abuse if a peer floods the tracker with a target ip using the same info hash and different peer_id's
        #will redirect the swarm to try to form connections to the target ip as a potential DDoS to that ip
        #or even to change the information of another peer in the db by finding out their peer id
        #potential fix: might be better to be hash the IP/port combination of the peer instead of the easily spoofable peer_id and use that as the db key instead
        #however, this is not relevant in a LAN enviornment and won't form enough connections per second for a lasting DoS due to the default behavior of end-user
        #clients to back off for extremely long periods after a failed attempt to contact a tracker so leave it, but change this for more optimized use on the internets
        #set the peer_id.md5 as the key to a new list object
        master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()]=self.createPeer(client_object['client_peer_id'],is_seed,client_ip,client_port)
        return


    #table objects are dictionaries that each contain 3 entries: complete (int), incomplete (int) and another dictionary
    def createInfoHashTable(self):
        return {'complete':0,'incomplete':0}


    #each peer list returns containing: (peer_id, is_seed,ip_address,client_port,ip_hex,port_hex,created time)
    #types are (rawbytes, bool, string, int, string, string)
    def createPeer(self,peer_id,is_seed,client_ip_address,client_port):
        #convert IP to hexadecimal format
        #if dealing with an ipv4 address, then count the octets
        #split into 4 sections
        #convert to hex, combine the hex pieces+hexed port
        if client_ip_address.count('.') == 3:
            #dealing with an ipv4 address
            #but, could also be dealing with a DNS name, but how to check for that...
            ip_list=client_ip_address.split('.')
            for i in (range(len(ip_list))):
                #print(str(ip_list[i]))
                ip_list[i]=hex(int(ip_list[i]))
                if len(ip_list[i]) != 4:
                    ip_list[i]=ip_list[i][:2]+'0'+ip_list[i][2:]
                #print(str(ip_list[i]))
            client_address_in_hex_no_port=str(ip_list[0])[2:]+str(ip_list[1])[2:]+str(ip_list[2])[2:]+str(ip_list[3])[2:]
        else:
            #dealing with an ipv6 address here, 
            #or a dns name without exactly 3 dots
            #might want to implement this at some point, maybeh
            address_no_port=client_ip_address

        #convert port to hex
        #print(client_port)
        client_port_in_hex=str(hex(int(client_port)))[2:]
        while len(client_port_in_hex) !=4:
            client_port_in_hex='0'+client_port_in_hex
        #print(ip_port_hex)

        #print(client_ip_address+":"+str(client_port))
        #print(client_address_in_hex_no_port+client_port_in_hex)

        #need to store these in hex
        return [peer_id, is_seed, client_ip_address, client_port, client_address_in_hex_no_port, client_port_in_hex, int(time.time())]

	#compare current time with last_peer_update, if peer exists, and if current time-last_peer_update < minimum_interval then client is silly
    def clientIsSilly(self,client_object):
        #print('pie')
        #if client has a recognized event, then it's okay
        if 'client_event' in client_object:
            if client_object['client_event'].lower() == 'Started'.lower():
                return False
            if client_object['client_event'].lower() == 'Stopped'.lower():
                return False
            if client_object['client_event'].lower() == 'Completed'.lower():
                return False
        global master_info_hash_table
        client_info_hash=hashlib.md5()
        client_info_hash.update(client_object['client_info_hash'].encode('utf-8'))
        client_peer_id=hashlib.md5()
        client_peer_id.update(client_object['client_peer_id'].encode('utf-8'))
        #print('pie2')
        if client_info_hash.hexdigest() in master_info_hash_table:
            if client_peer_id.hexdigest() in master_info_hash_table[client_info_hash.hexdigest()]:
                last_peer_update=master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()][6]
                if int(time.time())-last_peer_update < minimum_interval:
                    #print('silly client found')
                    return True
        return False

    #reset data on all tracked torrents
    def checkDB(self):
        global last_database_cleanup
        global master_info_hash_table

        #could also remove stale peers here
        #would make more sense to check the db every say 10 min or so (twice the request interval), instead of checking every time a client makes a request
        #itterate through hashes, for each hash check every peer's last_request time, make sure not empty
        #find all the current keys in the master table
        #for each key (info hashes)
            #find all the client keys (peer ids) in the table
            #for each peer id key
                #set the completed count for that table to 0
                #set the incomplete count to 0 for that table
                #if the client hasn't checked in, remove it
                #if the client is valid, then increment either incomplete or complete
        if len(master_info_hash_table) == 0:
            return
        #print(master_info_hash_table)
        #info_hash_keys=master_info_hash_table.keys()
        info_hash_keys=list(master_info_hash_table)
        #print(info_hash_keys)
        for i in (info_hash_keys):
            #peer_id_keys=master_info_hash_table[i].keys()
            peer_id_keys=list(master_info_hash_table[i])
            #print(peer_id_keys) #all the peers in a torrent's info_hash table+ complete/incomplete
            new_complete=0
            new_incomplete=0
            #remove_list=[]
            for k in (peer_id_keys):
                if k == 'complete' :
                    continue
                if k == 'incomplete':
                    continue
                #print(master_info_hash_table[i][k])  #the data of a peer in a torrent's info_hash table+ complete/incomplete
                if int(time.time())-master_info_hash_table[i][k][6] > consider_peers_dead_after:
                    #remove_list.append(k)
                    print(master_info_hash_table[i][k])
                    del master_info_hash_table[i][k]
                    print('peer removed from info hash table')
            #print(master_info_hash_table[i])  #the data of an info_hash table
            #print(remove_list)
            #for k in (remove_list):
                #print(master_info_hash_table[i][k][0])

            #print('peer removed from info hash table')
            #now that the stale peers have been removed, can modify the remaining seeds/non-seed peers more accurately
            #peer_id_keys=master_info_hash_table[i].keys()
            peer_id_keys=list(master_info_hash_table[i])
            #print(peer_id_keys) #print updated (slim) list of entries in an info_hash table
            for k in (peer_id_keys):
                if k == 'complete' :
                    continue
                if k == 'incomplete':
                    continue
                #print(master_info_hash_table[i][k])
                if master_info_hash_table[i][k][1] == True:
                    new_complete=new_complete+1
                elif master_info_hash_table[i][k][1] == False:
                    new_incomplete=new_incomplete+1
                else:
                    print('error determining client seed status')
            master_info_hash_table[i]['complete']=new_complete
            master_info_hash_table[i]['incomplete']=new_incomplete

        last_database_cleanup=int(time.time())

        #info_hash_keys=master_info_hash_table.keys()
        info_hash_keys=list(master_info_hash_table)
        #print(info_hash_keys)
        for i in (info_hash_keys):
            if len(master_info_hash_table[i]) == 2:
                del master_info_hash_table[i]
        return

    #remove data on a particular torrent (remove each associated peer from it first or not necessary?)
    def deleteTable(self,info_hash):
        global master_info_hash_table
        info_hash=hashlib.md5()
        info_hash.update(client_object['client_info_hash'].encode('utf-8'))
        #check to make sure it exists, then delete it, if it does't exist return an error
        if info_hash.hexdigest() in master_info_hash_table:
            del master_info_hash_table[peer_info_hash.hexdigest()]
        elif info_hash.hexdigest() not in master_info_hash_table:
            print("could not find specified info hash in master table when asked to remove it")
            return 'error'

    #deletes entry (of type list) from the associated table (of type dict)
    def removePeerEntry(self,peer_id,peer_info_hash):
        global master_info_hash_table
        peer_info_hash=hashlib.md5()
        peer_info_hash.update(client_object['client_info_hash'].encode('utf-8'))
        peer_id=hashlib.md5()
        peer_id.update(client_object['client_peer_id'].encode('utf-8'))
        #check to make sure it exists, then delete it, if it does't exist return an error
        if peer_info_hash.hexdigest() in master_info_hash_table:
            if peer_id.hexdigest() in master_info_hash_table[peer_info_hash.hexdigest()]:
                del master_info_hash_table[peer_info_hash.hexdigest()][peer_id.hexdigest()]
            elif peer_id.hexdigest() not in master_info_hash_table[peer_info_hash.hexdigest()]:
                print("could not find specified peer in the torrent's table when asked to remove a peer")
                return 'error'
        elif peer_info_hash.hexdigest() not in master_info_hash_table:
            print("could not find specified info hash in master table when asked to remove a peer")
            return 'error'


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        client_uri = self.request.uri
        client_path = self.request.path
        client_query = self.request.query
        client_remote_ip = self.request.remote_ip
        client_url = self.request.full_url()
        client_uri_dictionary = self.request.arguments

        global tracker_db

        client_request_dictionary = parseRawRequest(client_query)
        #print("pie")
        #print("client_request_dictionary['client_left']")
        #print(client_request_dictionary['client_left'])
        #print(client_request_dictionary)

        #check for returned error
        #requestObject["error"]=missing_info_hash
        #request should be a human readable string, not an error code according to "offical" 1.0 spec
        if 'error' in client_request_dictionary:
            #self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Type', 'text/plain')
            bencoded_error=errorHandler(client_request_dictionary['error'])
            self.write(bencoded_error)
            self.flush()
            #self.finish()
            return

        #if not errored out then check to see if peer already exists in db, if so, check to make sure request didn't come too soon
        if tracker_db.clientIsSilly(client_request_dictionary) == True:
            #print('pie3')
            #self.set_header('Content-Type', 'application/octet-stream')
            self.set_header('Content-Type', 'text/plain')
            bencoded_error=errorHandler(request_too_soon)
            self.write(bencoded_error)
            self.flush()
            #self.finish()
            return

        #purge the database if lifespan has expired
        global initialization_time
        global master_info_hash_table
        if int(time.time())-initialization_time > database_lifespan:
            master_info_hash_table=dict({})
            initialization_time=int(time.time())
            print('database erased')

        #update database with new peer if client wasn't silly
        #print('pie4')
        #db.update(client_object,client_remote_ip)
        tracker_db.updateClient(client_request_dictionary,client_remote_ip)

        #if it hasn't happned in a while, cleanup the db of stale data so it doesn't get returned to the peer
        global last_database_cleanup
        if int(time.time())-last_database_cleanup > clean_database_every:
            tracker_db.checkDB()

        #now just need to actually respond back

        current_client_info_hash=client_request_dictionary['client_info_hash']
        #print(client_request_dictionary)
        clientWantsNormalOrCompactResponse='normal'
        #retrieve relevant peerList from database
        if 'client_compact' in client_request_dictionary:
            #client_request_dictionary['client_compact']=0
            if client_request_dictionary['client_compact'] == '1':
                #print('compact client request detected')
                clientWantsNormalOrCompactResponse='compact'

        #get peerlist from database
        #get_peerList(info_hash,compact status as normal or minimal), returns a peerlist
        peer_List = tracker_db.get_peerList(current_client_info_hash,clientWantsNormalOrCompactResponse)
        #could maybe, retrieve non-seeder list to return to a seeder
        #or could just return the raw peer list for native parsing or fully parse it and return only the finished peer list
        #instead of preparsing it in the function and finishing the parsing in main (architecture not pretty as-is)
        #get_peerList(current_client_info_hash,normal)
        #get_peerList(current_client_info_hash,compact)
        #or like, remove the current client from the list when sending it back to them
        #or like, specify a maximum number of peers to retrieve

        #retrieve torrent statistics
        complete=tracker_db.get_complete(current_client_info_hash)
        incomplete=tracker_db.get_incomplete(current_client_info_hash)

        client_object=client_request_dictionary
        #self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Type', 'text/plain')
        #def generateClientResponse(client_object,peer_List,complete,incomplete):
        #parse compact,no_peer_id (for dict responses only), numwant for a requestObject
        #interval, min interval (optional), tracker id (optional), complete, incomplete, (peers(dictionary) or peers(binary))
        #optional, if current client_object is a seed, then could strip out other seeds from the response
        #print("pie1")

        #bencode the values
        #print(request_interval)
        #print(minimum_interval)
        #print(complete)
        #print(incomplete)
        bencoded_interval_value=bencode(request_interval,'int')
        bencoded_min_interval_value=bencode(minimum_interval,'int')
        bencoded_complete_value=bencode(complete,'int')
        bencoded_incomplete_value=bencode(incomplete,'int')
        #print(bencoded_complete_value)

        #print(bencoded_complete_string)
        #print(bencoded_complete_value)
        #print(bencoded_incomplete_string)
        #print(bencoded_incomplete_value)
        #print(bencoded_interval_string)
        #print(bencoded_interval_value)
        #print(bencoded_min_interval_string)
        #print(bencoded_min_interval_value)

        #redundant code (from above's clientWantsNormalOrCompactResponse)
        if 'client_compact' in client_object:
            if client_object['client_compact'] == '1':
                client_requested_compact=True
            else:
                client_requested_compact=False
        else:
            client_requested_compact=False

        #count the number available, that's the total_available. then pick whichever is lowest total_available, max_peers_in_response, or numwant 
        if 'client_numwant' in client_object:
            if int(client_object['client_numwant']) < max_peers_in_response:
                client_max_response_count=int(client_object['client_numwant'])
            else:
                client_max_response_count=max_peers_in_response
        else:
            client_max_response_count=max_peers_in_response

        #output the inital bencoded dictionary that will be used for the entire response
        response_global=bencoded_complete_string+bencoded_complete_value+bencoded_incomplete_string+bencoded_incomplete_value+bencoded_interval_string+bencoded_interval_value+bencoded_min_interval_string+bencoded_min_interval_value+bencoded_peers_string
        self.write('d')
        self.write(response_global)

        #now to respond back with the peer list in the format the client requested
        #okay now to figure out how to output the peer list as (dictionary w/peer_id , dictionary w/o peer_id, compact)
        #if raw_encoded_url_string.rfind('-') == -1:
        #binascii.a2b_hex
        #for normal dictionary responses, if the peer list is selected then need to send it out as bytes
        #peer list can contain -ut221-[hexdigits]  or [hexdigits], so detect and encode appropriately
        #for compact responses, the [compacted_peer_list_in_hex] needs to be sent out as bytes, len(works normally)
        #compact responses take the form: 5:peers48:[binary]  and are embedded as a key into the root dictionary of the bencoded response, 
        #not sure if the 48 is the length of the binary "string" in binary or the length of the binary "string" in hex, (assume it's binary first)

        #output for dictionary type:
        #dictionary peer list (multiple strings + bitstreams, difficult to pass back-forth through messages)
        #dictionary w/o peer list 1 string
        #output for compact type:
        #only 1 type but needs: 1string+1bitstream (peers) (can append e at the end)
        if client_requested_compact == False:
            total_available=int(len(peer_List)/3)
            if total_available < client_max_response_count:
                response_count=total_available
            elif total_available >= client_max_response_count:
                response_count=client_max_response_count

            #for normal responses need to know if clients don't want a peer ID included in the response
            if 'client_no_peer_id' in client_object:
                if client_object['client_no_peer_id'] == '1':
                    #if client selected no peer_id, then very easy to respond
                    #build string normally and send it, then return
                    for i in range (len(peer_List)):
                        #if parsing the last item in a pair, assume that it's a port number and bencode it as an int, else assume it's a string (peer_id and ip)
                        if i%3==2:
                            peer_List[i]=bencode(peer_List[i],'int')
                        elif i%3==1:
                            peer_List[i]=bencode(str(peer_List[i]),'string')
                    #now every item other than peer id's have been bencoded
                    #print("peer_List: "+str(peer_List))

                    bencoded_peer_array=[]
                    for i in range (0,len(peer_List),3):
                        bencoded_peer_array.append(bencode(bencoded_ip_string+str(peer_List[i+1])+bencoded_port_string+str(peer_List[i+2]),'dictionary'))

                    bencoded_peer_list=str(bencoded_peer_array[0])
                    for i in range (response_count):
                        if i!=0:
                            bencoded_peer_list=bencoded_peer_list+bencoded_peer_array[i]
                    bencoded_peer_list=bencode(bencoded_peer_list,'list')
                    self.write(bencoded_peer_list)
                    self.write('e')
                    self.flush()
                    #self.finish()
                    return

            #okay so client did not request a compact response and did not say no_peer_id's...let's do this
            #for normal response peer_list is (peer_id,ip, port,peer_id,ip, port,peer_id,ip, port,peer_id,ip, port...n), so multiples of 3
            #need to write prefix
            #need to cycle through peerlist, then
            #determine how many peers are needed (response_count)
            #then loop through every third peer item
                #process i, i+1 and i+2, writing each to output
                #bencode the port/ip and convert
                #write contents
                #(order of dictionary items not important)
            #go to next peer
            #when done, need to write postfix

            self.write('l')
            #this needs a different algorithm to incorporate response_count and to cycle properly
            i=0  #increment by 1 each loop, keep going for this many total loops
            k=0 #increment by 3 each loop, use this to reference the peer_List
            #for normal response peer_list is (peer_id,ip, port,peer_id,ip, port,peer_id,ip, port,peer_id,ip, port...n), so multiples of 3, starting with peer id then -> ip -> port
            while i < response_count:
                self.write('d')
                self.write(bencoded_port_string)
                peer_List[k+2]=bencode(peer_List[k+2],'int')
                self.write(peer_List[k+2])

                self.write(bencoded_ip_string)
                peer_List[k+1]=bencode(str(peer_List[k+1]),'string')
                self.write(peer_List[k+1])

                self.write(bencoded_peer_id_string)
                #spec says that peer_id's must be 20 bytes, assume that's true here (since this should have been checked before being input into db)
                self.write('20:')
                #need to find out of peer id is in ut format, binary format or shadow's format
                if peer_List[k].rfind('-') == -1:
                    #if there is no -, then assume it's pure hex, so just decode and send
                    peer_List[k]=binascii.a2b_hex(peer_List[k])
                    self.write(peer_List[k])
                else:
                    #if there are -'s then need to separate into two parts
                    #write the first part
                    #decode the second part
                    #write the second part (don't save)
                    peer_id_prefix=peer_List[k][:peer_List[k].rfind('-')+1]
                    self.write(peer_id_prefix)
                    peer_id_binary_part=peer_List[k][peer_List[k].rfind('-')+1:]
                    peer_id_binary_part=binascii.a2b_hex(peer_id_binary_part)
                    self.write(peer_id_binary_part)
                self.write('e') #close peer dictionary entry
                i=i+1
                k=k+3
                    
            self.write('e') #close list entry
            #when done, need to write postfix
            self.write('e') #final postfix, close root dictionary
            self.flush()
            #self.finish()
            return

        #so client requested a compact response
        #compact responses take the form: 5:peers48:[binary] and are embedded as a key into the root dictionary of the bencoded response, (so there's a post fix "e" after the peers list)
        #not sure if the 48 is the length of the binary "string" in binary or the length of the binary "string" in hex, (assume it's binary first)
        if client_requested_compact == True:
            #for compact response peer_list is (ip_in_hex, port_in_hex,ip_in_hex, port_in_hex,ip_in_hex, port_in_hex,...n), so multiples of 2
            total_available=int(len(peer_List)/2)
            if total_available < client_max_response_count:
                response_count=total_available
            elif total_available >= client_max_response_count:
                response_count=client_max_response_count

            #combine the ip/port strings with values, every 3 is 1 dictionary
            peer_array=[]
            for i in range (0,len(peer_List),2):
                peer_array.append(peer_List[i]+peer_List[i+1])

            peer_list_in_hex=peer_array[0]
            for i in range (response_count):
                if i!=0:
                    peer_list_in_hex=peer_list_in_hex+peer_array[i]

            peer_list_in_binary=binascii.a2b_hex(peer_list_in_hex)
            peer_list_length=str(len(peer_list_in_binary))

            #   48:[binary]  with a trailing e
            self.write(peer_list_length)
            self.write(':')
            self.write(peer_list_in_binary)
            self.write('e')
            self.flush()
            return

        print("unspecified error")
        self.flush()
        return

        #old code that doesn't do anything anymore (remove it at some point)
        #bencoded_peer_list=bencode(benscoded_peer_list,'string')
        #bencoded_peer_list=bencode(bencoded_peer_list,'list')
        #bencoded_peers_string_and_list=bencode('peers'+bencoded_peer_list,'string')
        #response=bencoded_complete_string+bencoded_complete_value+bencoded_incomplete_string+bencoded_incomplete_value+bencoded_interval_string+bencoded_interval_value+bencoded_min_interval_string+bencoded_min_interval_value+bencoded_peers_string_and_list
        #response=bencoded_complete_string+bencoded_complete_value+bencoded_incomplete_string+bencoded_incomplete_value+bencoded_interval_string+bencoded_interval_value+bencoded_min_interval_string+bencoded_min_interval_value+bencoded_peers_string+bencoded_peer_list

        #print(bencoded_peer_list)
        #response=bencode(response,'dictionary')
        #d8:completei0e10:incompletei1e8:intervali600e5:peersld2:ip9:127.0.0.17:peer id20:-UT2210-¹b,sÃÆQ<u•–4:porti18584eeee
        #current response returns hex digits for the peer id, not the binary form, might want to change that
        #print("response: "+response)
        #return response
        #def generateClientResponse(client_object,peerList)
        #response=generateClientResponse(client_request_dictionary,peer_List,complete,incomplete)
        #self.write(response)
        #self.finish()

        #debugging code
        #client_info_hash = self.get_argument("info_hash")
        #client_peer_id = self.get_argument("peer_id")
        #client_port = self.get_argument("port")
        #client_uploaded = self.get_argument("uploaded")
        #print("client_uri_dictionary: " + str(client_uri_dictionary))
        #print(client_uri_dictionary['info_hash'])
        #print("client_port: " + client_port)
        #self.write("client_uri: " + str(client_uri) + "<br>")
        #self.write("client_path: " + str(client_path) + "<br>")
        #self.write("client_query: " + str(client_query) + "<br>")


class InvalidRequest(tornado.web.RequestHandler):
    def get(self):
        #self.set_header('Content-Type', 'application/octet-stream')
        #self.set_header('Content-Type', 'text/plain')
        #should prolly just send a 404 or access restricted error instead, comment out header type if doing that
        self.send_error(403)
        self.flush()
        #self.finish()

def main():
    parse_command_line()
    global tracker_db
    tracker_db = Database()
    #the only valid request is /announce
    #in order to use /scrape add an entry
    #or to respond to anything /announce* like /announce.php switch which line is commented
    app = tornado.web.Application([
            (r"/announce.*", MainHandler),
            #(r"/announce", MainHandler),
			(r"/.*", InvalidRequest),
            ])
    app.listen(tracker_port)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()