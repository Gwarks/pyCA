#!/bin/env python
# -*- coding: utf-8 -*-
'''
	python-matterhorn-ca
	~~~~~~~~~~~~~~~~~~~~

	:copyright: 2014, Lars Kiesow <lkiesow@uos.de>
	:license: LGPL – see license.lgpl for more details.
'''

# Set default encoding to UTF-8
import sys

import os
import time
import pycurl
import dateutil.tz
from base64 import b64decode
import logging
import icalendar
from datetime import datetime
import os.path
import gst
import xml.etree.ElementTree as ElementTree
from twisted.internet import task,reactor
from itertools import izip,count

schedule=[]

if sys.version_info[0] == 2:
	from cStringIO import StringIO as bio
else:
	from io import BytesIO as bio

from config import config,CAPTURE_DIR,PREVIEW_DIR


def register_ca(address=config['UI']['URI'], status='idle'):
	params = [('address',address), ('state',status)]
	print(http_request('/capture-admin/agents/%s' % config['CAPTURE_AGENT_NAME'], params))


def recording_state(recording_id, status='upcoming'):
	params = [('state',status)]
	print(http_request('/capture-admin/recordings/%s' % recording_id, params))

def get_schedule():
	try:
		vcal = http_request('/recordings/calendars?agentid=%s' % config['CAPTURE_AGENT_NAME'])
	except Exception as e:
		print('ERROR: Could not get schedule: %s' % e.message)
		return []

	cal = None
	try:
		cal = icalendar.Calendar.from_string(vcal)
	except:
		cal = icalendar.Calendar.from_ical(vcal)
	events = []
	for event in cal.walk('vevent'):
		dtstart = unix_ts(event.get('dtstart').dt.astimezone(dateutil.tz.tzutc()))
		dtend   = unix_ts(event.get('dtend').dt.astimezone(dateutil.tz.tzutc()))
		uid     = event.get('uid').decode()

		# Ignore events that have already ended
		if dtend > get_timestamp():
			events.append( (dtstart,dtend,uid,event) )

	return sorted(events, key=lambda x: x[0])


def unix_ts(dt):
	epoch = datetime(1970, 1, 1, 0, 0, tzinfo = dateutil.tz.tzutc())
	delta = (dt - epoch)
	return delta.days * 24 * 3600 + delta.seconds


def get_timestamp():
	if config['IGNORE_TZ']:
		return unix_ts(datetime.now())
	return unix_ts(datetime.now(dateutil.tz.tzutc()))


def get_config_params(properties):
	param = []
	wdef = 'full'
	for prop in properties.split('\n'):
		if prop.startswith('org.opencastproject.workflow.config'):
			k,v = prop.split('=',1)
			k = k.split('.')[-1]
			param.append((k, v))
		elif prop.startswith('org.opencastproject.workflow.definition'):
			wdef = prop.split('=',1)[-1]
	return wdef, param


