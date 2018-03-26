#!/usr/bin/python3

import os
import sys
import re
import time
import tempfile
import json
import datetime
import subprocess

###############################################################################
#	read_str_from_file
###############################################################################
def read_str_from_file(filename):
	f = open(filename, 'r')
	ret = f.readline()
	while len(ret) > 0 and (ret[-1] == '\r' or ret[-1] == '\n'):
		ret = ret[:-1]
	f.close
	return ret
	
###############################################################################
#	read_int_from_file
###############################################################################
def read_int_from_file(filename):
	f = open(filename, 'r')
	ret = int(f.readline())
	f.close
	return ret
	
###############################################################################
#	write_str_to_file
###############################################################################
def write_str_to_file(filename, value):
	f = open(filename, 'w')
	f.write(value)
	f.close

###############################################################################
#	write_int_to_file
###############################################################################
def write_int_to_file(filename, value):
	f = open(filename, 'w')
	f.write(str(value))
	f.close

###############################################################################
#	class Gpio
###############################################################################
class Gpio:
	gpio_table = {
		'IN_FAN_FB': 72
	}

	def export(name):
		i = Gpio.gpio_table[name]
		if not os.path.exists('/sys/class/gpio/gpio%d' % i):
			write_int_to_file('/sys/class/gpio/export', i)

	def unexport(name):
		i = Gpio.gpio_table[name]
		if os.path.exists('/sys/class/gpio/gpio%d' % i):
			write_int_to_file('/sys/class/gpio/unexport', i)

	def set_direction(name, d):
		i = Gpio.gpio_table[name]
		write_str_to_file('/sys/class/gpio/gpio%d/direction' % i, d)

	def read(name):
		i = Gpio.gpio_table[name]
		return read_int_from_file('/sys/class/gpio/gpio%d/value' % i)

	def write(name, v):
		i = Gpio.gpio_table[name]
		write_int_to_file('/sys/class/gpio/gpio%d/value' % i, v)

###############################################################################
#	class Test_error
###############################################################################
class Test_error(Exception):
	def __init__(self, test, code, value=None):
		self.test = test
		self.code = code
		self.value = value

