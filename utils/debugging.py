#!/usr/bin/env python
# vim: set fileencoding=utf-8
"""
NOTE: Use this for private purposes only, it was taken from the Vystadial
project basically without permission.

Matěj
"""

import sys


def pdbhere():
    if 'ipdb' not in sys.modules:
        import ipdb
        ipdb.set_trace()


def pdbonerror():
    def bringup_ipdb(type, value, tb):
        if hasattr(sys, 'ps1') or not sys.stderr.isatty():
        # we are in interactive mode or we don't have a tty-like
        # device, so we call the default hook
            sys.__excepthook__(type, value, tb)
        else:
            import traceback, ipdb
            # we are NOT in interactive mode, print the exception…
            traceback.print_exception(type, value, tb)
            print
            # …then start the debugger in post-mortem mode.
            # pdb.pm() # deprecated
            ipdb.post_mortem(tb) # more “modern”

    sys.excepthook = bringup_ipdb
