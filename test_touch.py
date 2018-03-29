#!/usr/bin/python3

import os
import subprocess
import time
import argparse
from common import *

###############################################################################
#	class Test_touch
###############################################################################
class Test_touch(Test_basic):
	def __init__(self):
		Test_basic.__init__(self, 'touch')
		self.err_dict['NO_TOUCH'] = 'AR1100 HID-MOUSE not detected'
		
	def initialize(self):
		Test_basic.initialize(self)

	def finalize(self):
		try:
			Test_basic.finalize(self)
		except Test_error as e:
			sys.exit(-1)

	def check_touch(self):
		return subprocess.run(['sh', '-c', 'dmesg | grep AR1100'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0

###############################################################################
try:
	t = Test_touch()

	parser = argparse.ArgumentParser(description='Test touch')
	t.add_common_arguments(parser)
	args = parser.parse_args()
	t.copy_common_arguments(args)

	t.initialize()

	t.message('Check touch AR1100 HID-MOUSE')
	if not t.check_touch():
		raise Test_error(t, 'NO_TOUCH')

	t.success()

except Test_error as e:
	e.test.error(e.code, e.value)