###############################################################################
#	class Test_basic
###############################################################################
class Test_basic:
	def __init__(self, name):
		self.start = time.time()
		self.err_dict = { 
			'NON_ROOT': 'Non root', 
			'DEV_NOT_FOUND': 'Device \'%s\' not found',
			'RE_NOT_MATCH': 'Regular expression not match in string \'%s\'',
			'MISSING_VERSION': 'Missing version file'
		}
		self.COLOR_SUCCESS = '\033[92m'
		self.COLOR_INFO = '\033[96m'
		self.COLOR_ERROR = '\033[91m'
		self.COLOR_DEBUG = '\033[94m'
		self.COLOR_WARNING = '\033[93m'
		self.COLOR_MESSAGE = '\033[94m'
		self.COLOR_DEFAULT = '\033[39m'
		self.load_config()
		self.name = name
		self.save_inf = False
		self.save_log = False
		self.verbosity = 2
		self.color = True
		self.quiet = False
		self.log_file = None
		self.inf_file = None
		self.printk_backup = None

	def add_common_arguments(self, parser):
		parser.add_argument('--saveinf', type=str, choices=['yes', 'no'], default=self.config['saveinf'], help="save information on file")
		parser.add_argument('--savelog', type=str, choices=['yes', 'no'], default=self.config['savelog'], help="save log on file")
		parser.add_argument('-v', '--verbosity', type=int, choices=[0,1,2], default=self.config['verbosity'], help="set verbosity")
		parser.add_argument('--color', type=str, choices=['yes', 'no'], default=self.config['colorize'], help="colorize the output")
		parser.add_argument('-q', '--quiet', type=str, choices=['yes', 'no'], default=self.config['quiet'], help="set quiet mode")

	def copy_common_arguments(self, args):
		self.save_inf = (args.saveinf == 'yes')
		self.save_log = (args.savelog == 'yes')
		self.verbosity = args.verbosity
		self.color = (args.color == 'yes')
		self.quiet = (args.quiet == 'yes')

	def load_config(self):
		with open('config.json') as f:
			self.config = json.load(f)

	def get_test_version(self):
		if not os.path.exists('version'):
			raise Test_error(self, 'MISSING_VERSION')
		return read_str_from_file('version')

	def open_log(self):
		if self.save_log:
			os.umask(0)
			self.log_file = open('log.txt', 'a')

	def open_inf(self):
		if self.save_inf:
			os.umask(0)
			self.inf_file = open(tempfile.gettempdir() + '/inf.txt', 'a')

	def close_log(self):
		if self.log_file != None:
			self.log_file.close()
			self.log_file = None

	def close_inf(self):
		if self.inf_file != None:
			self.inf_file.close()
			self.inf_file = None

	def initialize(self):
		self.open_log()
		self.message('Start test [name=\'%s\', ver=\'%s\', ts=\'%s\']' % (self.name, self.get_test_version(), datetime.datetime.now()))
		if os.getuid() != 0:
			raise Test_error(self, 'NON_ROOT')
		if self.quiet:
			self.printk_backup = read_str_from_file('/proc/sys/kernel/printk')
			write_int_to_file('/proc/sys/kernel/printk', 0)
		self.open_inf()

	def finalize(self):
		if self.printk_backup != None:
			write_str_to_file('/proc/sys/kernel/printk', self.printk_backup)
			self.printk_backup = None

	def write_to_log(self, s):
		if self.log_file != None:
			self.log_file.write(s + '\n')

	def write_to_inf(self, name, value):
		if self.inf_file != None:
			self.inf_file.write('{}_{} {}\n'.format(self.name, name, value))

	def success(self):
		self.finalize()
		te = time.time() - self.start
		self.info('testDuration', '{:0.3f}'.format(te))
		s = '{:08.3f}-{}-OK'.format(te, self.name)
		if self.color:
			print(self.COLOR_SUCCESS + s + self.COLOR_DEFAULT)
		else:
			print(s)
		self.write_to_log(s)
		self.close_inf()
		self.close_log()
		sys.exit(0)
		
	def error(self, code, value):
		self.warning('RAISE %s' % code)
		try:
			self.finalize()
		except Test_error as e:
			pass
		if code in self.err_dict:
			err_txt = self.err_dict[code]
			if err_txt.find('%s') == -1:
				err_msg = err_txt
			else:
				err_msg = err_txt % (value)
		else:
			err_msg = 'Unknown error'
		te = time.time() - self.start
		self.info('duration', '{:0.3f}'.format(te))
		s = '{:08.3f}-{}-ERR {} ({})'.format(te, self.name, code, err_msg)
		if self.color:
			print(self.COLOR_ERROR + s + self.COLOR_DEFAULT)
		else:
			print(s)
		self.write_to_log(s)
		self.close_inf()
		self.close_log()
		sys.exit(-1)

	def set_verbosity(self, level):
		self.verbosity = level
		
	def info(self, name, value):
		s = '{:08.3f}-{}-INF {}_{}={}'.format(time.time() - self.start, self.name, self.name, name, value)
		if self.color:
			print(self.COLOR_INFO + s + self.COLOR_DEFAULT)
		else:
			print(s)
		self.write_to_log(s)
		self.write_to_inf(name, value)
		
	def debug(self, msg):
		s = '{:08.3f}-{}-DBG {}'.format(time.time() - self.start, self.name, msg)
		if self.verbosity > 1:
			if self.color:
				print(self.COLOR_DEBUG + s + self.COLOR_DEFAULT)
			else:
				print(s)
		self.write_to_log(s)

	def warning(self, msg):
		s = '{:08.3f}-{}-WRN {}'.format(time.time() - self.start, self.name, msg)
		if self.color:
			print(self.COLOR_WARNING + s + self.COLOR_DEFAULT)
		else:
			print(s)
		self.write_to_log(s)

	def message(self, msg):
		s = '{:08.3f}-{}-MSG {}'.format(time.time() - self.start, self.name, msg)
		if self.verbosity > 0:
			if self.color:
				print(self.COLOR_MESSAGE + s + self.COLOR_DEFAULT)
			else:
				print(s)
		self.write_to_log(s)
	
	def wait_for_device(self, d, timeout):
		start_time = time.time()
		while not os.path.exists(d):
			if time.time() - start_time > timeout:
				raise Test_error(self, 'DEV_NOT_FOUND', d)
			time.sleep(.1)

	def simple_re(self, s, r):
		p = re.compile(r)
		m = p.search(s)
		if m == None:
			raise Test_error(self, 'RE_NOT_MATCH', s)
		return m.group(1)

