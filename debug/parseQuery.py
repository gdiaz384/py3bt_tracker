#!/usr/bin/python
# -*- coding: UTF-8 -*-

import codecs
import binascii
import urllib.parse
import hashlib
import base64
import sys
import random

#import codecs
#codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)
#codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp437' else None)
#import fixWindowsCMD.py

random.seed()

#raw query
query="info_hash=%124Vx%9A%BC%DE%F1%23Eg%89%AB%CD%EF%124Vx%9A&peer_id=-UT2210-%b9b%2cs%c3%15%c6Q%3cu%95%96&port=18584&uploaded=0&downloaded=0&left=109603551&corrupt=0&key=0E09C995&event=started&numwant=200&compact=1&no_peer_id=1"
print("query: " + query)

#print the number of items in uri
queryItems=len(query.split("&"))
print("queryItems: " + str(queryItems))

#place each item into a dictionary container
client_rawRequestContainer=dict({})
for i in range(queryItems):
    print (str(i)+": "+(query.split("&")[i]))
    temp=query.split("&")[i]
    client_rawRequestContainer.update([temp.split("=")])

#initalize temp variables
invalid="invalid"
client_info_hash=invalid
client_peer_id=invalid
client_port=invalid
client_uploaded=invalid
client_downloaded=invalid
client_left=invalid
client_compact=invalid
client_no_peer_id=invalid
client_event=invalid
client_ip=invalid
client_numwant=invalid
client_key=invalid
client_trackerid=invalid
client_corrupt=invalid

#search dictionary to make sure the item is present, then place into temporary variables, error out on required variables
if ('info_hash' in client_rawRequestContainer) == (True):
    client_info_hash=client_rawRequestContainer["info_hash"]
else:
    print("error: info_hash not present")

if ('peer_id' in client_rawRequestContainer) == (True):
    client_peer_id=client_rawRequestContainer["peer_id"]
else:
    print("error: peer_id not present")
	
if ('port' in client_rawRequestContainer) == (True):
    client_port=client_rawRequestContainer["port"]
else:
    print("error: port not present")
	
if ('uploaded' in client_rawRequestContainer) == (True):
    client_uploaded=client_rawRequestContainer["uploaded"]
else:
    print("error: uploaded not present")
	
if ('downloaded' in client_rawRequestContainer) == (True):
    client_downloaded=client_rawRequestContainer["downloaded"]
else:
    print("error: downloaded not present")
	
if ('left' in client_rawRequestContainer) == (True):
    client_left=client_rawRequestContainer["left"]
else:
    print("error: left not present")
	
if ('compact' in client_rawRequestContainer) == (True):
    client_compact=client_rawRequestContainer["compact"]
else:
    print("error: compact not present")
	
if ('no_peer_id' in client_rawRequestContainer) == (True):
    client_no_peer_id=client_rawRequestContainer["no_peer_id"]
else:
    print("error: no_peer_id not present")
	
if ('event' in client_rawRequestContainer) == (True):
    client_event=client_rawRequestContainer["event"]
else:
    print("error: event not present")

if ('ip' in client_rawRequestContainer) == (True):
    client_ip=client_rawRequestContainer["ip"]
else:
    print("error: ip not present")
	
if ('numwant' in client_rawRequestContainer) == (True):
    client_numwant=client_rawRequestContainer["numwant"]
else:
    print("error: numwant not present")
	
if ('key' in client_rawRequestContainer) == (True):
    client_key=client_rawRequestContainer["key"]
else:
    print("error: key not present")
	
if ('trackerid' in client_rawRequestContainer) == (True):
    client_trackerid=client_rawRequestContainer["trackerid"]
else:
    print("error: trackerid not present")
	
if ('corrupt' in client_rawRequestContainer) == (True):
    client_corrupt=client_rawRequestContainer["corrupt"]
else:
    print("error: corrupt not present")

#print_client_info
print("client_info_hash: "+client_info_hash)
print("client_peer_id: "+client_peer_id)
print("client_port: "+client_port)
print("client_uploaded: "+client_uploaded)
print("client_downloaded: "+client_downloaded)
print("client_left: "+client_left)
print("client_compact: "+client_compact)
print("client_no_peer_id: "+client_no_peer_id)
print("client_event: "+client_event)
print("client_ip: "+client_ip)
print("client_numwant: "+client_numwant)
print("client_key: "+client_key)
print("client_trackerid: "+client_trackerid)
print("client_corrupt: "+client_corrupt)


print()
raw_info_hash=b'\x12\x34\x56\x78\x9a\xbc\xde\xf1\x23\x45\x67\x89\xab\xcd\xef\x12\x34\x56\x78\x9a'

