Digestive :cookie:
==================

[![Build Status](https://img.shields.io/github/workflow/status/akaIDIOT/Digestive/Test%20package.svg?style=flat)](https://github.com/akaIDIOT/Digestive/actions)

----

Run several digest algorithms on the same data efficiently.

Installation and use
--------------------

Run `python3 setup.py install` to install both the package and commandline script `digestive`.
It currently supports the following options (use `digestive --help` to show options after installation):

    usage: digestive [-h] [-m] [-1] [-2] [-5] [--hashes] [-e] [-j JOBS] [-b BYTES]
                     [-p {bytes,speed}] [-P] [-r] [-o OUTPUT]
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
      -3, --sha3-256        calculate SHA3-256 hash
      --sha3-512            calculate SHA3-512 hash
      --hashes              calculate MD5, SHA-1, SHA-256, SHA-512 and SHA3-256
                            hashes (equivalent to -m1253)
      -e, --entropy         calculate binary entropy
      -j JOBS, --jobs JOBS  use up to JOBS threads to process digests (defaults to
                            the number of digests)
      -b BYTES, --block-size BYTES
                            read data in chunks of BYTES at a time (defaults to
                            1M)
      -p {bytes,speed}, --progress {bytes,speed}
                            show progress information (defaults to bytes)
      -P, --no-progress     disable progress output (always disabled for redirected
                            output)
      -r, --recursive       process sources recursively
      -o OUTPUT, --output OUTPUT
                            write yaml-encoded output to file

Everything accessible from the console command is available from python:

- `digestive.io`: classes `Source` and `Sink`, used to read blocks of data from a source and provide a common interface to digest algorithms;
- `digestive.hash`: `Sink` implementations wrapping common hash digests MD5, SHA1, SHA256 and SHA512 (with SHA3-256 and SHA3-512 enabled if they're available);
- `digestive.entropy`: `Sink` implementation to calculate the binary entropy of a source;
- `digestive.main`: functions used by the commandline entry point to parse arguments and efficiently process data sources.
