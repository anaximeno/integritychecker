#!/usr/bin/env python3
""" Common is a support module, which contains the principals methods
and/or functions of this programm."""
# -*- coding: utf-8 -*-
__author__ = "Anaxímeno Brito"
__version__ = '0.4.5-beta'
__license__ = "GNU General Public License v3.0"
__copyright__ = "Copyright (c) 2020-2021 by " + __author__
import os
import sys
import hashlib as hlib
from time import sleep
from typing import Generator, Iterable


class Errors:

	@staticmethod
	def print_error(*err: str, exit: bool = True, err_num: int = 1):
		"""Print the error message and exit.\n
		Keyword args: 
			exit --> if is to exit after showing the error (default: True),
			err_num --> number of the error (default: 1)."""
		error_message = ' '.join(err)
		print("Shazam: Error: %s" % error_message)
		if exit: 
			sys.exit(err_num)

	@staticmethod
	def print_files_not_found(files_not_found: Iterable, exit: bool = False):
		n_not_found = len(files_not_found)
		if n_not_found == 0:
			pass
		elif n_not_found == 1:
			Errors.print_error(f'FileNotFound: {files_not_found[0].get_fullpath()!r}!', exit=exit)
		else:
			print('Files that were not found or cannot be read:')
			
			for file in files_not_found:
				print(f'  -> {file.get_fullpath()!r}')	

			if exit:
				sys.exit(1)


to_install = []
try:
	from termcolor import colored as clr
except ImportError:
	to_install.append('termcolor')
try:
	from alive_progress import alive_bar
except ImportError:
	to_install.append('alive_progress')
finally:
	if any(to_install):
		modules_to_install = ', '.join(to_install)
		Errors.print_error(f"Must install some modules first: {modules_to_install}!",
			"\nInstall them with pip or conda.", exit=True)
	else:
		del to_install


def hexa_to_int(hexa: str):
	"""Receive hexadecimal string and return integer."""
	try: 
		return int(hexa, 16)
	except ValueError:
		Errors.print_error(f"{hexa!r} is not an hexadecimal value!")


def get_hashtype(filename: str):
	"""Analyses the filename and return the hashtype."""
	for stype in Process.HASHTYPES_LIST[::-1]:
		if stype in filename: 
			return stype
	return False


def animate(string: str, sleep_time: float = 0.1):
	lines = string.splitlines()
	for line in lines:
		lag = '\r'
		for char in line:
			lag += char
			sys.stdout.write(lag)
			sys.stdout.flush()
			sleep(sleep_time)
		print('')