#so the info hash can't display in raw form, so encode it to a utf-8 bytestream (displayable)
#and then convert it to a string so it can be appended to the other string "raw_info_hash: "
#still won't be displayed exactly right but close enough, and it's stored correctly internally
print("raw_info_hash: "+str(raw_info_hash))
print("decoded_raw_info_hash"+(str(binascii.b2a_hex(raw_info_hash))))
print("length: "+str(len(binascii.b2a_hex(raw_info_hash))))
#40 hex digits means 20 bytes long

print()
encoded_info_hash=urllib.parse.quote_from_bytes(raw_info_hash,safe='')
print("url encoded_info_hash: " +encoded_info_hash)
#print("encoded_info_hash: " +encoded_info_hash.encode('utf-8'))

print()
decoded_info_hash=binascii.b2a_hex(urllib.parse.unquote_to_bytes(encoded_info_hash))
print("decoded_info_hash: "+str(decoded_info_hash))

#print()
#encoded_info_hash is the URL % encoded format
#now try for the non % format, failed x.x
#info_hash_data=base64.urlsafe_b64decode(encoded_info_hash)
#print("info_hash_data: "+str(info_hash_data))

#print("decoded_info_hash: "+str(decoded_info_hash.encode('utf-8')))
#print("raw_info_hash: "+str(raw_info_hash))
#encoded_info_hash=urllib.parse.quote(raw_info_hash,safe='')
#print("encoded_info_hash: "+str(encoded_info_hash))
#encoded_info_hash=urllib.parse.unquote(raw_info_hash, safe='')
#print("unencoded_info_hash: "+str(encoded_info_hash))

print()
raw_unencoded_peer_id='-UT2210-b9b2csc315c6Q3cu9596'
print("raw_unencoded_peer_id: "+str(raw_unencoded_peer_id))

prefix=raw_unencoded_peer_id[:raw_unencoded_peer_id.rfind('-')+1]
raw_unencoded_peer_id_part=raw_unencoded_peer_id[raw_unencoded_peer_id.rfind('-')+1:]
print(str(len(urllib.parse.unquote_to_bytes(raw_unencoded_peer_id_part))))
url_encoded_raw_peer_id_part=urllib.parse.quote(raw_unencoded_peer_id_part)
print("url_encoded_raw_peer_id_part: "+str(url_encoded_raw_peer_id_part))
#decoded_raw_peer_id=binascii.b2a_hex(urllib.parse.unquote_to_bytes(url_encoded_raw_peer_id))
decoded_raw_peer_id=prefix+str(url_encoded_raw_peer_id_part)
print("decoded_raw_peer_id: "+str(len(decoded_raw_peer_id))+": "+str(decoded_raw_peer_id))

#standard peer id
#aria's random hex method (also use by bram and others)
#shadow's method


#decode into bytes, make sure prefix+bytes = 20
#if prefix not present, then just convert to bytes and make sure =20
#Then stored form is no longer url encoded and ready for transmission
#make sure when creating hash that it's from the binary form
#do this when storing info_hash, peer_id and (per peer) keys

print()
print()
raw_encoded_url_string='-UT2210-%b9b%2cs%c3%15%c6Q%3cu%95%96'

print("raw_encoded_url_string: "+str(raw_encoded_url_string))
#check if string has seperate parts, if so decode only the second part
#a length of 24 hex digits means 12 bytes, 12 bytes of hex + prefix = 20 bytes if prefix is 8 bytes long
#35-3 (from hex to string conversion) is 32-8 =24, 24/2 = 12+8 = 20 bytes
#Note: the version could be encoded into the binary form itself instead of shown raw in the url (Aria does this)
if raw_encoded_url_string.rfind('-') == -1:
	decoded_url_string=urllib.parse.unquote_to_bytes(raw_encoded_url_string)
	#print(str(decoded_url_string))
	if len(decoded_url_string) != 20:
		print('error')
	temp=str(binascii.b2a_hex(decoded_url_string))
	#print(temp)
	decoded_url_string=temp[2:len(temp)-1]
elif raw_encoded_url_string.rfind('-') != -1:
	prefix=raw_encoded_url_string[:raw_encoded_url_string.rfind('-')+1]
	#print(str(len(prefix))+prefix)
	peer_id_part=raw_encoded_url_string[raw_encoded_url_string.rfind('-')+1:]
	decoded_url_string=urllib.parse.unquote_to_bytes(peer_id_part)
	#print(str(decoded_url_string))
	if len(prefix)+len(decoded_url_string) != 20:
		print('error')
	temp=str(binascii.b2a_hex(decoded_url_string))
	temp=temp[2:len(temp)-1]
	#print(temp)
	decoded_url_string=prefix+temp
print("decoded_url_string: "+decoded_url_string)


