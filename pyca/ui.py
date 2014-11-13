#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys

from config import config,PREVIEW_DIR
import ca

import os.path
from functools import wraps
from jinja2 import Template
from flask import Flask, render_template, request, send_from_directory, Response
from itertools import izip,count
import signal
from twisted.internet import reactor
from twisted.web import static, server
from twisted.web.wsgi import WSGIResource
import datetime

app = Flask(__name__)

site = '''
<!doctype html>
<html>
<head>
	<meta http-equiv="refresh" content="{{ refresh }}; URL=/">
	<title>pyCA</title>
</head>
<body style="text-align: center;">
	<a href='/manual'>
	{% if manual %}
		Stop
	{% else %}
		Start
	{% endif %}
	Capture</a>
	{% for p in preview %}
		<img style="max-width: 42%;" src="/img/{{ p }}" />
	{% endfor %}
	<table border="1"><tr><th>Start</th><th>Stop</th><th>ID</th></tr>
	{% for s in schedule %}
		<tr><td>{{ df(s[0]) }}</td><td>{{ df(s[1]) }}</td><td>{{ s[2] }}</td></tr>
	{% endfor %}
	</table>
</body>
</html>
'''
manual_stop=None

def checkCredentials(func):
	@wraps(func)
	def f(*p,**k):
		if not request.authorization \
				or request.authorization.username != config['UI']['USER'] \
				or request.authorization.password != config['UI']['PASSWD']:
			return Response('pyCA', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
		return func(*p,**k)
	return f


@app.route("/")
@checkCredentials
def home():
	preview = [i for i,p in izip(count(),config['CAPTURE_PIPES']) if p['preview']]
	return Template(site).render(preview=preview,refresh=config['UI']['REFRESH_RATE'],manual=(manual_stop!=None),schedule=ca.schedule,df=datetime.datetime.fromtimestamp)


@app.route("/img/<img>")
@checkCredentials
def img(img):
	'''Serve the preview image with the given id
	'''
	try:
		f='%s/%s.jpeg' % (PREVIEW_DIR,img)
		if os.path.isfile(f):
			[path,filename] = f.rsplit('/' , 1)
			return send_from_directory(path, filename)
	except:
		pass
	return '', 404


@app.route("/manual")
@checkCredentials
def manual():
	global manual_stop
	if manual_stop:
		manual_stop()
		manual_stop=None
	else:
		manual_stop=ca.manual()
	return home()

def run():
	app.debug=True
	reactor.listenTCP(5000,server.Site(WSGIResource(reactor,reactor.getThreadPool(),app)))
	ca.register_ca(status='idle')
	def onShutdown():
		if manual_stop:
			manual_stop()
        reactor.addSystemEventTrigger('before', 'shutdown',onShutdown)
	ca.control_loop()
	reactor.run()
	ca.register_ca(status='unknown')