def start_capture(schedule):
	now = get_timestamp()
	print('%i: start_recording...' % now)
	duration = schedule[1] - now
	recording_id = schedule[2]
	recording_name = 'recording-%s-%i' % (recording_id, now)
	recording_dir  = '%s/%s' % (CAPTURE_DIR, recording_name)
	try:
		os.mkdir(CAPTURE_DIR)
	except:
		pass
	os.mkdir(recording_dir)

	# Set state
	try:
		register_ca(status='capturing')
		recording_state(recording_id,'capturing')
	except:
		# Ignore it if it does not work (e.g. network issues) as it's more
		# important to get the recording as to set the correct current state in
		# the admin ui
		pass

	tracks = []
	try:
		stop=recording_command(recording_dir,recording_name)
	except Exception as e:
		print str(e)
		# Update state
		recording_state(recording_id,'capture_error')
		register_ca(status='idle')
		return False
	def f():
		tracks=stop()
		# Put metadata files on disk
		attachments = schedule[-1].get('attach')
		workflow_config=''
		for a in attachments:
			value = b64decode(a.decode())
			if value.startswith('<'):
				if '<dcterms:temporal>' in value:
					f = open('%s/episode.xml' % recording_dir, 'w')
					f.write(value)
					f.close()
				else:
					f = open('%s/series.xml' % recording_dir, 'w')
					f.write(value)
					f.close()
			else:
				workflow_def, workflow_config = get_config_params(value)
				with open('%s/recording.properties' % recording_dir, 'w') as f:
					f.write(value)

		# Upload everything
		try:
			register_ca(status='uploading')
			recording_state(recording_id,'uploading')
		except:
			# Ignore it if it does not work (e.g. network issues) as it's more
			# important to get the recording as to set the correct current state in
			# the admin ui
			pass

		try:
			ingest(tracks, recording_name, recording_dir, recording_id, workflow_def,
					workflow_config)
		except:
			print('ERROR: Something went wrong during the upload')
			# Update state if something went wrong
			try:
				recording_state(recording_id,'upload_error')
				register_ca(status='idle')
			except:
				# Ignore it if it does not work (e.g. network issues) as it's more
				# important to get the recording as to set the correct current state
				# in the admin ui
				pass
			return False

		# Update state
		try:
			recording_state(recording_id,'upload_finished')
			register_ca(status='idle')
		except:
			# Ignore it if it does not work (e.g. network issues) as it's more
			# important to get the recording as to set the correct current state in
			# the admin ui
			pass
	reactor.callLater(duration,f)
	return True


def http_request(endpoint, post_data=None):
	buf = bio()
	c = pycurl.Curl()
	url = '%s%s' % (config['ADMIN_SERVER']['URL'], endpoint)
	c.setopt(c.URL, url.encode('ascii', 'ignore'))
	if post_data:
		c.setopt(c.HTTPPOST, post_data)
	c.setopt(c.WRITEFUNCTION, buf.write)
	c.setopt(pycurl.HTTPAUTH, pycurl.HTTPAUTH_DIGEST)
	c.setopt(pycurl.USERPWD, "%s:%s" % \
			(config['ADMIN_SERVER']['USER'],config['ADMIN_SERVER']['PASSWD']))
	c.setopt(c.HTTPHEADER, ['X-Requested-Auth: Digest'])
	c.perform()
	status = c.getinfo(pycurl.HTTP_CODE)
	c.close()
	if status / 100 != 2:
		raise Exception('ERROR: Request to %s failed (HTTP status code %i)' % \
				(endpoint, status))
	result = buf.getvalue()
	buf.close()
	return result


def ingest(tracks, recording_name, recording_dir, recording_id, workflow_def,
		workflow_config=[]):

	# create mediapackage
	print('Creating new mediapackage')
	mediapackage = http_request('/ingest/createMediaPackage')

	# add episode dc catalog
	if os.path.isfile('%s/episode.xml' % recording_dir):
		print('Adding episode DC catalog')
		dc = ''
		with open('%s/episode.xml' % recording_dir, 'r') as f:
			dc = f.read()
		fields = [
				('mediaPackage', mediapackage),
				('flavor', 'dublincore/episode'),
				('dublinCore', dc)
			]
		mediapackage = http_request('/ingest/addDCCatalog', fields)

	# add series dc catalog
	if os.path.isfile('%s/series.xml' % recording_dir):
		print('Adding series DC catalog')
		dc = ''
		with open('%s/series.xml' % recording_dir, 'r') as f:
			dc = f.read()
		fields = [
				('mediaPackage', mediapackage),
				('flavor', 'dublincore/series'),
				('dublinCore', dc)
			]
		mediapackage = http_request('/ingest/addDCCatalog', fields)

	# add track
	for (flavor, track) in tracks:
		print('Adding track (%s)' % flavor)
		fields = [
				('mediaPackage', mediapackage), ('flavor', flavor),
				('BODY1', (pycurl.FORM_FILE, track.encode('ascii', 'ignore')))
			]
		mediapackage = http_request('/ingest/addTrack', fields)

	# ingest
	print('Ingest recording')
	fields = [
			('mediaPackage', mediapackage),
			('workflowDefinitionId', workflow_def),
			('workflowInstanceId', recording_id.encode('ascii', 'ignore'))
			]
	fields += workflow_config
	mediapackage = http_request('/ingest/ingest', fields)

