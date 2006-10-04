# (C) Copyright 2004 Nuxeo SARL <http://nuxeo.com>
# Author: Georges Racinet <gracinet@nuxeo.com>
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

import unittest

from Testing.ZopeTestCase import doctest

from Products.CPSDirectory.utils import QueryMatcher

class DirectoryUtilsTestCase(unittest.TestCase):

    def testNegate_str(self):
        query = {'sn': {'query': 'tutu', 'negate': True}}
        matcher = QueryMatcher(query)
        self.assert_(matcher.match({'sn': 'blob', 'givenName': '1'}))
        self.failIf(matcher.match({'sn': 'tutu', 'givenName': '2'}))

    def testNegate_int(self):
        query = {'sn': {'query': 1, 'negate': True}}
        matcher = QueryMatcher(query)
        self.assert_(matcher.match({'sn': 34, 'givenName': '1'}))
        self.failIf(matcher.match({'sn': 1, 'givenName': '2'}))

    def testNegate_list(self):
        query = {'sn': {'query': ('a', 'b'), 'negate': True}}
        matcher = QueryMatcher(query)
        self.assert_(matcher.match({'sn': 'c', 'givenName': '1'}))
        self.failIf(matcher.match({'sn': 'a', 'givenName': '2'}))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DirectoryUtilsTestCase),
        doctest.DocTestSuite('Products.CPSDirectory.utils'), 
        ))
