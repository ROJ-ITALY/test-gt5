#!/usr/bin/python3

import os
import sys
import subprocess
import time
import argparse
import tempfile

test_list = ['datetime', 'ethernet', 'fan', 'sd', 'touch', 'usb']

###############################################################################
#	class Scheduler
###############################################################################
class Scheduler:
	def __init__(self, tests, count, nostop):
		self.tests = tests
		self.count = count
		self.nostop = nostop
		self.test_failed = dict()

	def start_test(self, i, n, name):
		if (name == 'all'):
			for t in test_list:
				self.start_test(i, n, t)
		else:
			print('------------------------------')
			print(' %d/%d - %s' % (i, n, name))
			print('------------------------------')
			ret = subprocess.run(['python3', 'test_%s.py' % name])
			if ret.returncode != 0:
				if name in self.test_failed:
					self.test_failed[name] += 1
				else:
					self.test_failed[name] = 1
				if not args.nostop:
					raise Scheduler_error(2)

	def start(self):
		if self.tests == None:
			tests = test_list
		else:
			tests = self.tests

		full_test = True
		if 'all' not in self.tests:
			for t in test_list:
				if t not in self.tests:
					full_test = False
					break

		inf_path = tempfile.gettempdir() + '/inf.txt'
		if os.path.exists(inf_path):
			os.remove(inf_path)

		for i in range(0, self.count):
			for t in self.tests:
				self.start_test(i+1, self.count, t)
			self.show_report(i+1)

	def show_report(self, i):
		print('------------------------------')
		print('   Report %d' % i)
		print('------------------------------')
		print('Tests failed: %s' % scheduler.test_failed)

###############################################################################
#	class Scheduler_error
###############################################################################
class Scheduler_error(Exception):
	def __init__(self, code):
		self.code = code

###############################################################################
arg_test_list = list(test_list)
arg_test_list.append('all')

parser = argparse.ArgumentParser(description='Test scheduler')
parser.add_argument('-c', '--count', type=int, default=1, help="set number of iterations")
parser.add_argument('--nostop', action="store_true", help="continue on error")
parser.add_argument('tests', type=str, choices=arg_test_list, nargs='*', help='tests list')
args = parser.parse_args()

try:
	if os.getuid() != 0:
		raise Scheduler_error(1)

	scheduler = Scheduler(args.tests, args.count, args.nostop)
	scheduler.start()

except Scheduler_error as e:
	if e.code == 1:
		s = "Non root"
	elif e.code == 2:
		s = "Test failed"
	print('scheduler.py: error: %s' % s)
	sys.exit(e.code)
