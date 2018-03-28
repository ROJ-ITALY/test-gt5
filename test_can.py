#!/usr/bin/python3

import os
import subprocess
import time
import argparse
import socket
import select
import sys
import struct
import threading
from common import *

###############################################################################
#	class Test_can
###############################################################################
class Test_can(Test_basic):
	def __init__(self):
		Test_basic.__init__(self, 'can')
		self.err_dict['OS_ERROR'] = 'OS Error \'%s\''
		self.err_dict['TEST_CAN_FAIL'] = 'Test "CAN" failed'
		self.err_dict['NOT_BIND_IF'] = 'Could not bind to interface \'%s\''
		self.err_dict['TIMEOUT'] = 'Not receive package on interface \'%s\''
		self.rx_error = None
		self.sock = None
		self.interface = None

	def initialize(self):
		Test_basic.initialize(self)

	def finalize(self):
		try:
			Test_basic.finalize(self)
		except Test_error as e:
			sys.exit(-1)

	def tx(self, a_id, a_msg):
		try:
			can_pkt = struct.pack('<IB3x8s', a_id, len(a_msg), a_msg)
			self.sock.send(can_pkt)
		except OSError as e:
			raise Test_error(self, 'OS_ERROR', str(e))

	def rx(a_id, a_msg, t):
		try:
			inputs = [ t.sock ]
			outputs = []
			readable, writable, exceptional = select.select(inputs, outputs, inputs, 10)
			s = readable[0]
			can_pkt = s.recv(16)
			can_id, length, data = struct.unpack('<IB3x8s', can_pkt)
			can_id &= socket.CAN_EFF_MASK
			msg = data[:length]
			if can_id == (a_id+1) and msg == a_msg:
				pass
			else:
				t.rx_error = Test_error(t, 'TEST_CAN_FAIL')
		except IndexError:
			t.rx_error = Test_error(t, 'TIMEOUT', t.interface)
		except OSError as e:
				t.rx_error = Test_error(t, 'OS_ERROR', str(e))

	def test(self, interface, can_id, msg):
		self.interface = interface
		self.sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
		try:
			self.sock.bind((interface,))
		except OSError:
			raise Test_error(self, 'NOT_BIND_IF', interface)
		t = threading.Thread(target=Test_can.rx, args=(can_id, msg, self))
		t.start()
		time.sleep(.1)
		self.tx(can_id, msg)
		t.join()

		if self.rx_error == None:
			self.success()
		else:
			raise self.rx_error

###############################################################################
try:
	t = Test_can()

	parser = argparse.ArgumentParser(description='Test Can')
	t.add_common_arguments(parser)
	args = parser.parse_args()
	t.copy_common_arguments(args)
	
	t.initialize()

	t.test('can0', 0x12, b'11223344')

except Test_error as e:
	e.test.error(e.code, e.value)
