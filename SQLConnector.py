# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Tarek Ziadé <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id: SQLConnector.py 48272 2006-08-10 15:35:26Z atchertchian $
""" Allow sql connectors to be used by genericsetup,
    by programmaticaly adding a interface in the classes
"""
from zope.interface.declarations import classImplements
from interfaces import IPluggableConnection

def patch_connector(connector):
    classImplements(connector, IPluggableConnection)

connectors = []

# XXX making ZMySQLDA providing IPluggableConnection
# other plug can be added here as well
try:
    from Products.ZMySQLDA.DA import Connection
    connectors.append(Connection)
    # also patching the constructor to avoid
    # an error when generic setup creates the instance
    # with just the id
    def __init__(self, id, title='', connection_string='', check=None):
        Connection.old__init__(self, id, title, connection_string, check)
    Connection.old__init__ = Connection.__init__
    Connection.__init__ = __init__
except ImportError:
    pass

for connector in connectors:
    patch_connector(connector)
