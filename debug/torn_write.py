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

#from py3bencode import bencode

#import tornado
import tornado.ioloop
import tornado.web
import tornado.httpserver
import tornado.httputil
#import tornado.escape
#import tornado.gen
#from tornado.concurrent import Future
from tornado.options import define, options, parse_command_line

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        peerlist_hex_string='c0a8006a84f3c0a80064e9c7c0a800960c80c0a8006c33f1c0a8006a1b4b'
        peerlist_binary=binascii.a2b_hex(peerlist_hex_string)
        response=peerlist_binary
        print(response)
        
        #response='peers'
        #self.set_header('Content-Type', 'application/octet-stream')
        self.write('string')
        self.write(response)
        self.flush()
        #output for dictionary type:
        #dictionary peer list (multiple strings + bitstreams, difficult to pass back-forth through messages)
        #dictionary w/o peer list 1 string
        #output for compact type:
        #only 1 type but needs: 1string+1bitstream (peers) (can append e at the end)
        #could return...each component, and a peerlist, then write it dynamically as chunks in main response
        #return components + peer string, (bitstream list)
    
def main():
    parse_command_line()
    global tracker_db
    #tracker_db = Database()
    app = tornado.web.Application([
            (r"/announce.*", MainHandler),
            ])
    app.listen(8080)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()