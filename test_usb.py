#!/usr/bin/python3

import os
import subprocess
import time
import argparse
from common import *

###############################################################################
#	class Test_usb
###############################################################################
class Test_usb(Test_basic):
	def __init__(self):
		Test_basic.__init__(self, 'usb')
		self.err_dict['CHECK_A_FAILED'] = 'Check pen drive A failed or invalid pen drive A'
		self.err_dict['CHECK_B_FAILED'] = 'Check pen drive B failed or invalid pen drive B'
		self.err_dict['MOUNT_A_FAILED'] = 'Mount pen drive A failed'
		self.err_dict['MOUNT_B_FAILED'] = 'Mount pen drive B failed'
	
	def initialize(self):
		Test_basic.initialize(self)

	def finalize(self):
		try:
			Test_basic.finalize(self)
		except Test_error as e:		
			sys.exit(-1)

	def check(self):
		self.message('Check USB key A')
		ret = subprocess.run(['findmnt', '-S', 'LABEL=\"%s\"' % self.label_a, '-n', '-o', 'TARGET'], stdout=subprocess.PIPE)
		path_a = ret.stdout.decode('utf-8')[:-1]
		if not os.path.exists(path_a):
			raise Test_error(self, 'MOUNT_A_FAILED')
		if subprocess.run(['sha256sum', '-c', 'test-file.sha256'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path_a).returncode != 0:
			raise Test_error(self, 'CHECK_A_FAILED')

		self.message('Check USB key B')
		ret = subprocess.run(['findmnt', '-S', 'LABEL=\"%s\"' % self.label_b, '-n', '-o', 'TARGET'], stdout=subprocess.PIPE)
		path_b = ret.stdout.decode('utf-8')[:-1]
		if not os.path.exists(path_b):
			raise Test_error(self, 'MOUNT_B_FAILED')
		if subprocess.run(['sha256sum', '-c', 'test-file.sha256'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=path_b).returncode != 0:
			raise Test_error(self, 'CHECK_B_FAILED')

###############################################################################
try:
	t = Test_usb()
	
	parser = argparse.ArgumentParser(description='Test USB')
	t.add_common_arguments(parser)
	parser.add_argument('--labela', type=str, default=t.config['usb']['labela'], help="set pen drive A label")
	parser.add_argument('--labelb', type=str, default=t.config['usb']['labelb'], help="set pen drive B label")
	args = parser.parse_args()
	t.copy_common_arguments(args)
	t.label_a = args.labela
	t.label_b = args.labelb

	t.initialize()

	t.check()

	t.success()

except Test_error as e:
	e.test.error(e.code, e.value)


