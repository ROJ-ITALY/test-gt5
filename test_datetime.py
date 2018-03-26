#!/usr/bin/python3

import os
import subprocess
import argparse
from common import *

###############################################################################
#	class Test_datetime
###############################################################################
class Test_datetime(Test_basic):
	def __init__(self):
		Test_basic.__init__(self, 'datetime')
		self.err_dict['NTP_CLIENT_ERROR'] = 'NTP client error'
		self.err_dict['STORE_TO_HWCLOCK_FAILED'] = 'Store to hardware clock failed'
	
	def initialize(self):
		Test_basic.initialize(self)

	def finalize(self):
		try:
			Test_basic.finalize(self)
		except Test_error as e:		
			sys.exit(-1)

	def set_ip_address(self, if_name):
		return subprocess.run(['udhcpc', '-i', if_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

	def ntp_client(self):
		if subprocess.run(['ntpd', '-n', '-q', '-p', self.peer], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
			raise Test_error(self, 'NTP_CLIENT_ERROR')

	def hc_to_sys(self):
		if subprocess.run(['hwclock'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
			self.warning('Read from hardware clock failed')

	def sys_to_hc(self):
		if subprocess.run(['hwclock', '-w'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
			raise Test_error(self, 'STORE_TO_HWCLOCK_FAILED')

###############################################################################
try:
	t = Test_datetime()
	
	parser = argparse.ArgumentParser(description='Test Date & Time')
	t.add_common_arguments(parser)
	parser.add_argument('--peer', type=str, default=t.config['datetime']['peer'], help="set IP address of NTP server")
	args = parser.parse_args()
	t.copy_common_arguments(args)
	t.peer = args.peer

	t.initialize()

	t.message('Read hardware clock')
	t.hc_to_sys()

	t.message('Set IP address via dhcp')
	if not t.set_ip_address('eth0'):
		raise Test_error(t, 'NO_IP_ADDR')

	t.message('NTP client from %s' % t.peer)
	t.ntp_client()

	t.message('Write hardware clock')
	t.sys_to_hc()

	t.success()

except Test_error as e:
	e.test.error(e.code, e.value)


