#!/usr/bin/python3
""" ShaZam  can calculate a file sum and compare with a given one.

ShaZam as also other options like:
	calculate all supported hashsums of one file
	calculate and compare file sum which is inside a text file
	Calculate only the file sum without compare it 

Prerequesites:
	Python version 3.2.x or higher
	termcolor version 1.1.x or higher (install it with pip or conda)
	alive_progress version 1.6.x or higher (install it with pip or conda)
"""


#### Libraries
# Standart Libraries
import os
import sys
import hashlib as hlib
from time import sleep

# Third-part libraries
try:
	from termcolor import colored as clr
	from alive_progress import alive_bar
except ImportError:
	print_error("Important Modules are not installed yet: termcolor, " +
	"alive_progress.\nInstall them with: pip (or pip3) install termcolor " +
	"alive_progress")


version = None
if os.path.exists("/usr/share/shazam/VERSION"):
	with open("/usr/share/shazam/VERSION", "rt") as ver:
		version = str(ver.read()).strip()


__author__ = "Anaxímeno Brito"
__version__ = version if version else 'Undefined'
__license__ = "GNU General Public License v3.0"
__copyright__ = "Copyright (c) 2021 by Anaxímeno Brito"


# List of supported hash sums
sumtypes_list = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]
BUF_SIZE = 32768 # Constant, don't change!


def exists(path):
	"""Searchs for a file/path and return bool."""
	return os.path.exists(path)


def print_error(*err: object, exit=True):
	"""print error message and exit.
	Keyword arg: exit -- bool (default True)."""
	error_message = ' '.join(err)
	print("shazam: error: %s" % error_message)	
	if exit: 
		sys.exit(1)


def hexa_to_int(hexa):
		"""Receive hexadecimal string and return integer."""
		try:	
			return int(hexa, 16)
		except ValueError:
			print_error(f"{hexa!r} is not an hexadecimal value!")


def readable(fname):
		"""Analyses de readability and return bool."""
		if exists(fname) and os.path.isfile(fname):
			try:
				with open(fname, "rb") as f: f.read(1)
				return True
			except UnicodeDecodeError:
				return False
		else:
			return False


def sumtype(fname):
		"""Analyses the filename and return the sumtype."""
		if readable(fname):
			for stype in sumtypes_list[::-1]:
				if stype in fname:
					return stype
			print_error(f"Sumtype not recognized in: {fname!r}")


def contents(name):
		"""Return a list with tuples with the content of the file, 
		the tuple will be like (filename, sum)."""
		if exists(name):
			content = []

			with open(name, "rt") as txt:
				try:
					for line in txt:
						givensum, filename = line.split()
						if name[0] == '*' and not exists(name):
							filename = filename[1:]
						content.append((filename, givensum))
				except ValueError:
					print_error(f"Error reading {name!r}")
		
			return content		
		else:
			print_error(f"{name!r} was not found!")


class FileId(object):

	def __init__(self, name, givensum=None):
		self.name = name
		self.existence = exists(name)
		self.readability = readable(name)
		self.gsum = givensum
		self.integer_sum = hexa_to_int(givensum) if givensum else None
		if exists(name):
			self.size = os.path.getsize(name)
			self.hlist = {
				"md5": hlib.md5(),
				"sha1": hlib.sha1(),
				"sha224": hlib.sha224(),
				"sha256": hlib.sha256(),
				"sha384": hlib.sha384(),
				"sha512": hlib.sha512()
			}

	def get_hashsum(self, sumtype):
		"""Return the file's hash sum."""
		if self.readability:
			return self.hlist[sumtype].hexdigest()
		print_error(f"{self.name!r} is unreadable!")

	def gen_data(self, bars=True):
		"""Generates binary data. Keyword arg: bars -- bool (default: True)."""
		if not self.readability:
			print_error(f"{self.name!r} is unreadable!")
		else:
			if self.size < BUF_SIZE: 
				times = 1
			elif self.size % BUF_SIZE == 0: 
				times = int(self.size / BUF_SIZE)
			else:
				self.size -= self.size % BUF_SIZE
				times = int(self.size / BUF_SIZE) + 1

			def generate_data(f):
				file_data = f.read(BUF_SIZE)
				# when lower is the sleep value, faster will be the reading,
				sleep(0.00001) # but it will increase the CPU usage
				yield file_data

			with open(self.name, 'rb') as f:
				for _ in range(times):
					if bars:
						with alive_bar(times, bar='blocks', spinner='dots') as bar:
							yield from generate_data(f)
							bar()
					else:
						yield from generate_data(f)

	def update_data(self, sumtype, generated_data):
		"""Updates binary data to the sumtype's class."""
		for file_data in generated_data:
			self.hlist[sumtype].update(file_data)

	def checksum(self, sumtype) :
		"""Compares file's sum with givensum."""
		if hexa_to_int(self.hlist[sumtype].hexdigest()) == self.integer_sum:
			print(clr(f"{self.name} O", "green"))
		else:
			print(clr(f"{self.name} X", "red"))


