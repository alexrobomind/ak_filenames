from setuptools import setup, find_packages

setup(
	name = 'fzj-ak-filenames',
	version = '2.2',
	author = 'Alexander Knieps',
	author_email = 'a.knieps@fz-juelich.de',
	description = 'Filename parser & writer for fusion device configuration-related files',
	url = 'https://github.com/alexrobomind/ak_filenames',
	py_modules = ['ak_filenames'],
	install_requires = [
		'textX>=2.1.0',
	]
);

