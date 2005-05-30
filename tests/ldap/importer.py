#!/usr/bin/python
# -*- encoding: iso-8859-1 -*-
# (C) Copyright 2003 Nuxeo SARL <http://nuxeo.com>
# Authors:
# Tarek Ziadé <tz@nuxeo.com>
# Anahide Tchertchian <at@nuxeo.com>
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
# $Id$
"""
Perform replacements in sys.modules to be able to run tests with fake ldap
classes/methods
"""

import sys

from Products.CPSDirectory.tests import ldap
from Products.CPSDirectory.tests.ldap import ldapobject
from Products.CPSDirectory.tests.ldap import functions

modules_to_fake = {
    'ldap' : ldap,
    'ldap.ldapobject': ldapobject,
    'ldap.functions': functions,
    # XXX add other modules that need to be faked here
    }

modules_to_del = [
    'ldap.schema.models',
    'ldap.filter',
    'ldap.cidict',
    'ldapurl',
    'ldap.schema.subentry',
    'ldap.schema',
    'ldap.schema.tokenizer',
    '_ldap',
    ]

# None modules (deleting them to clear up sys.modules)
modules_to_del.extend([
    'ldap.schema.UserDict',
    'ldap.traceback',
    'ldap.thread',
    'ldap.ldap',
    'ldap.threading',
    'ldap.schema.types',
    'ldap.UserDict',
    'Products.LDAPUserGroupsFolder.ldap',
    'ldap.string',
    'ldap.sys',
    'ldap._ldap',
    'ldap.time',
    ])

for module_id, module in modules_to_fake.items():
    if module_id in sys.modules.keys():
        del sys.modules[module_id]
    sys.modules[module_id] = module

for module_id in modules_to_del:
    if module_id in sys.modules.keys():
        del sys.modules[module_id]

# debug log to show what modules are in sys.modules
#sys_ldap_keys = [(key, value) for key, value in sys.modules.items()
#                 if key.find('ldap') != -1]
#for item in sys_ldap_keys:
#    print item
