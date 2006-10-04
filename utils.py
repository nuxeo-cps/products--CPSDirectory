#-*- coding=iso-8859-15 -*-
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
"""CPSDirectory.utils: a module that provides utilities to be
used by CPSDirectory classes. """

from types import ListType, TupleType, StringType
import re
import operator
from types import NoneType

from Products.CPSUtil.text import toAscii

def operator_in(a, b):
    # operator.contains with reversed operands
    return a in b

def operator_notin(a, b):
    return a not in b


class QueryMatcher(object):
    """ Hold/prepare a query and allow to match entries against it.

    >>> qm = QueryMatcher({'id' : 'foo', 'spam' : 'eggs'},
    ...                   accepted_keys=['id'])
    >>> qm.match({'id':'foo'})
    True

    >>> qm = QueryMatcher({'id' : 'foo', 'spam' : 'eggs'},
    ...                   accepted_keys=['id'])
    >>> qm.match({'id':'the Foo'})
    False

    >>> qm = QueryMatcher({'id' : 'foo'}, accepted_keys=['id'],
    ...                    substring_keys=['id'])
    >>> qm.match({'id':'SpamFooEggs'})
    True

    Substring behaviour and accents:
    >>> qm = QueryMatcher({'id' : 'fooe'}, accepted_keys=['id'],
    ...                    substring_keys=['id'])
    >>> qm.match({'id':'SpamFooÉggs'})
    True

    >>> qm = QueryMatcher({'id' : 'fooé'}, accepted_keys=['id'],
    ...                    substring_keys=['id'])
    >>> qm.match({'id':'SpamFooEggs'})
    True

    >>> qm = QueryMatcher({'enabled': False}, accepted_keys=['enabled'])
    >>> qm.match({'enabled': True})
    False
    >>> qm.match({'enabled': False})
    True

    >>> qm = QueryMatcher({'enabled': True}, accepted_keys=['enabled'])
    >>> qm.match({'enabled': True})
    True
    >>> qm.match({'enabled': False})
    False

    We don't fail if the entry lacks keys from the query
    >>> qm.match({})
    False

    """

    def __init__(self, query, accepted_keys=None, substring_keys=None):
        self._substring_keys = substring_keys
        _query = {}
        ops = {}
        for key, value in query.items():
            if accepted_keys is not None and key not in accepted_keys:
                continue
            value, op = self._findType(key, value)
            if op is None:
                continue
            ops[key] = op
            _query[key] = value
        self.query = _query
        self.ops = ops

    def _findType(self, key, value, negate=False):
        """Find op and value.
        """
        if value in ('', None): # XXX
            if negate:
                raise NotImplementedError
            # Ignore empty searches
            return value, None
        elif isinstance(value, basestring):
            if (self._substring_keys is not None
                and key in self._substring_keys):
                if negate:
                    raise NotImplementedError
                op = 'substring'
                value = value.lower()
            else:
                if negate:
                    op = operator.ne
                else:
                    op = operator.eq
        elif isinstance(value, (int, long, bool)):
            if negate:
                op = operator.ne
            else:
                op = operator.eq
        elif isinstance(value, (list, tuple)):
            if negate:
                op = operator_notin
            else:
                op = operator_in
        elif isinstance(value, dict) and 'query' in value:
            if negate and value.get('negate'):
                raise ValueError("Cannot double negate")
            query = value['query']
            return self._findType(key, query, negate=True)
        else:
            raise ValueError("Bad value %s for '%s'" % (`value`, key))
        return value, op

    def getKeysSet(self):
        return set(self.query)

    def match(self, entry):
        """ Does the entry match the query ? Boolean valued.
        """
        ops = self.ops
        ok = True
        for key, value in self.query.items():
            if key not in entry:
                ok = False
                break
            searched = entry[key]
            if isinstance(searched, (basestring, int, long, NoneType)):
                # bool subclasses int
                searched = (searched,)
            matched = 0
            value_re = None
            op = ops[key]
            if isinstance(value, basestring):
                if op == 'substring':
                    value = toAscii(value).lower()
                if '*' in value or '?' in value:
                    regexp = re.escape(value)
                    regexp = regexp.replace('\\?', '.?')
                    regexp = regexp.replace('\\*', '.*')
                    value_re = re.compile(regexp)

            for item in searched:
                # Wild cards like * are currently accepted
                if op == 'substring':
                    matched = value in toAscii(item).lower() or value == '*'
                else: # op is an operator
                    matched = op(item, value)
                if matched:
                    break
            if not matched:
                ok = False
                break
        return ok
