#!/usr/bin/python3

import os
import subprocess
import time
import argparse
from common import *

###############################################################################
#	class Test_ethernet
###############################################################################
class Test_ethernet(Test_basic):
	def __init__(self):
		Test_basic.__init__(self, 'ethernet')
		self.err_dict['IF_NOT_FOUND'] = 'Interface \'%s\' not found'
		self.err_dict['PING_FAILED'] = 'Ping failed'
		
	def initialize(self):
		Test_basic.initialize(self)

	def finalize(self):
		try:
			Test_basic.finalize(self)
		except Test_error as e:
			sys.exit(-1)

	def check_interface(self, if_name):
		return subprocess.run(['ip', 'address', 'show', if_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

	def get_mac_address(self, if_name):
		ret = subprocess.run(['ip', 'address', 'show', if_name], stdout=subprocess.PIPE)
		mac_address = self.simple_re(ret.stdout.decode('utf-8'), '.*link/ether ([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})')
		return mac_address

	def get_ip_address(self, if_name):
		ret = subprocess.run(['ip', 'address', 'show', if_name], stdout=subprocess.PIPE)
		ip_address = self.simple_re(ret.stdout.decode('utf-8'), '.*inet ([0-9]*\.[0-9]*\.[0-9]*\.[0-9]*)')
		return ip_address

	def set_ip_address(self, if_name):
		return subprocess.run(['udhcpc', '-n', '-i', if_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

	def ping(self):
		if subprocess.run(['ping', self.target, '-q', '-c', '3'], stdout=subprocess.DEVNULL).returncode != 0:
			raise Test_error(self, 'PING_FAILED')

###############################################################################
try:
	t = Test_ethernet()

	parser = argparse.ArgumentParser(description='Test Ethernet')
	t.add_common_arguments(parser)
	parser.add_argument('-t', '--target', type=str, default=t.config['ethernet']['target'], help="set target IP address to ping")
	args = parser.parse_args()
	t.copy_common_arguments(args)
	t.target = args.target

	t.initialize()

	t.message('Check interface \'eth0\'')
	if not t.check_interface('eth0'):
		raise Test_error(t, 'IF_NOT_FOUND', 'eth0')

	t.message('Set IP address via dhcp')
	if not t.set_ip_address('eth0'):
		raise Test_error(t, 'NO_IP_ADDR')

	t.message('Get IP address \'eth0\'')
	ip_address = t.get_ip_address('eth0')
	t.message('IP address \'eth0\': %s' % ip_address)

	t.message('Get MAC address \'eth0\'')
	ip_address = t.get_mac_address('eth0')
	t.info('MAC_address_eth0', ip_address)

	t.message('Ping %s' % t.target)
	t.ping()

	t.success()

except Test_error as e:
	e.test.error(e.code, e.value)
