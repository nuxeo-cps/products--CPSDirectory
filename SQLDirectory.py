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

from zLOG import LOG, DEBUG, TRACE, ERROR

import sys
from Acquisition import aq_base, aq_parent, aq_inner
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from DateTime.DateTime import DateTime

from Products.CPSSchemas.StorageAdapter import BaseStorageAdapter
from Products.CPSDirectory.BaseDirectory import BaseDirectory
from Products.CPSDirectory.BaseDirectory import ConfigurationError
from Products.CPSDirectory.BaseDirectory import AuthenticationFailed


class SQLSyntaxError(ValueError):
    """SQL syntax error exception."""
    pass


class SQLDirectory(BaseDirectory):
    """SQL Directory.

    A directory that connects to an SQL database.
    """
    # XXX what about tables where the id is not a string, like an int ?

    meta_type = 'CPS SQL Directory'

    security = ClassSecurityInfo()

    _properties = BaseDirectory._properties + (
        {'id': 'password_field', 'type': 'string', 'mode': 'w',
         'label': "Field for password (if authentication)"},
        {'id': 'sql_connection_path', 'type': 'selection', 'mode': 'w',
         'label': "SQL connection",
         'select_variable': 'all_sql_connection_paths'},
        #{'id': 'sql_syntax', 'type': 'selection', 'mode': 'w',
        # 'label': "SQL syntax", 'select_variable': 'all_sql_syntaxes'},
        {'id': 'sql_table', 'type': 'string', 'mode': 'w',
         'label': "SQL table"},
        #{'id': 'sql_auxiliary_tables', 'type': 'string', 'mode': 'w',
        # 'label': "SQL auxiliary tables"},
        )

    #all_sql_syntaxes = ('postgresql',)

    password_field = ''
    sql_connection_path = ''
    #sql_syntax = all_sql_syntaxes[0]
    sql_table = ''
    #sql_auxiliary_tables = ''

    def all_sql_connection_paths(self):
        """Get SQL database connections in the current folder and above.

        Returns a list of absolute paths.
        """
        paths = ['']
        context = self
        while context is not None:
            if getattr(aq_base(context), 'objectValues', None) is not None:
                for ob in context.objectValues():
                    if getattr(aq_base(ob), '_isAnSQLConnection', False):
                        path = '/'.join(ob.getPhysicalPath())
                        paths.append(path)
            context = aq_parent(aq_inner(context))
        paths.sort()
        return paths

    #def _postProcessProperties(self):
    #    """Post-processing after properties change."""
    #    BaseDirectory._postProcessProperties(self)
    #    # XXX sql_auxiliary_tables

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
        # XXX deal with unicode and latin1
        if isinstance(value, str):
            if quoter is None:
                quoter = self._getSQLQuoter()
            return quoter(value)
        elif isinstance(value, (int, long)):
            return str(value)
        elif isinstance(value, DateTime):
            # XXX probably depends on SQL dialect
            return "'"+value.ISO()+"'"
        else:
            LOG('getSQLValue', DEBUG, 'Unknown conversion for %s' % `value`)
            raise ValueError(value)

    security.declarePublic('debugTest') # XXX
    def debugTest(self):
        """DEBUG XXX"""
        return str(self.searchEntries(uid=(1,2,4), return_fields=['*']))

    #
    # API
    #

    security.declarePrivate('listEntryIds')
    def listEntryIds(self):
        """List all the entry ids."""
        sql = "SELECT %(id)s FROM %(table)s" % {
            'id': self.getSQLField(self.id_field),
            'table': self.sql_table,
            }
        items, data = self._execute(sql)
        res = [t[0] for t in data]
        return res

    security.declarePrivate('listEntryIdsAndTitles')
    def listEntryIdsAndTitles(self):
        """List all the entry ids and titles."""
        id_field = self.id_field
        title_field = self.title_field
        if title_field == id_field:
            ids = self.listEntryIds()
            return [(id, id) for id in ids]
        sql = "SELECT %(id)s, %(title)s FROM %(table)s" % {
            'id': self.getSQLField(id_field),
            'title': self.getSQLField(title_field),
            'table': self.sql_table,
            }
        items, data = self._execute(sql)
        return data

    security.declarePublic('hasEntry')
    def hasEntry(self, id):
        """Does the directory have a given entry?"""
        sql = ("SELECT COUNT(%(idf)s) FROM %(table)s"
               " WHERE %(idf)s = %(id)s") % {
            'idf': self.getSQLField(self.id_field),
            'table': self.sql_table,
            'id': self.getSQLValue(id),
            }
        items, data = self._execute(sql)
        return not not data[0][0]

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
            LOG('getEntryAuthenticated', TRACE, "No field '%s' for %s in %s" %
                (password_field, id, self.getId()))
            raise AuthenticationFailed
        if not self._checkPassword(password, cur_password):
            LOG('getEntryAuthenticated', TRACE,
                "Authentication failed for %s in %s" % (id, self.getId()))
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
        id = entry[self.id_field]
        if self.hasEntry(id):
            raise KeyError("Entry %s already exists" % `id`)

        sql_data = self._convertDataToQuotedSQL(entry)
        sql = "INSERT INTO %(table)s (%(fields)s) VALUES (%(vals)s)" % {
            'table': self.sql_table,
            'fields': ', '.join(sql_data.keys()),
            'vals': ', '.join(sql_data.values()),
            }
        self._execute(sql)

        # XXX should be a way to use autoincrement ids and return it
        # XXX depends on SQL dialect
        return None

    security.declarePublic('deleteEntry')
    def deleteEntry(self, id):
        """Delete an entry in the directory."""
        self.checkDeleteEntryAllowed(id=id)
        if not self.hasEntry(id):
            raise KeyError("No entry %s" % `id`)
        sql = "DELETE FROM %(table)s WHERE %(idf)s = %(id)s" % {
            'table': self.sql_table,
            'idf': self.getSQLField(self.id_field),
            'id': self.getSQLValue(id),
            }
        self._execute(sql)

    security.declarePrivate('_searchEntries')
    def _searchEntries(self, return_fields=None, **kw):
        """Search for entries in the directory.

        See API in the base class.
        """
        id_field = self.id_field
        schema = self._getSchemas()[0]
        all_field_ids = schema.keys()

        # Find field_ids needed to compute returned fields.
        # XXX this code is also in ZODBDirectory and should be factored out
        if return_fields is None:
            field_ids = []
        else:
            attrsd = {}
            if return_fields == ['*']:
                return_fields = all_field_ids
            for field_id in return_fields:
                if field_id not in all_field_ids:
                    continue
                attrsd[field_id] = None
                dep_ids = schema[field_id].read_process_dependent_fields
                for dep_id in dep_ids:
                    attrsd[dep_id] = None
            field_ids = attrsd.keys()
            field_ids.sort()
        if not id_field in field_ids:
            field_ids.append(id_field)

        # Build query
        sql = "SELECT %(fields)s FROM %(table)s" % {
            'fields': ', '.join([self.getSQLField(fid) for fid in field_ids]),
            'table': self.sql_table,
            }
        # Where clause
        clauses = []
        quoter = self._getSQLQuoter()
        for key, value in kw.items():
            if key not in all_field_ids:
                continue
            clause = self._makeClause(key, value, quoter)
            if clause is not None:
                clauses.append(clause)
        if clauses:
            sql = sql + " WHERE " + " AND ".join(clauses)
        items, data = self._execute(sql)

        # Build results
        res = []
        idix = field_ids.index(id_field)
        for result in data:
            result = list(result)
            id = result[idix]
            entry = {}
            for field_id in field_ids:
                entry[field_id] = result.pop(0)
                # XXX conversions !
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
        LOG('_execute', TRACE, "Execute:\n  %s" % sql)
        conn = self._getConnection()
        try:
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

        LOG('_execute', TRACE, "Result:\n%s" % `res`)
        return res

    def _getEntryFromSQL(self, id, field_ids, password=None):
        """Get SQL entry.

        Returns converted values.
        """
        password_field = self.password_field
        if password is None or password_field in field_ids:
            fids = field_ids
        else:
            fids = list(field_ids) + [password_field]

        sql = ("SELECT %(fields)s FROM %(table)s"
               " WHERE %(idf)s = %(id)s") % {
            'fields': ', '.join([self.getSQLField(fid) for fid in fids]),
            'table': self.sql_table,
            'idf': self.getSQLField(self.id_field),
            'id': self.getSQLValue(id),
            }
        items, data = self._execute(sql)
        if not data:
            raise KeyError("No entry %s" % `id`)
        if len(data) > 1:
            LOG('SQLDirectory', ERROR,
                'Got %s entries for %s=%s' % (len(data), self.id_field, id))
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
            entry[field_id] = result.pop(0)
            # XXX conversions !
        return entry

    def _convertDataToQuotedSQL(self, data, skip_id=False):
        """Convert a data mapping into a correct quoted SQL one.

        Skips the id field if skip_id.
        Uses the schema to decide how conversion is done.
        """
        quoter = self._getSQLQuoter()
        sql_data = {}
        for field_id, field in self._getSchemas()[0].items(): # XXX
            if field.write_ignore_storage:
                continue
            if not data.has_key(field_id):
                continue
            if skip_id and field_id == self.id_field:
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
        sets = ["%s = %s" % (key, value) for key, value in sql_data.items()]
        sql = "UPDATE %(table)s SET %(sets)s WHERE %(idf)s = %(id)s" % {
            'table': self.sql_table,
            'sets': ', '.join(sets),
            'idf': self.getSQLField(self.id_field),
            'id': self.getSQLValue(id),
            }
        self._execute(sql)

    def _makeClause(self, key, value, quoter):
        """Make the where clause for search query
        """
        sqlfield = self.getSQLField(key)
        if isinstance(value, str):
            if not value:
                # For string match, we ignore empty values,
                # they likely come from unfilled html input fields.
                return None
            if value == '*':
                return None
            if key in self.search_substring_fields:
                # Note: LIKE is not supported by Gadfly
                op = 'LIKE'
                val = self.getSQLValue('%'+value+'%', quoter=quoter)
            else:
                op = '='
                val = self.getSQLValue(value, quoter=quoter)
        elif isinstance(value, (int, long)):
            op = '='
            val = str(value)
        elif isinstance(value, (list, tuple)):
            if not value:
                # cannot match, ignore FIXME should fail query ?
                return None
            op = 'IN'
            val = ', '.join([self.getSQLValue(v, quoter=quoter)
                             for v in value])
            val = '('+val+')'
        else:
            raise ValueError("Bad value %s for '%s'" % (`value`, key))
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

        field_ids = self.getFieldIds()
        entry = self._dir._getEntryFromSQL(id, field_ids,
                                           password=self._password)
        return self._getData(entry=entry)

    def _getFieldData(self, field_id, field, entry=None):
        """Get data from one field."""
        return entry[field_id]

    def _setData(self, data):
        """Set data to the entry, from a mapping."""
        data = self._setDataDoProcess(data)
        dir = self._dir
        sql_data = dir._convertDataToQuotedSQL(data, skip_id=True)
        dir._updateDataInSQL(self._id, sql_data)

    def _getContentUrl(self, entry_id, field_id):
        raise NotImplementedError
        return '%s/getImageFieldData?entry_id=%s&field_id=%s' % (
            self._dir.absolute_url(), entry_id, field_id)

InitializeClass(SQLStorageAdapter)