print()
raw_encoded_url_string='A2%2D1%2D19%2D0%2D%3DQ%C8%D3%7DS%BD%DA%95%25'

print("raw_encoded_url_string: "+str(raw_encoded_url_string))
if raw_encoded_url_string.rfind('-') == -1:
	decoded_url_string=urllib.parse.unquote_to_bytes(raw_encoded_url_string)
	#print(str(decoded_url_string))
	if len(decoded_url_string) != 20:
		print('error')
	temp=str(binascii.b2a_hex(decoded_url_string))
	#print(temp)
	decoded_url_string=temp[2:len(temp)-1]
elif raw_encoded_url_string.rfind('-') != -1:
	prefix=raw_encoded_url_string[:raw_encoded_url_string.rfind('-')+1]
	#print(str(len(prefix))+prefix)
	peer_id_part=raw_encoded_url_string[raw_encoded_url_string.rfind('-')+1:]
	decoded_url_string=urllib.parse.unquote_to_bytes(peer_id_part)
	#print(str(decoded_url_string))
	if len(prefix)+len(decoded_url_string) != 20:
		print('error')
	temp=str(binascii.b2a_hex(decoded_url_string))
	temp=temp[2:len(temp)-1]
	#print(temp)
	decoded_url_string=prefix+temp
print("decoded_url_string: "+decoded_url_string)



print()
raw_encoded_url_string='S58B-----%b9b%2cs%c3%15%c6Q%3cu%95%96'

print("raw_encoded_url_string: "+str(raw_encoded_url_string))
if raw_encoded_url_string.rfind('-') == -1:
	decoded_url_string=urllib.parse.unquote_to_bytes(raw_encoded_url_string)
	#print(str(decoded_url_string))
	if len(decoded_url_string) != 20:
		print('error')
	temp=str(binascii.b2a_hex(decoded_url_string))
	#print(temp)
	decoded_url_string=temp[2:len(temp)-1]
elif raw_encoded_url_string.rfind('-') != -1:
	prefix=raw_encoded_url_string[:raw_encoded_url_string.rfind('-')+1]
	#print(str(len(prefix))+prefix)
	peer_id_part=raw_encoded_url_string[raw_encoded_url_string.rfind('-')+1:]
	decoded_url_string=urllib.parse.unquote_to_bytes(peer_id_part)
	#print(str(decoded_url_string))
	if len(prefix)+len(decoded_url_string) != 20:
		print('error')
	temp=str(binascii.b2a_hex(decoded_url_string))
	temp=temp[2:len(temp)-1]
	#print(temp)
	decoded_url_string=prefix+temp
print("decoded_url_string: "+decoded_url_string)



print()
#need to store these in hex
ip4_address='128.168.0.10'
ip_port=8080
#print(ip_port)
ip_port_in_hex=str(hex(ip_port))[2:]
while len(ip_port_in_hex) !=4:
	ip_port_in_hex='0'+ip_port_in_hex
#print(ip_port_hex)
#if dealing with an ipv4 address, then count the octets
#split into 4 sections
#convert to hex, combine the hex pieces+hexed port
if ip4_address.count('.') == 3:
	#dealing with an ipv4 address
	ip_list=ip4_address.split('.')
	for i in (range(len(ip_list))):
		#print(str(ip_list[i]))
		ip_list[i]=hex(int(ip_list[i]))
		if len(ip_list[i]) != 4:
			ip_list[i]=ip_list[i][:2]+'0'+ip_list[i][2:]
		#print(str(ip_list[i]))
		#temp=str(ip_list[0])[2:]
		#temp1=str(ip_list[1])[2:]
		#temp2=str(ip_list[2])[2:]
		#temp3=str(ip_list[3])[2:]
		#address_no_port=temp+temp1+temp2+temp3
	address_in_hex_no_port=str(ip_list[0])[2:]+str(ip_list[1])[2:]+str(ip_list[2])[2:]+str(ip_list[3])[2:]
else:
	#dealing with an ipv6 address
	address_no_port=ip4_address
#print(ip4_address+":"+str(ip_port))
#print(address_no_port)
hex_address=address_in_hex_no_port+ip_port_in_hex
#print(hex_address)

raw_encoded_url_string3='S58B-----%15%c6%3cu%95%96'

#print()
#print("raw_encoded_url_string3: "+str(raw_encoded_url_string3))
if raw_encoded_url_string3.rfind('-') != -1:
	prefix=raw_encoded_url_string3[:raw_encoded_url_string3.rfind('-')+1]
	#print(prefix)
	peer_id_part=raw_encoded_url_string3[raw_encoded_url_string3.rfind('-')+3:]
	decoded_url_string3=binascii.b2a_hex(urllib.parse.unquote_to_bytes(peer_id_part))
	decoded_url_string3=prefix+str(decoded_url_string3)
