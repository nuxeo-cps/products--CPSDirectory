#!/usr/bin/python
# -*- encoding: iso-8859-1 -*-
# Author: Tarek Ziadé <tz@nuxeo.com>
#
#  split_tokens and extract_tokens are taken from python-ldap :
#  written by Michael Stroeder <michael@stroeder.com>
#  See http://python-ldap.sourceforge.net for details.
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
"""


"""


__version__ = '0.1.1'

__all__ = [
  'open','initialize','init',
  'explode_dn','explode_rdn',
  'get_option','set_option'
]

import sys
import fakeldap

ob_pt = None

def initialize(uri,trace_level=0,trace_file=sys.stdout,trace_stack_limit=None):
  ob = fakeldap.FakeLdap()
  ob_pt = ob
  return ob


def open(host,port=389,trace_level=0,trace_file=sys.stdout,trace_stack_limit=None):
  pass

init = open


def explode_dn(dn,notypes=0):
  """
  explode_dn(dn [, notypes=0]) -> list

  This function takes a DN and breaks it up into its component parts.
  The notypes parameter is used to specify that only the component's
  attribute values be returned and not the attribute types.
  """
  return dn.split(',')


def explode_rdn(rdn,notypes=0):
  """
  explode_rdn(rdn [, notypes=0]) -> list

  This function takes a RDN and breaks it up into its component parts
  if it is a multi-valued RDN.
  The notypes parameter is used to specify that only the component's
  attribute values be returned and not the attribute types.
  """
  return rdn.split('+')


def get_option(option):
  if ob_pt is not None:
      return ob_pt.get_option(option)
  else:
      return None


def set_option(option,invalue):
  if ob_pt is not None:
      ob_pt.set_option(option,invalue)


def is_ldap_url(url):
  return url.startswith('ldap://')
