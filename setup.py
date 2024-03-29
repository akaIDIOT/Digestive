import codecs
from setuptools import find_packages, setup

import digestive


setup(
    name='digestive',
    version=digestive.__version__,  # TODO: don't read this from (uninstalled) module
    url='https://github.com/akaIDIOT/Digestive',
    packages=find_packages(),
    description='Run several digest algorithms on the same data efficiently',
    author='Mattijs Ugen',
    author_email=codecs.encode('nxnvqvbg@hfref.abercyl.tvguho.pbz', 'rot_13'),
    license='ISC',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Programming Language :: Python :: 3',
    ],
    install_requires=(
        'decorator',
        'pyyaml'
    ),
    entry_points={
        'console_scripts': {
            'digestive = digestive.main:main'
        }
    }
)
