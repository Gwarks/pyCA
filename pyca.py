#!/usr/bin/python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
import os

if __name__ == '__main__':
	if sys.argv[1] in('start','stop','status'):
		os.system("zdaemon -p './pyca.py ui' "+sys.argv[1])
	elif sys.argv[1]=='test':
		from pyca import ca
		ca.test()
	elif sys.argv[1]=='ui':
		from pyca import ui
		ui.run()
	else:
		print('Usage: %s start | stop | status | test | ui' % sys.argv[0])
