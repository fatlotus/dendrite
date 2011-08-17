#!/usr/bin/env python

from distutils.core import setup

setup(
   name='Dendrite',
   version='1.0',
   description='An evented server for the GO mobile notification service',
   author='Jeremy Archer',
   author_email='fatlotus@gmail.com',
   packages='dendrite',
   url='http://www.github.com/globusonline/dendrite',
   package_dir={ '' : 'src' },
)