def control_loop():	
	local={'next':None,'call':None}
	def f():
		global schedule
		schedule=get_schedule() or schedule
		if schedule:
			if schedule[0][2]!=local['next']:
				if local['call']:
					local['call'].cancel()
				local['next']=schedule[0][2]
				local['call']=reactor.callLater(schedule[0][0]-get_timestamp(),start_capture,schedule[0])
	task.LoopingCall(f).start(config['UPDATE_FREQUENCY'])

def recording_command(rec_dir, rec_name):
	pipe=gst.Pipeline()
	tracks=[]
	for i,launch in izip(count(),config['CAPTURE_PIPES']):
		s={'file':'%s/%s-%d.%s'%(rec_dir,rec_name,i,launch['suffix']),'preview':'%s/%s.jpeg'%(PREVIEW_DIR,i)}
		pipe.add(gst.parse_bin_from_description(launch['launch']%s,False))
		tracks.append((launch['flavor'],s['file']))
	if pipe.set_state(gst.STATE_PLAYING)==gst.StateChangeReturn(gst.STATE_CHANGE_FAILURE):
		return None
	def f():
		pipe.set_state(gst.STATE_NULL)
		return tracks
	return f

def write_dublincore_episode(recording_name,recording_dir,recording_id,start,end):
	dc=ElementTree.Element('dublincore')
	dc.attrib['xmlns']="http://www.opencastproject.org/xsd/1.0/dublincore/"
	dc.attrib['xmlns:dcterms']="http://purl.org/dc/terms/"
	ElementTree.SubElement(dc,'dcterms:license').text='Creative Commons 3.0: Attribution-NonCommercial-NoDerivs'
	ElementTree.SubElement(dc,'dcterms:temporal').text='start=%s; end=%s; scheme=W3C-DTF;'%(datetime.utcfromtimestamp(start).isoformat(' '),datetime.utcfromtimestamp(end).isoformat(' '))
	ElementTree.SubElement(dc,'dcterms:spatial').text=config['CAPTURE_AGENT_NAME']
	ElementTree.SubElement(dc,'dcterms:identifier').text=recording_id
	ElementTree.SubElement(dc,'dcterms:title').text=recording_name
	ElementTree.ElementTree(dc).write('%s/episode.xml'%recording_dir,encoding="UTF-8")

def test():
	register_ca(status='capturing')
	timestamp=get_timestamp();
	recording_name = '%s-test-%i' % (config['CAPTURE_AGENT_NAME'],timestamp)
	recording_dir  = '%s/%s' % (CAPTURE_DIR, recording_name)
	try:
		os.mkdir(CAPTURE_DIR)
	except:
		pass	
	os.mkdir(recording_dir)
	stop=recording_command(recording_dir, recording_name)
	time.sleep(60)
	tracks=stop()
	register_ca()
	write_dublincore_episode(recording_name,recording_dir,recording_name,timestamp,timestamp+60)
	#ingest(tracks,recording_name,recording_dir,recording_name,'full')
	register_ca(status='unknown')

def manual():
	register_ca(status='capturing')
	timestamp=get_timestamp();
	recording_name = '%s-manual-%i' % (config['CAPTURE_AGENT_NAME'],timestamp)
	recording_dir  = '%s/%s' % (CAPTURE_DIR, recording_name)
	try:
		os.mkdir(CAPTURE_DIR)
	except:
		pass	
	os.mkdir(recording_dir)
	stop=recording_command(recording_dir, recording_name)
	def f():
		tracks=stop()
		register_ca()
		write_dublincore_episode(recording_name,recording_dir,recording_name,timestamp,get_timestamp())
		ingest(tracks,recording_name,recording_dir,recording_name, 'full')
	return f

