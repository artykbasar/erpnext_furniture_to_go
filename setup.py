# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')

# get version from __version__ variable in erpnext_furniture_to_go/__init__.py
from erpnext_furniture_to_go import __version__ as version

setup(
	name='erpnext_furniture_to_go',
	version=version,
	description='ERPNext integration with Furniture To Go',
	author='Artyk Basarov',
	author_email='info@artyk.co.uk',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
