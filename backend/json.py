#!/usr/bin/python3
#-*- coding: utf-8 -*-
# This code is PEP8-compliant. See http://www.python.org/dev/peps/pep-0008/.
"""

Wyrd In: Time tracker and task manager
CC-Share Alike 2012 © The Wyrd In team
https://github.com/WyrdIn

"""
#import json

#data = [ { 'a':'A', 'b':(2, 4), 'c':3.0 } ]
#print(json.dumps(data, sort_keys=True))
import json
import tempfile
#encode decode basics
data = [ { 'a':'A', 'b':(2, 4), 'c':3.0 } ]
data_string = json.dumps(data)
print ('ENCODED:', data_string)

decoded = json.loads(data_string)
print ('DECODED:', decoded)

print ('ORIGINAL:', type(data[0]['b']))
print ('DECODED :', type(decoded[0]['b']))

#file ops
f = tempfile.NamedTemporaryFile(mode='w+')
json.dump(data, f)
f.flush()

print (open(f.name, 'r').read())
