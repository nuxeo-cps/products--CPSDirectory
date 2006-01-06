#!/usr/bin/python
# -*- encoding: iso-8859-1 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
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
from functions import open, initialize, init, explode_dn, explode_rdn, get_option, set_option
import ldapobject
import filter

NO_SUCH_OBJECT = 'NO_SUCH_OBJECT'
SIZELIMIT_EXCEEDED = 'SIZELIMIT_EXCEEDED'
SERVER_DOWN = 'SERVER_DOWN'
INVALID_DN_SYNTAX = 'INVALID_DN_SYNTAX'
UNWILLING_TO_PERFORM = 'UNWILLING_TO_PERFORM'
INAPPROPRIATE_AUTH = 'INAPPROPRIATE_AUTH'
INVALID_CREDENTIALS = 'INVALID_CREDENTIALS'
INSUFFICIENT_ACCESS = 'INSUFFICIENT_ACCESS'
SCOPE_BASE = 0
SCOPE_ONELEVEL = 1
SCOPE_SUBTREE = 2
from fakeldap import MOD_ADD, MOD_DELETE, MOD_REPLACE
OPT_REFERRALS = 8
OPT_TIMELIMIT = 4
OPT_SIZELIMIT = 3
OPT_NETWORK_TIMEOUT = 20485
OPT_PROTOCOL_VERSION = 17

VERSION2 = 2
VERSION3 = 3

class LDAPError(Exception):
    pass