class File(object):
	"""This class holds all necessary informations and operations
	for one file object."""

	# Will store files that exists or not.
	Found = []
	Not_Found = []

	def __init__(self, filename: str, given_hashsum: str = '', 
		file_for_check: bool = True, **kwargs):
		self._dir, self._fname = os.path.split(filename)
		if '.' in self._fname:
			self._name, self._extension = os.path.splitext(self._fname)
		else:
			self._name, self._extension = self._fname, ''

		if self._name[0] == '*' and not(self.exists()):
			self._name = self._name[1:]

		# ´givensum´ is the original file sum which is give at the download place.
		self._gsum = given_hashsum

		# ´self._given_integer_sum´ is the integer value of the hash sum,
		# it will be used in comparisons for checking if the values are equal.
		self._given_integer_sum = hexa_to_int(self._gsum) if self._gsum else None
		if file_for_check is True:
			self._calculated_hashes = []
			self.hlist = {
				"md5": hlib.md5(),
				"sha1": hlib.sha1(),
				"sha224": hlib.sha224(),
				"sha256": hlib.sha256(),
				"sha384": hlib.sha384(),
				"sha512": hlib.sha512()
			}

		if self.exists():
			self.Found.append(self)
		else:
			self.Not_Found.append(self)

	def __str__(self):
		return self.get_fullpath()

	def get_name(self):
		return str(self._name)

	def get_extension(self):
		return str(self._extension)

	def get_fullname(self):
		return self.get_name() + self.get_extension()

	def get_dir(self):
		return str(self._dir)

	def get_fullpath(self):
		return os.path.join(self.get_dir(), self.get_fullname())

	def get_size(self):
		if self.exists() is True:
			return os.path.getsize(self.get_fullpath())
		return None
	
	def get_given_sum(self):
		return str(self._gsum)

	def exists(self):
		return os.path.exists(self.get_fullpath())

	def is_readable(self):
		if not self.exists():
			return False
		try:
			with open(self.get_fullpath(), 'rb') as f:
				f.read(1)
			return True
		except UnicodeDecodeError:
			return False

	def get_hashsum(self, hashtype: str):
		"""Return the file's hash sum."""
		if hashtype in self._calculated_hashes:
			return self.hlist[hashtype].hexdigest()
		return None

	def gen_data(self, *, bar_animation: bool = True) -> Generator:
		"""Generates binary data. 
		Keyword arg: 
			bars --> bool (default: True).
		"""
		if self.is_readable() is False:
			err = 'is not readable' if self.exists() else 'was not found'
			Errors.print_error(f"Reading Error: {self.get_fullpath()!r} {err}!", exit=True)

		BUF_SIZE = 32768
		times = (self.get_size() // BUF_SIZE) + (self.get_size() % BUF_SIZE)
		if bar_animation:
			with alive_bar(times, bar='blocks', spinner='dots') as bar:
				with open(self.get_fullpath(), 'rb') as f:
					for _ in range(times):
						yield f.read(BUF_SIZE)
						sleep(Process.SLEEP_VALUE)
						bar()
		else:
			with open(self.get_fullpath(), 'rb') as f:
				for _ in range(times):
					yield f.read(BUF_SIZE)
					sleep(Process.SLEEP_VALUE)

	def read_content(self):
		"""Return a `list with tuples` with the content of the file,
		each tuple has the following structure: `(filesum, filename)`."""
		if self.is_readable() is False:
			Errors.print_error(f'It is not possible to read {self.get_fullname()!r}!')
		try:
			with open(self.get_fullpath(), 'rt') as textfile:
				content = [
					(line.split()[0], line.split()[1]) for line in textfile
				]
			if content:
				return content
			Errors.print_error(f'{self.get_fullpath()!r} is empty!')
		except IndexError:
			Errors.print_error(f'error reading {self.get_fullpath()!r}!')
		except UnicodeDecodeError:
			Errors.print_error(f'Cannot read {self.get_fullpath()!r}!')	

	def update_data(self, hashtype: str, generated_data: Iterable) -> None:
		"""Updates binary data to the hashtype's class."""
		if self.is_readable() is False:
			err = 'is not readable' if self.exists() else 'was not found'
			Errors.print_error(f"Reading Error: {self.name!r} {err}!", exit=True)

		for file_data in generated_data:
			self.hlist[hashtype].update(file_data)
		self._calculated_hashes.append(hashtype)

	def checksum(self, hashtype: str) -> bool:
		"""Compares file's sum with givensum and return the results"""
		return hexa_to_int(self.get_hashsum(hashtype)) == self._given_integer_sum


class Process(object):
	# When lower is the sleep value, faster will be the reading,
	# but it will increase the CPU usage, it can be changed to
	# improve the performance.
	SLEEP_VALUE = 0.00001
	# List of all supported hash sums:
	HASHTYPES_LIST = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]

	def __init__(self):
		# ´self.found´ and ´self.unfound´ store files depending on their
		# existence/readability or not, and below them are their respective lengths.
		self._files_found = File.Found
		self._files_not_found = File.Not_Found

		self._calculted_files = []

	def _show_file_result(self, file: File, hashtype: str):
		color = "green" if file.checksum(hashtype) is True else "red"
		print(clr(f"{file.get_fullpath()}", color))

	def checkfile(self, file: File, hashtype: str, **kwargs):
		"""Check and Compare the hash sum."""
		file_data = kwargs['file_data'] if 'file_data' in kwargs else None
		bar_animation  = kwargs['bar_animation'] if 'bar_animation' in kwargs else True
		verbosity = kwargs['verbosity'] if 'verbosity' in kwargs else True
		found, _ = self._search_files([file])

		if any(found) is False:
			Errors.print_error(f'{file.get_fullpath()!r} was not found!')

		file.update_data(hashtype=hashtype,
			generated_data=file_data or file.gen_data(bar_animation=bar_animation))
		print('\n--> File: ', end='')
		self._show_file_result(file, hashtype)
		if verbosity:
			print(f"| Given      Hash Sum:  {file.get_given_sum()!r}")
			print(f"| Calculated Hash Sum:  {file.get_hashsum(hashtype)!r}")
			print("-------------")

	def calculate_sum(self, files: Iterable, hashtype: str, verbosity: bool = True):
		"""Calculates and prints the file's hash sum"""
		found, not_found = self._search_files(files)
		n_found = len(found)

		if n_found != 0:
			print("\t\tCalculating Hashes...")
			with alive_bar(n_found, bar='blocks', spinner='dots') as bar:
				for file in found:
					file.update_data(hashtype, file.gen_data(bar_animation=False))
					if verbosity:
						print(f"{file.get_hashsum(hashtype)} {file.get_fullpath()}")
					bar()
		
		if found and not_found:
			print()  # Skip one line

		Errors.print_files_not_found(not_found)

	def checkfiles(self, files: Iterable, hashtype: str, verbosity=False):
		"""Checks and compare the hash sums of more than one files."""
		found, not_found = self._search_files(files)
		n_found = len(found)
		if n_found == 0:
			Errors.print_files_not_found(not_found, exit=True)
			Errors.print_error('Files not recognized!')
		elif n_found == 1:
			self.checkfile(found[0], hashtype, verbosity=verbosity)
		else:
			if verbosity:
				print("\tCalculating Binaries...")
				files_data = []

			with alive_bar(n_found, bar='blocks', spinner='dots') as bar:
				for file in found:
					if verbosity:
						files_data.append(list(file.gen_data(bar_animation=False)))
					else:
						file.update_data(
							hashtype=hashtype, 
							generated_data=file.gen_data(bar_animation=False))
						self._show_file_result(file, hashtype)
					bar()

			if verbosity:
				for file, file_data in zip(found, files_data):
					self.checkfile(file, hashtype, file_data=file_data, bar_animation=False)
		
		Errors.print_files_not_found(not_found)

	def totalcheck(self, files: Iterable):
		"""Print all supported hash sums of one file."""
		found, not_found = self._search_files(files)
		n_found = len(found)

		if n_found == 0:
			Errors.print_files_not_found(not_found, exit=True)

		print("\tCalculating Hashes...")
		generated_datas = [list(file.gen_data()) for file in found]

		print("\n\tGetting Hash Sums...")
		with alive_bar(len(found[0].hlist.keys()) * n_found, spinner='waves') as bar:
			for file, generated_data in zip(found, generated_datas):
				for hashtype in file.hlist.keys():
					file.update_data(hashtype, generated_data)
					sleep(Process.SLEEP_VALUE)
					bar()
		print("\n")

		for n, file in enumerate(found):
			if n > 0 and n < n_found:
				print("\n")
			print(f"--> {file.get_fullname()!r}:")
			for hashtype in file.hlist.keys():
				print(f"| {hashtype}sum: {file.get_hashsum(hashtype)} {file.get_fullpath()}")
			print('---------------')

		Errors.print_files_not_found(not_found)

	def _search_files(self, files: Iterable):
		files = set(files)
		found = list(files.intersection(self._files_found))
		not_found = list(files.intersection(self._files_not_found))
		return found, not_found

	def write(self, files: Iterable, hashtype: str, name: str = None):
		found, _ = self._search_files(files)
		if len(found) != 0:
			filename = name or hashtype + 'sum.txt'
			with open(filename, 'w') as txt:
				for file in found:
					txt.write(f"{file.get_hashsum(hashtype)} {file.get_fullpath()}\n")
			animate(f"\nFile: {filename!r} Created!", sleep_time=0.064)			
		else:
			Errors.print_error('Files not found, cannot save the file!')

