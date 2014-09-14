Digestive :cookie:
==================

[![Build Status](http://img.shields.io/travis/akaIDIOT/Digestive/master.svg?style=flat)](https://travis-ci.org/akaIDIOT/Digestive)
[![Coverage Status](https://img.shields.io/coveralls/akaIDIOT/Digestive/master.svg?style=flat)](https://coveralls.io/r/akaIDIOT/Digestive)

----

Run several digest algorithms on the same data efficiently.

Installation and use
--------------------

Run `python3 setup.py install` to install both the package and commandline script `digestive`.
Use `digestive --help` to view commandline options.

Everything accessible from the console command is available from python:

- `digestive.io`: classes `Source` and `Sink`, used to read blocks of data from a source and provide a common interface to digest algorithms;
- `digestive.hash`: `Sink` implementations wrapping common hash digests MD5, SHA1, SHA256 and SHA512;
- `digestive.entropy`: `Sink` implementation to calculate the binary entropy of a source;
- `digestive.main`: functions used by the commandline script to parse arguments and efficiently process sources.
