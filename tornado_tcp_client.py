#!/usr/bin/env python
#coding=utf-8

from tornado import ioloop
from tornado import iostream
import socket


class MyStream(iostream.IOStream):
  def __init__(self, id, pool, sock, data):
    iostream.IOStream.__init__(self, sock)
    self.__data = data
    self.__pool = pool
    self.__id = id
  
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
    self.__pool.count_ok()
    self.__pool.on_body(self.__id, data)


class parallel_tcp_client:
  def count_ok(self):
    self.__ok_counter += 1

  def register_call_t(self, id,  task):
    data = None
    if len(task) > 2:
      data = task[2]
    on_body = None
    if len(task) > 3:
      on_body = task[3]
    
    self.register_call(id, task[0], task[1], data)
  
  def register_call(self, id, host, port, data = None):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    stream = MyStream(id, self, s, "GET / HTTP/1.0\r\nHost: %s\r\n\r\n"%host)

    stream.set_close_callback(self.close_callback)
    stream.connect((host, port), stream.send_request)

  def close_callback(self):
      if self.__ok_counter == self.__task_count:
        ioloop.IOLoop.instance().stop()
      elif len(self.__task_list):
        id = self.__task_count - len(self.__task_list)
        task = self.__task_list.pop()
        self.register_call_t(id, task)
  
  def on_body(self, id, data):
    self.__on_body(id, data)      

  def __init__(self, task_list, concurency, _on_body):
    self.__task_list = task_list
    self.__ok_counter = 0
    self.__task_count = len(self.__task_list)
    self.__on_body = _on_body
    for i in xrange(concurency):
      task = self.__task_list.pop()
      self.register_call_t(i, task)
      if len(self.__task_list) == 0:
        break

    ioloop.IOLoop.instance().start()

def ask_parallel(task_list, concurency, _on_body = None):
  pclient = parallel_tcp_client(task_list, concurency, _on_body) 


def map_parallel(task_list, concurency=5):
  result = [None] * len(task_list)
  def _register_result(id, data):
    result_list[id] = data

  pclient = parallel_tcp_client(task_list, concurency, _register_result)

if __name__ == "__main__":
  task_list = []
  for i in xrange(10):
    task_list.append(["ya.ru", 80, "GET / HTTP/1.0\r\nHost: %s\r\n\r\n"%"ya.ru"])

  def print_page(id, data):
    print "task_id: %d, data_len: %d"%(id, len(data))
  
  ask_parallel(task_list, 20, print_page)