class Process(object):

	def __init__(self, *files, sumtype=None):
		if files:
			self.files = files
		else:
			self.files = []
		self.sumtype = sumtype

	def analyse_files(self):
		"""Return tuple `(found, unfound)` with files that have been found and not found."""
		found = None
		unfound = None
		if self.files:
			found = [f for f in self.files if f.existence is True]
			unfound = [f.name for f in self.files if f not in found]
		return found, unfound

	def add_file(self, fileid):
		self.files.append(fileid)

	def define_sumtype(self, sumtype):
		if sumtype in sumtypes_list:
			self.sumtype = sumtype
		else:
			print_error(f"Unsupported sumtype: {sumtype!r}")

	def check_process(self):
		"""Check and Compare the hash sum."""
		fileid = self.files[0]
		if not fileid.existence:
			print_error(f"File not found: {fileid.name!r}")
		elif not self.sumtype:
			print_error("Sumtype is Undefined!")
		else:
			fileid.update_data(self.sumtype, fileid.gen_data())
			fileid.checksum(self.sumtype)

	def only_show_sum(self):
		"""Only calculates and print the file's hash sum."""
		found, unfound = self.analyse_files()
		if not self.sumtype:
			print_error("Sumtype is Undefined")
		elif found:
			with alive_bar(len(found), bar='blocks', spinner='dots') as bar:
				for fileid in found:
					fileid.update_data(self.sumtype, fileid.gen_data(bars=False))
					print(f"{fileid.get_hashsum(self.sumtype)} {fileid.name}")
					bar()

		if unfound:
			print("\nThe files below weren't found:")
			for filename in unfound:
				print(" -> ", filename)

	def check_multifiles(self):
		"""Checks and compare the hash sums of more than one files."""
		found, unfound = self.analyse_files()
		if not self.sumtype:
			print_error("Sumtype is Undefined")
		elif found:
			with alive_bar(len(found), bar='blocks', spinner='dots') as bar:
				for fileid in found:
					fileid.update_data(self.sumtype, fileid.gen_data(bars=False))
					fileid.checksum(self.sumtype)
					bar()

		if unfound:
			print("\nThe files below weren't found:")
			for filename in unfound :
				print(" -> ", filename)

	def show_allsums(self):
		"""Print all supported hash sums of one file."""
		fileid = self.files[0]
		
		if fileid.existence is True:
			print("Calculating sum...")
			generated_data = list(fileid.gen_data())
		
			with alive_bar(len(fileid.hlist.keys()), spinner='waves') as bar:
				print("Getting hashes...")
				for sumtype in fileid.hlist.keys():
					fileid.update_data(sumtype, generated_data)
					# when lower is the sleep value, faster will be the reading,
					sleep(0.00001)
					# but it will increase the CPU usage
					bar()

			for sumtype in fileid.hlist.keys():
				print(f"{sumtype}sum: {fileid.get_hashsum(sumtype)} {fileid.name}")
		else:
			print_error(f"{fileid.name!r} was not found!")

	def write(self):
		found, unfound = self.analyse_files()
		if found and self.sumtype:
			textfile = self.sumtype + 'sum.txt'
			with open(textfile, 'w') as txt:
				for fileid in found:
					txt.write(f"{fileid.get_hashsum(self.sumtype)} {fileid.name}\n")

		del unfound
		#if unfound:
		#	print("\nThe files below weren't found:")
		#	for filename in unfound :
		#		print(" -> ", filename)
			
