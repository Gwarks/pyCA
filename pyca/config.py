# -*- coding: utf-8 -*-
import os
import yaml

CAPTURE_DIR         = '%s/../recordings' % os.path.dirname(os.path.abspath(__file__))
PREVIEW_DIR         = '%s/../preview' % os.path.dirname(os.path.abspath(__file__))

f=open('%s/../config.yaml' % os.path.dirname(os.path.abspath(__file__)))
config=yaml.load(f)
f.close()
del f

