#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from config import config,PREVIEW_DIR
import ca

import os.path
from functools import wraps
from jinja2 import Template
from flask import Flask, render_template, request, send_from_directory, Response
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
		<img style="max-width: 90%;" src="/img/{{ p }}" />
	{% endfor %}
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
	#preview = [p % {'previewdir':config.PREVIEW_DIR} for p in config.CAPTURE_PREVIEW]
	#preview = zip(preview, range(len(preview)))
	#preview = [p[1] for p in preview if os.path.isfile(p[0])]
	preview=""
	template = Template(site)
	return template.render(preview=preview, refresh=config['UI']['REFRESH_RATE'],manual=(manual_stop!=None))


@app.route("/img/<img>")
@checkCredentials
def img(img):
	'''Serve the preview image with the given id
	'''
	f = ''
	#try:
	#	f = config.CAPTURE_PREVIEW[int(img)] % {'previewdir':config.PREVIEW_DIR}
	#	if os.path.isfile(f):
	#		[path,filename] = f.rsplit('/' , 1)
	#		return send_from_directory(path, filename)
	#except:
	#	pass
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
