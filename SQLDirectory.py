# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Florent Guillaume <fg@nuxeo.com>
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
"""SQLDirectory

This is a directory backed by a table in an SQL database.
"""

import sys
import logging
from datetime import datetime

from ZODB.loglevels import TRACE
from Acquisition import aq_base, aq_parent, aq_inner
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from DateTime.DateTime import DateTime
from OFS.Cache import Cacheable

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter
from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.BaseDirectory import ConfigurationError
from Products.CPSDirectory.BaseDirectory import AuthenticationFailed

from Products.CPSDirectory.interfaces import IDirectory
from Products.CPSDirectory.interfaces import IBatchable
from Products.CPSDirectory.interfaces import IOrderable

from zope.interface import implements


logger = logging.getLogger('CPSDirectory.SQLDirectory')


class SQLSyntaxError(ValueError):
    """SQL syntax error exception."""
    pass


class SQLDirectory(BaseDirectory, Cacheable):
    """SQL Directory.

    A directory that connects to an SQL database.
    """
    implements(IDirectory, IBatchable, IOrderable)

    # XXX what about tables where the id is not a string, like an int ?

    meta_type = 'CPS SQL Directory'

    manage_options = (
        BaseDirectory.manage_options +
        Cacheable.manage_options
        )

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'id_is_serial', 'type': 'boolean', 'mode': 'w',
         'label': "Id column is SERIAL"},
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': "Field for password (if authentication)"},
        {'id': 'sql_connection_path', 'type': 'selection', 'mode': 'w',
         'label': "SQL connection",
         'select_variable': 'all_sql_connection_paths'},
        {'id': 'sql_table', 'type': 'string', 'mode': 'w',
         'label': "SQL table"},
        {'id': 'dialect', 'type': 'selection', 'mode': 'w',
         'label': "SQL dialect", 'select_variable': 'all_dialects'},
        {'id': 'encoding', 'type': 'selection', 'mode': 'w',
         'label': "DB Encoding", 'select_variable': 'all_encoding'},
        {'id': 'method_clause', 'type': 'string', 'mode': 'w',
         'label': "SQL clause filtering"},
        )

    all_dialects = (
        'postgresql',
        'mysql',
        )

    all_encoding = (
        'iso-8859-15',
        'iso-8859-1',
        'utf-8',
        )

    id_is_serial = False
    password_field = ''
    sql_connection_path = ''
    sql_table = ''
    dialect = all_dialects[0]
    encoding = all_encoding[0]
    method_clause = ''

    def all_sql_connection_paths(self):
        """Get SQL database connections in the current folder and above.

        Returns a list of absolute paths.
        """
        paths = ['']
        context = self
        utool = getToolByName(self, 'portal_url')
        while context is not None:
            if getattr(aq_base(context), 'objectValues', None) is not None:
                for ob in context.objectValues():
                    if getattr(aq_base(ob), '_isAnSQLConnection', False):
                        paths.append(utool.getRelativeUrl(ob))
            context = aq_parent(aq_inner(context))
        paths.sort()
        return paths

    def _postProcessProperties(self):
        """Post-processing after properties change."""
        BaseDirectory._postProcessProperties(self)
        self.ZCacheable_invalidate()

    security.declarePrivate('_getAdapters')
    def _getAdapters(self, id, search=0, **kw):
        """Get the adapters for an entry."""
        dir = self
        adapters = [SQLStorageAdapter(schema, id, dir, **kw)
                    for schema in self._getSchemas(search=search)]
        return adapters

    security.declarePrivate('getSQLField')
    def getSQLField(self, field_id):
        """Get the SQL name for a field id."""
        # FIXME: make configurable
        return field_id

    security.declarePrivate('getSQLValue')
    def getSQLValue(self, value, quoter=None):
        """Get a quoted SQL value."""
        if isinstance(value, (basestring, DateTime, datetime)):
            if quoter is None:
                quoter = self._getSQLQuoter()
            if isinstance(value, basestring):
                if isinstance(value, str):
                    value = unicode(value, self.encoding)
                value = value.encode('utf-8')
            elif isinstance(value, DateTime):
                value = value.ISO()
            elif isinstance(value, datetime):
                value = value.isoformat()
            return quoter(value)
        elif isinstance(value, bool):
            if value:
                if self.dialect == 'mysql':
                    return '1'
                else:
                    return 'TRUE'
            else:
                if self.dialect == 'mysql':
                    return '0'
                else:
                    return 'FALSE'
        elif isinstance(value, (int, long, float)):
            return str(value)
        elif isinstance(value, DateTime):
            # XXX probably depends on SQL dialect
            return "'"+value.ISO()+"'"
        elif value is None:
            return 'NULL'
        else:
            logger.debug("getSQLValue: Unknown conversion for %r", value)
            raise ValueError(value)

    security.declarePrivate('valueFromSQL')
    def valueFromSQL(self, value):
        """Get a python value from a SQL one.
        """
        if isinstance(value, str):
            v = unicode(value, self.encoding)
            try:
                v.encode('ascii')
            except UnicodeEncodeError:
                # If we don't have ascii, keep the unicode value
                value = v
        return value

    security.declarePublic('debugTest') # XXX
    def debugTest(self):
        """DEBUG XXX"""
        return str(self.searchEntries(uid=(1,2,4), return_fields=['*']))

    #
    # API
    #

    security.declarePublic('isAuthenticating')
    def isAuthenticating(self):
        """Check if this directory does authentication.

        Returns a boolean.

        An SQL Directory is considered authenticating if
        the password field is not empty.
        """
        return not not self.password_field

    security.declarePrivate('getEntryAuthenticated')
    def getEntryAuthenticated(self, id, password, **kw):
        """Get and authenticate an entry.

        Returns the entry if authenticated.
        Raises KeyError if the entry doesn't exist.
        Raises AuthenticationFailed if authentication failed.
        """
        entry = self._getEntryKW(id, **kw) # may raise KeyError
        password_field = self.password_field
        cur_password = entry.get(password_field)
        if cur_password is None:
            logger.log(TRACE, "getEntryAuthenticated: No field %r "
                       "for %s in %s", password_field, id, self.getId())
            raise AuthenticationFailed
        if not self._checkPassword(password, cur_password):
            logger.log(TRACE, "getEntryAuthenticated: Authentication failed "
                       "for %s in %s", id, self.getId())
            raise AuthenticationFailed
        return entry

    # XXX put this into base class, it's duplicated in ZODBDirectory
    def _checkPassword(self, candidate, password):
        """Check that a password is correct.

        Returns a boolean.
        """
        return (candidate == password)

    security.declarePrivate('_createEntry')
    def _createEntry(self, entry):
        """Create an entry in the directory."""
        if self.id_is_serial:
            if entry.get(self.id_field) not in ('', 0, None):
                raise ValueError("Cannot pass an id for a directory with "
                                 "SERIAL")
            entry.pop(self.id_field, None)
        else:
            id = self.getEntryId(entry)
            if self._hasEntry(id):
                raise KeyError("Entry %s already exists" % `id`)

        sql_data = self._convertDataToQuotedSQL(entry)
        sql = "INSERT INTO %(table)s (%(fields)s) VALUES (%(vals)s)" % {
            'table': self.sql_table,
            'fields': ', '.join(sql_data.keys()),
            'vals': ', '.join(sql_data.values()),
            }
        self._execute(sql)

        if self.id_is_serial:
            if self.dialect == 'postgresql':
                sql = 'SELECT CURVAL(%s)' % self.getSQLValue(
                    '%s_%s_seq' % (self.sql_table, self.id_field))
            elif self.dialect == 'mysql':
                sql = 'SELECT LAST_INSERT_ID()'
            else:
                raise ValueError("Unknow SQL dialect %r" % self.dialect)
            items, data = self._execute(sql)
            id = data[0][0] # An int
            entry[self.id_field] = id

        return id

    def _getMethodClause(self):
        clause = ''
        if self.method_clause:
            meth = getattr(self, self.method_clause, None)
            if meth is None:
                raise RuntimeError("Unknown clause method %s for dir %s"
                                   % (self.method_clause, self.getId()))
            clause = meth()
        return clause

    def _makeWhereClause(self, id):
        clause = " %s = %s" % (self.getSQLField(self.id_field),
                               self.getSQLValue(id))
        tmp = self._getMethodClause()
        if tmp:
            clause += ' AND ' + tmp
        return clause

    security.declarePrivate('_deleteEntry')
    def _deleteEntry(self, id):
        """Delete an entry in the directory."""
        if self.id_is_serial and not isinstance(id, int):
            id = int(id)
        if not self._hasEntry(id):
            raise KeyError("No entry %s" % `id`)
        where = self._makeWhereClause(id)
        sql = "DELETE FROM %s WHERE %s" % (self.sql_table, where)
        self._execute(sql)
        entry = self.setEntryId(id, {})

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, query_options=None, **kw):
        """Search for entries in the directory.

        See API in the base class.

        Extension: query_options is a mapping containing one or several of:
        - limit: for batching
        - offset: for batching
        - count: for batching (return just a count of entries)
        - order_by: for batching (is a basestring or a tuple)
        - reverse: for batching (revered order)

        Other extensions to the base syntax:
        - foo={'query': v, 'range': 'min'/'max'}
            Query for >= or <= instead of equality
        - foo={'query': [v1,v2], 'range': 'min:max'}
            Range query
        """
        all_field_ids = self._getFieldIds()
        query_options = query_options or {}
        count = query_options.pop('count', False)

        if count:
            columns = 'COUNT(*)'
        else:
            # Find field_ids needed to compute returned fields.
            attrsd, return_fields = self._getSearchFields(return_fields)
            field_ids = attrsd.keys()
            field_ids.sort()
            columns = ', '.join([self.getSQLField(fid) for fid in field_ids])

        # Build query
        sql = 'SELECT %s FROM %s' % (columns, self.sql_table)

        # Where clause
        clauses = []
        quoter = self._getSQLQuoter()
        for key, value in kw.items():
            if key not in all_field_ids:
                continue
            clause = self._makeClause(key, value, quoter)
            if clause is not None:
                clauses.append(clause)
        clause = self._getMethodClause()
        if clause:
            clauses.append(clause)
        if clauses:
            sql = sql + " WHERE " + " AND ".join(clauses)

        # Order by
        order_by = query_options.get('order_by')
        if order_by:
            if isinstance(order_by, basestring):
                order_by = (order_by,)
            sql += ' ORDER BY ' + ', '.join(self.getSQLField(fid)
                                            for fid in order_by)
            if query_options.get('reverse'):
                sql += ' DESC'

        # Batching
        limit = query_options.get('limit')
        if limit:
            sql += ' LIMIT %d' % limit
        offset = query_options.get('offset')
        if offset:
            sql += ' OFFSET %d' % offset

        # Build results
        items, data = self._execute(sql)
        res = []

        if count:
            return [data[0][0]]

        idix = field_ids.index(self.id_field)
        for result in data:
            id = result[idix]
            if return_fields is None:
                res.append(id)
            else:
                result = list(result)
                entry = {}
                for field_id in field_ids:
                    value = result.pop(0)
                    entry[field_id] = self.valueFromSQL(value)
                res.append((id, entry))

        # Now we must compute a partial datamodel for each result,
        # to get correct computed fields.
        # XXX FIXME: do it!
        # XXX this should be factored out in a common implementation
        #     as LDAPBackingDirectory also does it
        # Note: search should be done on computed fields!
        #       That's what ZODBDirectory correctly does, but not LDAP.
        #       This needs a second pass of search on partial datamodel.

        return res

    #
    # Internal
    #

    def _getDB(self):
        """Get the Z SQL DB object."""
        path = self.sql_connection_path
        if not path:
            raise ConfigurationError(
                "Directory %s: no SQL connection specified" % self.getId())
        dbc = self.unrestrictedTraverse(path, None)
        if (dbc is None
            or not getattr(aq_base(dbc), '_isAnSQLConnection', False)):
            raise ConfigurationError(
                "Directory %s: %s is not a valid SQL connection" %
                (self.getId(), path))
        return dbc

    def _getConnection(self):
        """Get the SQL connection."""
        dbc = self._getDB()
        return dbc()


    def _getSQLQuoter(self):
        """Get a quoting method designed for the connection.

        The method, when applies to a string, returns a fully quoted
        version that can be inserted directly in a query.
        """
        dbc = self._getDB()
        return dbc.sql_quote__

    def _execute(self, sql):
        """Execute an SQL statement.

        Returns a tuple (items, data) or raises an exception.
        """
        keyset = None
        if self.ZCacheable_isCachingEnabled():
            if sql.startswith("SELECT"):
                keyset = {'query': sql}
                logger.log(TRACE, "_execute: Searching cache for %s", keyset)
                res = self.ZCacheable_get(keywords=keyset)
                if res is not None:
                    logger.log(TRACE, "_execute: -> results=%s", res[:10])
                    return res
            else:
                self.ZCacheable_invalidate()

        conn = self._getConnection()
        try:
            logger.debug("_execute: Execute:\n  %s", sql)
            if self.dialect == 'mysql':
                res = conn.query(sql, max_rows=0) # MySQL-DA defaults to 1000
            else:
                res = conn.query(sql)
        except SyntaxError, e:
            # Gadlfy: invalid syntax
            raise SQLSyntaxError(str(e))
        except NameError, e:
            # Gadfly: invalid column or table name
            raise ConfigurationError(str(e))
        except:
            e, v = sys.exc_info()[:2]
            if isinstance(e, str):
                if e.endswith('Error'):
                    # Gadfly: general parsing errors
                    raise SQLSyntaxError(e+' '+str(v))
            raise

        logger.log(TRACE, "_execute: Result:\n%r", res)

        if keyset is not None:
            logger.log(TRACE, "_execute: Putting in cache")
            self.ZCacheable_set(res, keywords=keyset)

        return res

    def _getEntryFromSQL(self, id, field_ids, password=None):
        """Get SQL entry.

        Returns converted values.
        """
        if self.id_is_serial and not isinstance(id, int):
            id = int(id)
        password_field = self.password_field
        if password is None or password_field in field_ids:
            fids = field_ids
        else:
            fids = list(field_ids) + [password_field]

        fields = ", ".join(self.getSQLField(fid) for fid in fids)
        where = self._makeWhereClause(id)
        sql = "SELECT %s FROM %s WHERE %s" % (fields, self.sql_table, where)
        items, data = self._execute(sql)
        if not data:
            raise KeyError("No entry %s" % `id`)
        if len(data) > 1:
            logger.error("Got %s entries for %s=%s",
                         len(data), self.id_field, id)
        result = list(data[0])

        # Check password
        if password is not None:
            i = fids.index(password_field)
            entry_pw = result[i]
            if entry_pw != password:
                raise AuthenticationFailed

        # Build entry
        entry = {}
        for field_id in field_ids:
            value = result.pop(0)
            entry[field_id] = self.valueFromSQL(value)
        return entry

    def _convertDataToQuotedSQL(self, data, skip_id=False):
        """Convert a data mapping into a correct quoted SQL one.

        Skips the id field if skip_id.
        Uses the schema to decide how conversion is done.
        """
        quoter = self._getSQLQuoter()
        sql_data = {}
        for field_id, field in self._getFieldItems():
            if field.write_ignore_storage:
                continue
            if not data.has_key(field_id):
                continue
            if skip_id and field_id in (self.id_field,):
                continue
            value = data[field_id]
            sql_value = self.getSQLValue(value, quoter=quoter)
            sql_data[self.getSQLField(field_id)] = sql_value
        return sql_data

    def _updateDataInSQL(self, id, sql_data):
        """Update an SQL entry.

        sql_data contains quoted sql values.
        """
        if not sql_data:
            return
        if self.id_is_serial and not isinstance(id, int):
            id = int(id)
        sets = ", ".join("%s = %s" % (key, value)
                         for key, value in sql_data.iteritems())
        where = self._makeWhereClause(id)
        sql = "UPDATE %s SET %s WHERE %s" % (self.sql_table, sets, where)
        self._execute(sql)

    def _makeClause(self, key, value, quoter, negate=False):
        """Make the where clause for search query
        """
        if isinstance(value, basestring):
            if not value:
                if negate:
                    op = '!='
                    val = self.getSQLValue('', quoter=quoter)
                else:
                    # For string match, we ignore empty values,
                    # they likely come from unfilled html input fields.
                    # XXX this is irregular
                    # XXX strip should be done by form machinery
                    logger.debug("Empty string search for field %s" % key)
                    return None
            if value == '*':
                if negate:
                    # negate of '*' is empty ('') values
                    # XXX this is irregular but we have to provide
                    # a way to search for '' values
                    op = '='
                    val = self.getSQLValue('', quoter=quoter)
                else:
                    op = 'IS NOT'
                    val = 'NULL'
            elif key in self.search_substring_fields:
                # Note: LIKE is not supported by Gadfly
                if negate:
                    op = 'NOT LIKE'
                else:
                    op = 'LIKE'
                val = self.getSQLValue('%'+value+'%', quoter=quoter)
            else:
                if negate:
                    op = '!='
                else:
                    op = '='
                val = self.getSQLValue(value, quoter=quoter)
        elif isinstance(value, bool):
            if negate:
                op = '!='
            else:
                op = '='
            if value:
                if self.dialect == 'mysql':
                    val = '1'
                else:
                    val = 'TRUE'
            else:
                if self.dialect == 'mysql':
                    val = '0'
                else:
                    val = 'FALSE'
        elif isinstance(value, (int, long)):
            if negate:
                op = '!='
            else:
                op = '='
            val = str(value)
        elif isinstance(value, (list, tuple)):
            if not value:
                # cannot match, ignore FIXME should fail query ?
                return None
            if negate:
                op = 'NOT IN'
            else:
                op = 'IN'
            val = ', '.join([self.getSQLValue(v, quoter=quoter)
                             for v in value])
            val = '('+val+')'
        elif value is None:
            if negate:
                op = 'IS NOT'
                val = 'NULL'
            else:
                op = 'IS'
                val = 'NULL'
        elif isinstance(value, dict) and 'query' in value:
            if negate and value.get('negate'):
                raise ValueError("Cannot double negate")
            negate = negate or value.get('negate')
            query = value['query']
            if 'range' in value:
                range = value['range']
                if range == 'min':
                    if negate:
                        op = '<'
                    else:
                        op = '>='
                    val = self.getSQLValue(query, quoter=quoter)
                elif range == 'max':
                    if negate:
                        op = '>'
                    else:
                        op = '<='
                    val = self.getSQLValue(query, quoter=quoter)
                elif range == 'min:max':
                    if (not isinstance(query, (list, tuple)) or
                        len(query) != 2):
                        raise ValueError("Bad query %r for %r" % (value, key))
                    if negate:
                        op = 'NOT BETWEEN'
                    else:
                        op = 'BETWEEN'
                    val = '%s AND %s' % (self.getSQLValue(query[0],
                                                          quoter=quoter),
                                         self.getSQLValue(query[1],
                                                          quoter=quoter))
                else:
                    raise ValueError("Bad range %r for %r" % (value, key))
            elif value.get('negate'):
                return self._makeClause(key, query, quoter, negate=True)
            else:
                raise ValueError("Bad value %s for '%s'" % (`value`, key))
        else:
            raise ValueError("Bad value %s for '%s'" % (`value`, key))
        sqlfield = self.getSQLField(key)
        clause = "%s %s %s" % (sqlfield, op, val)
        return clause


