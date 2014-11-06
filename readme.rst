PyCA – Matterhorn Capture Agent
===============================

**PyCA** is a fully functional Opencast Matterhorn [MH]_ Capture Agent written
in about 300 lines Python code. It is free software licenced under the terms of
both the FreeBSD license and the LGPL. The target systems are primarily small
devices like the Raspberry Pi [RPi]_ although it can, of course, also run on a
normal PC without a problem.

Installation
************

Here is a short summary for Debian based OS like Raspian::

  git clone https://github.com/lkiesow/pyCA.git
  cd pyCA
  sudo apt-get install python-virtualenv python-dev libcurl-gnutls-dev
  virtualenv venv
  . ./venv/bin/activate
  pip install icalendar python-dateutil pycurl
  vim pyca/config.py
  python pyca.py run

For RedHat bases systems like Fedora it's almost the same::

  git clone https://github.com/lkiesow/pyCA.git
  cd pyCA
  sudo yum install python-virtualenv
  virtualenv venv
  . ./venv/bin/activate
  pip install icalendar python-dateutil pycurl
  vim pyca/config.py  <-- Edit the configuration
  python pyca.py run

Todo
****
* Confidence monitoring
* Create daemon mode


.. [MH] http://opencast.org/matterhorn
.. [RPi] http://www.raspberrypi.org/
