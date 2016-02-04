import codecs
from setuptools import find_packages, setup

import digestive


setup(
    name='digestive',
    version=digestive.__version__,
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=['decorator', 'PyYAML'],
    tests_require=['pyhamcrest', 'mock', 'pytest'],
    extras_require={
        'sha3': 'pysha3',
    },
    entry_points={
        'console_scripts': {
            'digestive = digestive.main:main'
        }
    }
)