InitializeClass(SQLDirectory)

class SQLStorageAdapter(BaseStorageAdapter):
    """SQL  Storage Adapter

    This adapter gets and sets data from an SQL database.
    """

    def __init__(self, schema, id, dir, password=None, **kw):
        """Create an Adapter for a schema."""
        self._id = id
        self._dir = dir
        self._password = password
        BaseStorageAdapter.__init__(self, schema, **kw)

    def getData(self):
        """Get data from an entry, returns a mapping.

        Fills default value from the field if the object has no attribute.
        """
        id = self._id
        if id is None:
            # Creation.
            return self.getDefaultData()

        field_ids = self.getReadableFieldIds()
        entry = self._dir._getEntryFromSQL(id, field_ids,
                                           password=self._password)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        return entry[field_id]

    def _setData(self, data, toset=None):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data, toset=toset)
        if not toset:
            return
        dir = self._dir
        sql_data = dir._convertDataToQuotedSQL(data, skip_id=True)
        dir._updateDataInSQL(self._id, sql_data)

    def _getContentUrl(self, entry_id, field_id):
        raise NotImplementedError
        return '%s/getImageFieldData?entry_id=%s&field_id=%s' % (
            self._dir.absolute_url(), entry_id, field_id)

InitializeClass(SQLStorageAdapter)
