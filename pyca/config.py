# -*- coding: utf-8 -*-
import os

CAPTURE_AGENT_NAME  = 'PyCA-test'
IGNORE_TZ           = False
ADMIN_SERVER_URL    = 'http://172.22.28.161:8080'
ADMIN_SERVER_USER   = 'matterhorn_system_account'
ADMIN_SERVER_PASSWD = 'CHANGE_ME'
UPDATE_FREQUENCY    = 60
CAPTURE_DIR         = '%s/../recordings' % os.path.dirname(os.path.abspath(__file__))
PREVIEW_DIR         = CAPTURE_DIR

# Setting this to true will cause the pyCA to not register itself or ingest
# stuff to the admin server. It's useful if you want it as cbackup to another
# CA to just get the files manually if the regular CA fails.
BACKUP_AGENT        = False

########################################################################
## Capture configuration                                               #
########################################################################

# Specify any command you like to use for capturing. You can also execute a
# shell script if you want to. The only thing that is important is that the
# command has to terminate itself in time.
#
# Possible string substitutions you can use are:
# ==============================================
#
#   %(time)s        Time to capture in seconds
#   %(recdir)s      Directory to put recordings in
#   %(recname)s     Autogenerated name of the recording.
#   %(previewdir)s  Directory to put preview images in
#
# Examples:
# =========
#
# Record audio only using FFmpeg:
# -------------------------------
#
# CAPTURE_COMMAND = '''ffmpeg -f alsa -ac 1 -i hw:1 -t %(time)s -c:a flac -ac 1 \
#   -c:v libx264 -preset ultrafast -qp 0 %(recdir)s/%(recname)s.flac'''
#
#
# Record video4linux2 and alsa source:
# ------------------------------------
#
# CAPTURE_COMMAND = '''ffmpeg -f v4l2 -s 1280x720 -i /dev/video1 \
#   -f alsa -ac 1 -i hw:1 -t %(time)s -c:a flac -ac 1 \
#   -c:v libx264 -preset ultrafast -qp 0 %(recdir)s/%(recname)s.mkv'''
#
#
# Record video on a Reaspberry Pi using the camera module:
# --------------------------------------------------------
#
# CAPTURE_COMMAND = '''raspivid -n -t %(time)s000 -b 4000000 -fps 30 -o - | \
#   ffmpeg -r 30 -i pipe:0 -c:v copy %(recdir)s/%(recname)s.mp4'''
#
#
# Record audio using arecord:
# ---------------------------
#
# CAPTURE_COMMAND = '''arecord -c 2 -d %(time)s -r 44100 -f S16_LE -D hw:0 \
#   %(recdir)s/%(recname)s.mp4'''
#
#
# Record video and audio on a Reaspberry Pi using the camera module:
# ------------------------------------------------------------------
#
# CAPTURE_COMMAND = '''raspivid -t %(time)s000 -b 4000000 -fps 30 -o - | \
#   ffmpeg -ac 1 -f alsa -i plughw:1 \
#   -r 25 -i pipe:0 \
#   -filter:a aresample=async=1 \
#   -c:a flac -c:v copy \
#   -t %(time)s -y %(recdir)s/%(recname)s.mp4'''
#
#
# Confidence monitoring
# =====================
#
# A preview image can be generated during the capture process so that the
# currently captured content can be inspected. If FFmpeg is used for capturing
# a commandline for writing such a preview image could look like this:
#
#   ... -t %(time)s -map 0:v -filter:v select='not(mod(n\,50))' \
#       -updatefirst 1 %(recdir)s/preview.jpg
#
# This would write every 50th frame as JPEG to disk.
#
# Example using a test source with confidence monitoring:

#CAPTURE_COMMAND = '''ffmpeg -re -f lavfi -r 25 -i testsrc \
#		-t %(time)s -map 0:v %(recdir)s/%(recname)s.mp4 \
#		-t %(time)s -map 0:v -filter:v select='not(mod(n\,50))' \
#			-updatefirst 1 %(previewdir)s/preview.jpg'''

# Specify the names of the output files as well as their flavor. Multiple
# output files can be specified. The same string substitutions can be made as
# with the capture command.
#CAPTURE_OUTPUT = [('presenter/source', '%(recdir)s/%(recname)s.mp4')]

# Specify a preview image to show in the web UI. If no image is specified, none
# is shown. Multiple images can be specified. The only string substitution
# ehich can be used in here is %(previewdir)s.
# Warning: Files specified in this list will be deleted after the recording is
# finished.
#CAPTURE_PREVIEW = ['%(previewdir)s/preview.jpg']

CAPTURE_PIPES = [
('presenter/source','mpg',True,
'v4l2src device=/dev/video0 ! queue ! video/x-raw-rgb ! ffmpegcolorspace ! ffenc_mpeg2video bitrate=2000000 ! mpegtsmux ! filesink location=%(file)s'),
('presentation/source','mpg',True,
'v4l2src device=/dev/video1 ! queue ! video/x-raw-rgb,framerate=30/1 ! ffmpegcolorspace ! ffenc_mpeg2video bitrate=2000000 ! mpegtsmux ! filesink location=%(file)s'),
('audience/source','mpg',True,
' hdv1394src blocksize="4136" ! queue ! filesink location=%(file)s'),
('presenter/source','ogg',False,
'alsasrc device=hw:0 ! audioconvert ! queue ! vorbisenc ! oggmux ! filesink location=%(file)s'),
]



########################################################################
## UI configuration                                                    #
########################################################################

UI_USER = 'admin'
UI_PASSWD = 'opencast'
UI_REFRESH_RATE = 2
UI_URI = 'http://localhost:5000'
