#!/usr/bin/env python
#coding=utf-8

from tornado import ioloop
from tornado import iostream
import socket

task_list = []
for i in xrange(10):
  task_list.append(["ya.ru", 80])

task_count = len(task_list)
ok_counter = 0

class MyStream(iostream.IOStream):
  def __init__(self, sock, data):
    iostream.IOStream.__init__(self, sock)
    self.__data = data
  
  def send_request(self):
      self.write(self.__data) 
      self.read_until("\r\n\r\n", self.on_headers)

  def on_headers(self, data):
      headers = {}
      for line in data.split("\r\n"):
         parts = line.split(":")
         if len(parts) == 2:
             headers[parts[0].strip()] = parts[1].strip()
      self.read_bytes(int(headers["Content-Length"]), self.on_body)
  
  def on_body(self, data):
    global ok_counter
    ok_counter += 1  
    print "len(data): ",len(data)




def register_call(host, port):
  s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
  stream = MyStream(s, "GET / HTTP/1.0\r\nHost: %s\r\n\r\n"%host)
    
  #stream = iostream.IOStream(s)
  stream.set_close_callback(close_callback)
  stream.connect((host, port), stream.send_request)

def close_callback():
    print "closed"
    if ok_counter == task_count:
      ioloop.IOLoop.instance().stop()
    elif len(task_list):
      task = task_list.pop()
      register_call(task[0], task[1])
      

for i in xrange(5):
  task = task_list.pop()
  register_call(task[0], task[1])

ioloop.IOLoop.instance().start()
