PyCA – Matterhorn Capture Agent
===============================

**PyCA** is a fully functional Opencast Matterhorn [MH]_ Capture Agent written
in about 300 lines Python code. It is free software licenced under the terms of
both the FreeBSD license and the LGPL. The target systems are primarily
normal PCs.

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

.. [MH] http://opencast.org/matterhorn