else:
	decoded_url_string3=binascii.b2a_hex(urllib.parse.unquote_to_bytes(raw_encoded_url_string3))
#print("decoded_url_string3: " + str(len(decoded_url_string3)) + ": " + str(decoded_url_string3))

def createTable(table_id,client_dictionary,client_remote_ip):
        #use the client dictionary along with IP info to create a Peer
        #determine if a client_ip was used in the client_dictionary, if so use it, else use the IP from the connection instead

        if (client_dictionary['left'] == 0):
            isSeed=True
        elif (client_dictionary['left'] != 0):
            isSeed=False
        
        if client_ip in client_dictionary:
            new_Peer=createPeer(client_dictionary['client_peer_id'],isSeed,client_dictionary['client_ip'],client_dictionary['client_port'])
        elif client_ip not in client_dictionary:
            new_Peer=createPeer(client_dictionary['client_peer_id'],isSeed,client_remote_ip ,client_dictionary['client_port'])

        #set initial values for peer count
        complete=0
        incomplete=0
        if (isSeed == True):
            complete=1
        elif (isSeed != True):
            incomplete=1
        
        #and finally create a new table using the table id specified and the new Peer
        #generate new peer
        
        #table_id[0].append()
        return



info_hash_table=({})
complete=0
incomplete=0
client0=['-UT2210-b9b2csc315c6Q3cu9596',False,'192.168.0.1',2342,'192.168.0.1',2342]
client1=['-UT2210-b9b2csc315c6Q3cu9595',False,'192.168.0.2',9653,'192.168.0.1',2342]
client2=['-UT2210-b9b2csc315c6Q3cu9593',False,'192.168.0.3',5412,'192.168.0.1',2342]

#print(client0)
#print(client1)
#print(client2)

info_hash_table['complete']=complete
info_hash_table['incomplete']=incomplete

#map the md5 hash of the peer_id to the client object
clientHash=hashlib.md5()
clientHash.update(client0[0].encode('utf-8'))
info_hash_table[clientHash.digest()]=client0
clientHash=hashlib.md5()
clientHash.update(client1[0].encode('utf-8'))
info_hash_table[clientHash.digest()]=client1
clientHash=hashlib.md5()
clientHash.update(client2[0].encode('utf-8'))
info_hash_table[clientHash.digest()]=client2

#print("Entries in info_hash_table: " +str(len(info_hash_table)))
#print("complete:"+ str(info_hash_table["complete"]))
#print("incomplete:" + str(info_hash_table["incomplete"]))


#query a single client
#print("client_ip:")
client_query=hashlib.md5()
client_query.update(client0[0].encode('utf-8'))
#print(info_hash_table[client_query.digest()][2])
#print("client port")
client_query=hashlib.md5()
client_query.update(client0[0].encode('utf-8'))
#print(info_hash_table[client_query.digest()][3])

#build a peerlist
#md5 hashes of the peer_id are used as keys
info_hashes_table_keys=info_hash_table.keys()
peer_list=[]
for i in (info_hashes_table_keys):
	if (i != 'complete'):
		if (i != 'incomplete'):
			#print(str(info_hash_table[i][2])+":"+str(info_hash_table[i][3]))
			peer_list.append((info_hash_table[i][2],info_hash_table[i][3]))

#print (peer_list)

master_info_hash_table=({})
#masterlist is a dictionary mapping md5 hashes of info_hashes to table_objects (dict objects)
info_hash0='%124Vx%9A%BC%DE%F1%23Eg%89%AB%CD%EF%124Vx%9A '
info_hash1='%124Vx%9A%BC%DE%F1%23Eg%89%AB%CD%EF%124Vx%9B '
info_hash2='%124Vx%9A%BC%DE%F1%23Eg%89%AB%CD%EF%124Vx%9C '

#Class dummy();
#	pass

	
#client_requested_info_hash=hashlib.md5()
#client_requested_info_hash.update(info_hash0.encode('utf-8'))
#info_hash_table[clientHash.digest()]=client0
#if not exist then create a new one
#if client_requested_info_hash.digest() not in master_info_hash_table:
#	master_info_hash_table[client_requested_info_hash.digest()]=createTable()
#setattr(master_info_hash_table[client_requested_info_hash.digest()],newTable,newTable)
	#dummy_reference_table={newTable:master_info_hash_table[client_requested_info_hash.digest()]}
	#master_info_hash_table[client_requested_info_hash.digest()].set_name(newTable)
#elif client_requested_info_hash.digest() in master_info_hash_table:
#	print("already present")



#this should be the table string now
#print(master_info_hash_table[client_requested_info_hash.digest()])
#this should be the table object now
#print(str(master_info_hash_table[client_requested_info_hash.digest()]))

