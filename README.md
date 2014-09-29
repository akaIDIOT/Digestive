Digestive :cookie:
==================

[![Build Status](http://img.shields.io/travis/akaIDIOT/Digestive/master.svg?style=flat)](https://travis-ci.org/akaIDIOT/Digestive)
[![Coverage Status](https://img.shields.io/coveralls/akaIDIOT/Digestive/master.svg?style=flat)](https://coveralls.io/r/akaIDIOT/Digestive)

----

Run several digest algorithms on the same data efficiently.

Installation and use
--------------------

Run `python3 setup.py install` to install both the package and commandline script `digestive`.
It currently supports the following options (use `digestive --help` to show options after installation):

    usage: main.py [-h] [-m] [-1] [-2] [-5] [--hashes] [-e] [-j JOBS] [-b BYTES]
                   [-f {auto,raw,ewf}] [-P]
                   FILE [FILE ...]
    
    run multiple digests on files
    
    positional arguments:
      FILE                  input files
    
    optional arguments:
      -h, --help            show this help message and exit
      -m, --md5             calculate MD5 hash
      -1, --sha1            calculate SHA-1 hash
      -2, --sha256          calculate SHA-256 hash
      -5, --sha512          calculate SHA-512 hash
      --hashes              calculate MD5, SHA-1, SHA-256 and SHA-512 hashes
                            (equivalent to -m125)
      -e, --entropy         calculate binary entropy
      -j JOBS, --jobs JOBS  use up to JOBS threads to process digests (defaults to
                            the number of digests)
      -b BYTES, --block-size BYTES
                            read data in chunks of BYTES at a time (defaults to
                            1M)
      -f {auto,raw,ewf}, --format {auto,raw,ewf}
                            specify source format (defaults to auto)
      -P, --no-progress     disable progress output (always disabled for piped
                            output)

**Note:** EWF-support requires version 2 of [`libewf`](https://code.google.com/p/libewf/).
Ubuntu or Debian-based systems will likely find this package named `libewf2`, `libewf1` won't work.
Other distributions might not make this distinctions; look for for `libewf.so.2`.

Everything accessible from the console command is available from python:

- `digestive.io`: classes `Source` and `Sink`, used to read blocks of data from a source and provide a common interface to digest algorithms;
- `digestive.ewf`: class `EWFSource` to read blocks of data from EWF filesets and the corresponding functions interfacing with [`libewf`](https://code.google.com/p/libewf/);
- `digestive.hash`: `Sink` implementations wrapping common hash digests MD5, SHA1, SHA256 and SHA512;
- `digestive.entropy`: `Sink` implementation to calculate the binary entropy of a source;
- `digestive.main`: functions used by the commandline entry point to parse arguments and efficiently process data sources.
