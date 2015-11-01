#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Description:
py3bt_tracker is a cross-platform standalone ephemeral tracker for torrents written in Python3.
The development emphasis is on zero-configuration "just works" software.
Currently implemented using a multidimentional array in memory and the Tornado Web Server (http).

google_define('ephemeral') #returns: adjective - lasting for a very short time -synonyms: transient, short-lived, brief

Current version: 1.0.0-rc2

###stop reading now###

Version 1 Todo list:
-incomplete and complete should increment/decrement -partially done, need to improve "update" code still  -in progress
-add ipv6 support at some point -will get around to it eventually... -in progress
-Should return a response of peers picked randomly from peer pool for a torrent, will get around to it eventually... -in progress
-figure out how to read, store and respond with dns names...somehow. -No idea how to implement that, maybe just resolve first and store ip's? or does spec require sending back dns names...x.x -in progress
-maybe implement logging, maybe 
-Version 2 Todo list:
-add required response delay before giving out peers or adding to main peer db to raise the bar on potential for abuse in untrustworthy enviornments
-improve performance for use in WANs (production quality code optimizations + fully async web server)
-also add obfuscation feature (using the ipaddress library), and make wipe old peers/db optional (essentially have a reliably mode and a screwy mode filled with wrong info)
-add udp tracker support (beep 15) -Does Tornado even know what UDP is? maybeh, or just import udp support from another project
"""

import urllib.parse #parse urls
import hashlib        #create md5 hashes from info_hash peer_id's to use as lookup keys in db
import binascii       #convert from hex/binary to ascii and back
import time             #keep track of when to erase db and peers
import socket       #required for dns lookups, used to get ip from dns name if one is specified using &ip= parameter
import ipaddress   #used to add ipv6 support
import argparse     #used to add command line options

import os #not sure if need this actually
import random #used to shuffle peers list before response, and seems like it would be useful for maybe generating fake peers

#tornado stuff
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httputil
#from tornado.concurrent import Future
#from tornado.options import define, options, parse_command_line

#configurable settings
tracker_port=6969
request_interval=1     #in minutes
#wipe_database every this many seconds, 3600 seconds = 1 hr
#database_lifespan=2592000   #30 days
#database_lifespan=3600          #1 hour
database_lifespan=360              #6 minutes
max_peers_in_response=50
enable_obfuscation=False

#add command line options
command_Line_parser=argparse.ArgumentParser()
command_Line_parser.add_argument("-p", "--port", help="select which port to run on (int)",default=tracker_port,type=int)
command_Line_parser.add_argument("-i", "--client_request_interval", help="how often should clients check the server (min)",default=request_interval,type=int)
command_Line_parser.add_argument("-o", "--enable_obfuscation", help="seed database with random IP addresses", action="store_true")

#parse command line settings
command_Line_arguments=command_Line_parser.parse_args()

tracker_port=command_Line_arguments.port
#print("specified port: " + str(tracker_port))

request_interval=command_Line_arguments.client_request_interval
#print("interval in min: " + str(request_interval))
request_interval=request_interval*60
#print("interval in seconds: " + str(request_interval))

if command_Line_arguments.enable_obfuscation:
    enable_obfuscation=True
#print("enable_obfuscation: " + str(enable_obfuscation))

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
bencoded_peers6_string=bencode('peers6','string')  #so conflicting info: should it be peers6 (beep 7) or peers_ipv6 (bt_tracker_protocol)?
bencoded_failure_reason_string=bencode('failure reason','string')
bencoded_failure_code_string=bencode('failure code','string')


#returns a human readable failure response as a bencoded dictionary
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
    client_ipv4="invalid"
    client_ipv6="invalid"

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

    if ('downloaded' in client_rawRequestContainer) == (True):
        client_downloaded=client_rawRequestContainer["downloaded"]

    if ('left' in client_rawRequestContainer) == (True):
        client_left=client_rawRequestContainer["left"]

    if ('compact' in client_rawRequestContainer) == (True):
        client_compact=client_rawRequestContainer["compact"]

    if ('no_peer_id' in client_rawRequestContainer) == (True):
        client_no_peer_id=client_rawRequestContainer["no_peer_id"]

    if ('event' in client_rawRequestContainer) == (True):
        client_event=client_rawRequestContainer["event"]

    if ('ip' in client_rawRequestContainer) == (True):
        client_ip=client_rawRequestContainer["ip"]
 
    if ('numwant' in client_rawRequestContainer) == (True):
        client_numwant=client_rawRequestContainer["numwant"]

    if ('key' in client_rawRequestContainer) == (True):
        client_key=urllib.parse.unquote(client_rawRequestContainer["key"])
        #client_key=client_rawRequestContainer["key"]

    if ('trackerid' in client_rawRequestContainer) == (True):
        client_trackerid=client_rawRequestContainer["trackerid"]

    if ('corrupt' in client_rawRequestContainer) == (True):
        client_corrupt=client_rawRequestContainer["corrupt"]

    if ('ipv4' in client_rawRequestContainer) == (True):
        #ipv4 addresses should not be url encoded, only ipv6, but w/e
        client_ipv4=urllib.parse.unquote(client_rawRequestContainer["ipv4"])

    if ('ipv6' in client_rawRequestContainer) == (True):
        client_ipv6=urllib.parse.unquote(client_rawRequestContainer["ipv6"])
        
    #print client_info (debugging code)
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
    #print("client_ipv4: "+client_ipv4)
    #print("client_ipv6: "+client_ipv6)

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
    if client_ipv4 != "invalid":
        requestObject["client_ipv4"]=client_ipv4
    if client_ipv6 != "invalid":
        requestObject["client_ipv6"]=client_ipv6
    return requestObject


class Database:
    def __init__(self):
        #create table containing global list of all known torrents
        #masterlist is a dictionary mapping md5 hashes of info_hash to table_objects (dictionary)
        #table objects are dictionaries that each contain 3 entries: complete (int), incomplete (int) and another dictionary
        #each dictionary of client data can be contains an md5 key which references a list containing: (peer_id, is_seed,ipv4_dottedstring,client_port,ip_in_hex,port_in_hex)
        global master_info_hash_table
        master_info_hash_table=dict({})
        #the idea is to wipe the database every hour or so (for no particular reason)
        global initialization_time
        initialization_time=int(time.time())
        #needed to purge the database of stale peers every once in a while
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
    def get_peerList(self,client_info_hash):
        #itterate through that list to create the peer list of IPs/ports

        current_query=hashlib.md5()
        current_query.update(client_info_hash.encode('utf-8'))
        info_hash_table=master_info_hash_table[current_query.hexdigest()]

        #build a peerlist
        #md5 hashes of the peer_id are used as keys
        info_hashes_table_keys=info_hash_table.keys()
        peer_list=[]
        for i in (info_hashes_table_keys):
            if (i != 'complete'):
                if (i != 'incomplete'):
                    peer_list.append(info_hash_table[i])
        #print(peer_list)
        return peer_list

    def updateClient(self,client_object,client_remote_ip):
        #Todo: update this very old function to handle updates better, should not just override existing peers and also
        #take into account previously existing seed status, new status and events and factor all of that into updated incomplete/complete numbers
        #for the relevant info_hash

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

        #client can:
        #ip (4)
        #ip (6)
        #ip (4), ipv6
        #ip (4), ipv4, ipv6
        #ip (6), ipv4
        #ip (6), ipv4, ipv6

        #initalize ipv4 and ipv6 addresses to invalid
        ipv4address='invalid'
        ipv6address='invalid'
        #check for ipv4 and ipv6
        if 'ipv4' in client_object:
            ipv4address=client_object['ipv4']
        if 'ipv6' in client_object:
            ipv6address=client_object['ipv6']

        #strip out port if present, 
        #uh..how to do that for ipv4...does it come in as ipv4:port or [ipv4]:port ?
        #just do both
        if ipv4address.count(']') != 0:
            temp_list=urllib.parse.unquote(ipv4address).split(']')
            ipv4address=list1[0][1:len(list1[0])+1]
        if ipv4address.count(':') != 0:
            temp_list=urllib.parse.unquote(ipv4address).split(':')
            ipv4address=list1[0][0:len(list1[0])+1]

        #strip out port ipv6 port
        if ipv6address.count(']') != 0:
            temp_list=urllib.parse.unquote(ipv6address).split(']')
            ipv6address=list1[0][1:len(list1[0])+1]
        #now have ipv4, ipv6, raw ip and ip (argument)

        #if &ip= specified (of undetermined version), that takes precidence over raw ip used to connect to server
        if 'client_ip' in client_object:
            client_ip=client_object['client_ip']
            #spec says client may send a DNS name in the &ip= argument, 
            #if dns name, then need to convert it to raw ip form
            #can actually just do a blind dns lookup on an address (ip or dns) and it will always return the ip, could detect it as a raw ip or dns name somehow maybe
            client_ip=socket.getaddrinfo(client_ip,80)[0][4][0]
            #the above code means "do a dns lookup on client_ip and place the result of that lookup into an object" (a random port is required cuz w/e)
            #that object is a list filled all of the returned dns entries. each list entry is another list where each entry is a tuple (value pairs)
            #[0] enter the first list object and go to the 4th tuple [4] and then fetch the first item in that tuple [0]
        elif 'client_ip' not in client_object:
            client_ip=client_remote_ip

        #ipv6 addresses sometimes have the scope % padded at the end, need to strip that out
        if client_ip.count('%') != 0:
            client_ip=client_ip[:client_ip.rfind('%')]
        
        #then check which version client ip is
        client_ip_object=ipaddress.ip_address(client_ip)
        #if it's version 4, replace ipv4 address
        if str(client_ip_object.version)=='4':
            ipv4address=str(client_ip_object)
        #from spec: "In case of IPv6 address [...] it[, an &ip= argument,] indicates only that client can communicate via IPv6."
        #so does that mean ignore it completely or what?
        #if it's version 6, replace ipv6 address
        if str(client_ip_object.version)=='6':
            ipv6address=str(client_ip_object)

        #ipv6 is now determined, and is a string, if not invalid, need to expand to full hex
        if ipv6address != 'invalid':
            ipv6address=str(ipaddress.ip_address(ipv6address).exploded)

        #but! should not respond back with 'invalid' addresses in final response, so check for 'invalid' string

        #always use the port from the &port= option, the ports included in the addresses above that were stripped out have no legitimate use cases
        client_port=client_object['client_port']

        #this returns a dictionary object (completed: int, incomplete: int,peer_id.md5 : client_list)
        #master_info_hash_table[client_info_hash.hexdigest()]
        #this returns the client's list (peer_id, is_seed,ipv4_dottedstring,client_port,ipv4_hex,port_hex)
        #master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()]
        #get the ip using master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()][2]

        #client could be incomplete and already in the db
        #client could be incomplete and not in the db
        #client could be a seeder and already in the db
        #client could be a seeder and not already in the db

        #possible scenarios
        #if info_hash doesn't exist in master_table, create info_hash_table entry
        #then just always create a new peer (set the specified peer_id.md5 to that newpeer object)

        #if info_hash doesn't exist in master table, create info_hash table entry
        if client_info_hash.hexdigest() not in master_info_hash_table:
            #set the info_hash.md5 as the key to a new dictionary object
            master_info_hash_table[client_info_hash.hexdigest()]=self.createInfoHashTable()

        #if client doesn't exists in the info_hash table, then add+1 to the list of seeders/incomplete peers        
        if client_peer_id.hexdigest() not in master_info_hash_table[client_info_hash.hexdigest()]:
            #if this new client is a seed, increment completes
            if (is_seed==True):
                master_info_hash_table[client_info_hash.hexdigest()]['complete']=master_info_hash_table[client_info_hash.hexdigest()]['complete']+1
            #if the client is a new client and not a seed, increment the incomplete list
            elif (is_seed!=True):
                master_info_hash_table[client_info_hash.hexdigest()]['incomplete']=master_info_hash_table[client_info_hash.hexdigest()]['incomplete']+1

        #if the client has an event, and if that event is completed, increment seeders and decriment incomplete
        if 'client_event' in client_object:
            if (client_object['client_event'].lower()=='Completed'.lower()):
                master_info_hash_table[client_info_hash.hexdigest()]['complete']=master_info_hash_table[client_info_hash.hexdigest()]['complete']+1
                master_info_hash_table[client_info_hash.hexdigest()]['incomplete']=master_info_hash_table[client_info_hash.hexdigest()]['incomplete']-1

        #so how to uniquely identify a peer?
        #currently this has potential for abuse if a peer gives the tracker a target ip using the same info hash and a fake &ip= value
        #will redirect the swarm to try to form connections to the target ip as a potential DDoS to that ip
        #or even to change the information of another peer in the db by finding out their peer id
        #potential fix: might be better to be hash the IP/port combination of the peer instead of the easily spoofable peer_id and use that as the db key instead
        #however, the raw client source port is random, and binding that could lead to each client having multiple entries and the destination post is spoofable
        #essentially, the issue is that detecting unique peers via raw information is very unreliable due to NAT and load balancers situations
        #and yet and information given by the client itself is spoofable, therefore no solution exists for identifying clients that doesn't break *something*
        #so multiple users behind the same NAT can't use the tracker or a single user (possibly malicious) could enter fake data into the DB
        #So no good options available soft approaches are a hueristic analysis of DB or de-duplicate entries, or have tracker connect to client to verify connectivity (NO)
        #could also give clients keys when they first connect and at least require clients to respond with it back. But that doesn't solve the initial connection being added to the db

        #could blindly add clients to the DB initially, but give them an extremely low required interval to check back in, say 1 min (any maybe respond back with an empty peer list)
        #only legitimate clients would respond back, say in a minute or two, and could respond a 2nd time with an updated (longer) interval
        #so how to identify if the client has spoken to the tracker before?, hash a client generated key + a tracker instance ID
        #key can be client generated, stored server or server generated, then just hash the key+tracker instance id and send that to the client as a trackerid
        #the client responds back with a peer id and a tracker id, and maybe a key, if the client has spoken before, a key will be present in their peer_id entry
        #then take that stored key and hash it with the tracker instance id, they are a legitimate client if the resulting hash matches the one reported back by the client
        #if they are not, take the key they provided (or generate one) and store it, and send back a new trackerid for them to return (try again basically)
        #then after they have responded back, add clients to a second list of "verified" peers (those who have at least responded back), and give them the peer list
        #for MITM exploits that try to find the swarm's peer_ids or keys, just run the server over TLS~
        #and that is really complicated, but it would work, I think maybe and will save for version 2.0.0

        #however, this is not relevant in a LAN enviornment and won't form enough connections per second for a lasting DoS due to the default behavior of end-user
        #clients to back off for extremely long periods after a failed attempt to contact a peer so leave it
        #can't really change it without breaking clients behind NATs in one way or another or dramatically increases the server code's complexity, doing so would also delay peer discovery by 1 min

        #set the peer_id.md5 as the key to a new list object
        master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()]=self.createPeer(client_object['client_peer_id'],is_seed,client_port,ipv4address,ipv6address)
        
         #if the client was already in the db, and if that event is a stopped event, decrement the seeders or incomplete and remove that peer from the db
        if 'client_event' in client_object:
            if (client_object['client_event'].lower()=='Stopped'.lower()):
                del master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()]
                if (is_seed==True):
                    master_info_hash_table[client_info_hash.hexdigest()]['complete']=master_info_hash_table[client_info_hash.hexdigest()]['complete']-1
                if (is_seed!=True):
                    master_info_hash_table[client_info_hash.hexdigest()]['incomplete']=master_info_hash_table[client_info_hash.hexdigest()]['incomplete']-1
        return


    #table objects are dictionaries that each contain 3 entries: complete (int), incomplete (int) and another dictionary
    def createInfoHashTable(self):
        return {'complete':0,'incomplete':0}


    #each peer list returns containing: (peer_id, is_seed , created_time, port, port hex ,ipv4 (.), ipv4 hex, ipv6 (:), ipv6 hex)
    #types are (rawbytes, bool, string, int, string, string)
    def createPeer(self,peer_id,is_seed,client_port,client_ipv4_address,client_ipv6_address):
        #note that either ipv4 or ipv6 may be invalid

        #convert IP to hexadecimal format
        #if dealing with an ipv4 address, then count the octets
        #split into 4 sections
        #convert to hex, combine the hex pieces+hexed port
        if client_ipv4_address == 'invalid':
            client_ipv4_address_in_hex='invalid'
        elif client_ipv4_address != 'invalid':
            #dealing with an ipv4 address
            #but, could also be dealing with a DNS name, but how to check for that...
            ip_list=client_ipv4_address.split('.')
            for i in (range(len(ip_list))):
                #print(str(ip_list[i]))
                ip_list[i]=hex(int(ip_list[i]))
                if len(ip_list[i]) != 4:
                    ip_list[i]=ip_list[i][:2]+'0'+ip_list[i][2:]
                #print(str(ip_list[i]))
            client_ipv4_address_in_hex=str(ip_list[0])[2:]+str(ip_list[1])[2:]+str(ip_list[2])[2:]+str(ip_list[3])[2:]

        if client_ipv6_address=='invalid':
            client_ipv6_address_in_hex='invalid'
        elif client_ipv6_address!='invalid':
            if client_ipv6_address.count(':') != 7:
                client_ipv6_address_in_hex='invalid'
            elif client_ipv6_address.count(':') == 7:
                temp_list=client_ipv6_address.split(':')
                client_ipv6_address_in_hex=str(temp_list[0])
                for i in range(1,8):
                    client_ipv6_address_in_hex=client_ipv6_address_in_hex+str(temp_list[i])

        #convert port to hex
        #print(client_port)
        client_port_in_hex=str(hex(int(client_port)))[2:]
        while len(client_port_in_hex) !=4:
            client_port_in_hex='0'+client_port_in_hex
        #print(ip_port_hex)

        #print(client_ipv4_address+":"+str(client_port))
        #print(client_ipv4_address_in_hex_no_port+client_port_in_hex)

        #need to store these in hex
        #each peer list returns containing: (peer_id, is_seed , created_time, port, port hex ,ipv4 (.), ipv4 hex, ipv6 (:), ipv6 hex)
        return [peer_id, is_seed, int(time.time()), client_port, client_port_in_hex, client_ipv4_address, client_ipv4_address_in_hex, client_ipv6_address, client_ipv6_address_in_hex ]

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
                last_peer_update=master_info_hash_table[client_info_hash.hexdigest()][client_peer_id.hexdigest()][2]
                if int(time.time())-last_peer_update < minimum_interval:
                    #print('silly client found')
                    return True
        return False

    #reset data on all tracked torrents
    def checkDB(self):
        global last_database_cleanup
        global master_info_hash_table

        #remove stale peers here
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
                if int(time.time())-master_info_hash_table[i][k][2] > consider_peers_dead_after:
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
        #client_info_hash = self.get_argument("info_hash")
        #client_peer_id = self.get_argument("peer_id")
        #client_port = self.get_argument("port")
        #client_uploaded = self.get_argument("uploaded")
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

        #now just need to actually respond back (http over tcp)

        current_client_info_hash=client_request_dictionary['client_info_hash']
        #print(client_request_dictionary)

        #retrieve torrent statistics
        complete=tracker_db.get_complete(current_client_info_hash)
        incomplete=tracker_db.get_incomplete(current_client_info_hash)

        #get peerlist from database and return the raw client objects (lists) for native parsing
        #get_peerList(info_hash), returns a peer_list that is a list of list objects, each containing a different peer
        peer_List = tracker_db.get_peerList(current_client_info_hash)
        #each peer list returns containing: (peer_id, is_seed , created_time, port, port hex ,ipv4 (.), ipv4 hex, ipv6 (:), ipv6 hex)

        #possible improvements
        #could also remove the current client from the list before sending it back to them
        #or like, specify a maximum number of peers to retrieve
        #could maybe, retrieve non-seeder list to return to a seeder
        #get_peerList(current_client_info_hash)  #would return all peers of an info_hash
        #get_peerList(current_client_info_hash,'no_seeders')  #would return the non-seeders of an info_hash

        #spec says "the tracker randomly selects peers to include in the response"
        random.shuffle(peer_List)
        print(peer_List)
        
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

        total_available=int(len(peer_List))
        if total_available < client_max_response_count:
            response_count=total_available
        elif total_available >= client_max_response_count:
            response_count=client_max_response_count

        print('response_count: ')
        print(response_count)
        #output the inital bencoded dictionary that will be used for the entire response
        response_global=bencoded_complete_string+bencoded_complete_value+bencoded_incomplete_string+bencoded_incomplete_value+bencoded_interval_string+bencoded_interval_value+bencoded_min_interval_string+bencoded_min_interval_value+bencoded_peers_string
        self.write('d')
        self.write(response_global)

        #now to respond back with the peer list in the format the client requested
        #figure out how to output the peer list as (dictionary w/peer_id , dictionary w/o peer_id, compact)
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
        if client_requested_compact != True:
            #for normal responses, prepare the list by bencoding the values in the response (skip the peer id)
            #each peer in the list contains: (peer_id [0], is_seed [1], created_time [2], port [3], port hex [4],ipv4 (.) [5], ipv4 hex [6], ipv6 (:) [7], ipv6 hex [8])
            for i in range (len(peer_List)):
                peer_List[i][3]=bencode(peer_List[i][3],'int')
                if peer_List[i][5] !='invalid':
                    peer_List[i][5]=bencode(str(peer_List[i][5]),'string')
                if peer_List[i][7] !='invalid':
                    peer_List[i][7]=bencode(str(peer_List[i][7]),'string')
            #now every item other than peer id's and compact values (the hex ones) have been bencoded
            #print("peer_List: "+str(peer_List))

            #for normal responses, need to know if clients don't want a peer ID included in the response
            if 'client_no_peer_id' in client_object:
                if client_object['client_no_peer_id'] == '1':
                    #if client selected no peer_id, then very easy to respond
                    #build bencoded dictionaries of peers to respond with, (store them in a python list), 
                    #then append each bencoded dictionary to one another, 
                    #format that as a bencoded list, send it, then return
                    bencoded_peer_array=[]
                    for i in range (len(peer_List)):
                        if peer_List[i][5] !='invalid':
                            bencoded_peer_array.append(bencode(bencoded_ip_string+peer_List[i][5]+bencoded_port_string+peer_List[i][3],'dictionary'))
                        if peer_List[i][7] !='invalid':
                            bencoded_peer_array.append(bencode(bencoded_ip_string+peer_List[i][7]+bencoded_port_string+peer_List[i][3],'dictionary'))

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

            #okay so client did not request a compact response and did not say no_peer_id's and have both ipv4 and ipv6 addresses to respond with...let's do this
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
            #for normal response peer_list is (peer_id,ip, port,peer_id,ip, port,peer_id,ip, port,peer_id,ip, port...n), so multiples of 3, starting with peer id then -> ip -> port
            #each peer in the list contains: (peer_id [0], is_seed [1], created_time [2], port [3], port hex [4],ipv4 (.) [5], ipv4 hex [6], ipv6 (:) [7], ipv6 hex [8])
            while i < response_count:
                if peer_List[i][5] !='invalid':
                    self.write('d')
                    self.write(bencoded_peer_id_string)
                    #spec says that peer_id's must be 20 bytes, assume that's true here (since this should have been checked before being input into db)
                    self.write('20:')
                    #need to find out of peer id is in ut format, binary format or shadow's format
                    if str(peer_List[i][0].rfind('-')) =='-1':
                        #if there is no -, then assume it's pure hex, so just decode and send
                        peer_List[i][0]=binascii.a2b_hex(peer_List[i][0])
                        self.write(peer_List[i][0])
                    else:
                        #if there are -'s then need to separate into two parts
                        #write the first part
                        #decode the second part
                        #write the second part (don't save)
                        peer_id_prefix=peer_List[i][0][:peer_List[i][0].rfind('-')+1]
                        self.write(peer_id_prefix)
                        peer_id_binary_part=peer_List[i][0][peer_List[i][0].rfind('-')+1:]
                        peer_id_binary_part=binascii.a2b_hex(peer_id_binary_part)
                        self.write(peer_id_binary_part)
                    self.write(bencoded_ip_string)
                    self.write(peer_List[i][5])
                    self.write(bencoded_port_string)
                    self.write(peer_List[i][3])
                    self.write('e') #close peer dictionary entry

                if peer_List[i][7] !='invalid':
                    self.write('d')
                    self.write(bencoded_peer_id_string)
                    #spec says that peer_id's must be 20 bytes, assume that's true here (since this should have been checked before being input into db)
                    self.write('20:')
                    #need to find out of peer id is in ut format, binary format or shadow's format
                    if str(peer_List[i][0].rfind('-')) =='-1':
                        #if there is no -, then assume it's pure hex, so just decode and send
                        peer_List[i][0]=binascii.a2b_hex(peer_List[i][0])
                        self.write(peer_List[i][0])
                    else:
                        #if there are -'s then need to separate into two parts
                        #write the first part
                        #decode the second part
                        #write the second part (don't save)
                        peer_id_prefix=peer_List[i][0][:peer_List[i][0].rfind('-')+1]
                        self.write(peer_id_prefix)
                        peer_id_binary_part=peer_List[i][0][peer_List[i][0].rfind('-')+1:]
                        peer_id_binary_part=binascii.a2b_hex(peer_id_binary_part)
                        self.write(peer_id_binary_part)
                    self.write(bencoded_ip_string)
                    self.write(peer_List[i][7])
                    self.write(bencoded_port_string)
                    self.write(peer_List[i][3])
                    self.write('e') #close peer dictionary entry
                i=i+1
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
            #each peer in the list contains: (peer_id [0], is_seed [1], created_time [2], port [3], port hex [4],ipv4 (.) [5], ipv4 hex [6], ipv6 (:) [7], ipv6 hex [8])

            #combine the ip/port strings with values
            peer_array=[]
            for i in range (len(peer_List)):
                if peer_List[i][6] !='invalid':
                    peer_array.append(peer_List[i][6]+peer_List[i][4])

            #print(peer_array)
            if len(peer_array) >0:
                peer_list_in_hex=peer_array[0]
                #every value does not get appended to the peer_array, only the ipv4 ones
                #so need to pick whichever is lower to respond with, the response_count or the len(peer_array)
                if len(peer_array) < response_count:
                    response_count=len(peer_array)
                for i in range(response_count):
                    if i!=0:
                        peer_list_in_hex=peer_list_in_hex+peer_array[i]

                peer_list_in_binary=binascii.a2b_hex(peer_list_in_hex)
                #peer_list_in_binary=peer_list_in_hex
                peer_list_length=str(len(peer_list_in_binary))
                #   48:[binary]  with a trailing e
                self.write(peer_list_length)
                self.write(':')
                self.write(peer_list_in_binary)

            peer_array=[]
            for i in range (len(peer_List)):
                if peer_List[i][8] !='invalid':
                    peer_array.append(peer_List[i][8]+peer_List[i][4])

            if len(peer_array) >0:
                if len(peer_array) < response_count:
                    response_count=len(peer_array)
                peer_list_in_hex=peer_array[0]
                for i in range (response_count):
                    if i!=0:
                        peer_list_in_hex=peer_list_in_hex+peer_array[i]

                self.write(bencoded_peers6_string)
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


class InvalidRequest(tornado.web.RequestHandler):
    def get(self):
        #self.set_header('Content-Type', 'application/octet-stream')
        #self.set_header('Content-Type', 'text/plain')
        #should prolly just send a 404 or access restricted error instead, comment out header type if doing that
        self.send_error(403)
        self.flush()
        #self.finish()

def main():
    #parse_command_line()
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
