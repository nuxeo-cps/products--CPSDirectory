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


class QueryMatcher:
    """ Hold/prepare a query and allow to match entries against it.

    >>> qm = QueryMatcher({'id' : 'foo', 'spam' : 'eggs'},
    ...                   accepted_keys=['id'])
    >>> qm.match({'id':'foo'})
    True

    >>> qm = QueryMatcher({'id' : 'foo'}, accepted_keys=['id'],
    ...                    substring_keys=['id'])
    >>> qm.match({'id':'SpamFooEggs'})
    True

    """

    def __init__(self, query, accepted_keys=None, substring_keys=None):
        _query = {}
        match_types = {}
        for key, value in query.items():
            if accepted_keys is not None and key not in accepted_keys:
                continue
            if not value:
                # Ignore empty searches
                continue
            if isinstance(value, StringType):
                if substring_keys is not None and key in substring_keys:
                    match_types[key] = 'substring'
                    value = value.lower()
                else:
                    match_types[key] = 'exact'
            elif isinstance(value, ListType) or isinstance(value, TupleType):
                match_types[key] = 'list'
            else:
                raise ValueError("Bad value %s for '%s'" % (`value`, key))
            _query[key] = value
        self.query = _query
        self.match_types = match_types

    def getKeysSet(self):
        return set(self.query)

    def match(self, entry):
        """ Does the entry match the query ? Boolean valued.
        """
        search_types = self.match_types
        ok = 1
        for key, value in self.query.items():
            searched = entry[key]
            if isinstance(searched, StringType):
                searched = (searched,)
            matched = 0
            for item in searched:
                # FIXME? No wild cards like * are currently accepted
                if search_types[key] == 'list':
                    matched = item in value
                elif search_types[key] == 'substring':
                    matched = item.lower().find(value) != -1
                else: # search_types[key] == 'exact':
                    matched = item == value
                if matched:
                    break
            if not matched:
                ok = 0
                break
        return ok == 1
