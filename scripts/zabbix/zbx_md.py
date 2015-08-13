#!/usr/bin/env python

from glob import glob
import os
import json

devices = []

for devpath in glob('/sys/block/md*'):
    device = os.path.basename(devpath)
    devices += [{'{#MDDEV}':device}]
    for prop in os.listdir(os.path.join(devpath,'md')):
        proppath = os.path.join(devpath,'md',prop)
        if (not os.path.isfile(proppath)):
            continue
        if (not os.access(proppath, os.R_OK)):
            # write-only file, ignore
            continue
        try:
            f = open(proppath, 'r')
            val = f.read()
        except:
            continue
        print 'md[%s,%s]: %s' % (device,prop,val),

print 'md.discovery:', json.dumps({'data':devices})
