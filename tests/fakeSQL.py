# Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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

import re

class FakeSQLConnection:
    _isAnSQLConnection = True
    def __init__(self, id):
        self.id = id
        self.dbc = FakeDBC()
    def __call__(self):
        return self.dbc
    def _createTable(self, id, columns):
        self.dbc._createTable(id, columns)
    def sql_quote__(self, value):
        return quote(value)

select_re = re.compile(r'SELECT (.*) FROM ([^ ]+)(?: WHERE (.*))?')
insert_re = re.compile(r'INSERT INTO ([^ ]+) \((.*)\) VALUES \((.*)\)')
delete_re = re.compile(r'DELETE FROM ([^ ]+) WHERE (.*)')
update_re = re.compile(r'UPDATE ([^ ]+) SET (.*) WHERE (.*)')
eq_re = re.compile(r'([^ ]+) = "([^"]*)"')
set_re = eq_re
in_re = re.compile(r'([^ ]+) IN \((.*)\)')
count_re = re.compile(r'COUNT\(([^)]*)\)')

def quote(v):
    if '"' not in v:
        return '"%s"' % v
    else:
        raise ValueError("Cannot quote %r" % v)

def unquote(v):
    v = v.strip()
    if len(v) < 2 or v[0] != '"' or v[-1] != '"':
        raise ValueError("Bad quoted value %r" % v)
    return v[1:-1]


class FakeDBC:
    def __init__(self):
        self.columns = {}
        self.data = {}

    def _createTable(self, id, columns):
        self.columns[id] = [col.upper() for col in columns]
        self.data[id] = []

    def query(self, sql):
        #print 'query:', sql
        m = select_re.match(sql)
        if m is not None:
            columns, table, where = m.groups()
            return self.doSelect(table, columns, where)
        m = insert_re.match(sql)
        if m is not None:
            table, columns, values = m.groups()
            return self.doInsert(table, columns, values)
        m = delete_re.match(sql)
        if m is not None:
            table, where = m.groups()
            return self.doDelete(table, where)
        m = update_re.match(sql)
        if m is not None:
            table, sets, where = m.groups()
            return self.doUpdate(table, sets, where)

        raise ValueError("Cannot parse query %r" % sql)

    def doSelect(self, table, columns, where):
        if table not in self.data:
            raise ValueError("No table %s" % table)
        columns, counts, orig_columns = self._parseColumns(table, columns,
                                                           allow_count=True)

        match_info = self._parseWhere(table, where)

        # Filter results
        results = []
        data = self.data[table]
        for line in data:
            if self._matchLine(line, match_info):
                # Matches !
                res = [line[col] for col in columns]
                results.append(tuple(res))

        # Counts, single column assumed
        if counts:
            results = [(len(results),)]

        coldef = [{'width': None, 'null': None, 'type': 's', 'name': col}
                  for col in orig_columns]
        return (coldef, results)


    def doInsert(self, table, columns, values):
        if table not in self.data:
            raise ValueError("No table %s" % table)
        columns = self._parseColumns(table, columns)

        values = values.split(',')
        if len(values) != len(columns):
            raise ValueError("Length mismatch")

        # Defaults
        line = {}
        for col in self.columns[table]:
            line[col] = None

        # Values
        for i in range(len(values)):
            line[columns[i]] = unquote(values[i])

        self.data[table].append(line)


    def doDelete(self, table, where):
        if table not in self.data:
            raise ValueError("No table %s" % table)

        match_info = self._parseWhere(table, where)

        data = []
        for line in self.data[table]:
            if not self._matchLine(line, match_info):
                data.append(line)
        self.data[table] = data

    def doUpdate(self, table, sets, where):
        if table not in self.data:
            raise ValueError("No table %s" % table)

        match_info = self._parseWhere(table, where)
        table_columns = self.columns[table]

        update = {}
        while sets:
            m = eq_re.match(sets)
            if m is None:
                raise ValueError("Cannot parse SET of %r" % sets)
            sets = sets[len(m.group(0)):].strip()
            if sets.startswith(','):
                sets = sets[1:].strip()
            col, val = m.groups()
            col = col.upper()
            if col not in table_columns:
                raise ValueError("No column %s" % col)
            update[col] = val

        for line in self.data[table]:
            if self._matchLine(line, match_info):
                line.update(update)

    def _parseColumns(self, table, columns, allow_count=False):
        table_columns = self.columns[table]
        orig_columns = [col.strip().upper() for col in columns.split(',')]
        columns = []
        counts = []
        for col in orig_columns:
            m = count_re.match(col)
            if m is not None:
                col = m.group(1)
                counts.append(col)
            if col not in table_columns:
                raise ValueError("No column %s" % col)
            columns.append(col)
        if counts:
            if not allow_count:
                raise ValueError("Syntax error, cannot use COUNT")
            if len(counts) > 1:
                raise ValueError("Too many COUNTs")
            if len(columns) > 1:
                raise ValueError("COUNT must be alone")
        if allow_count:
            return columns, counts, orig_columns
        return columns

    def _parseWhere(self, table, where):
        table_columns = self.columns[table]
        equalities = []
        members = []
        if where is not None:
            for clause in where.split(' AND '):
                clause = clause.strip()
                m = eq_re.match(clause)
                if m is not None:
                    groups = m.groups()
                    col = groups[0].upper()
                    if col not in table_columns:
                        raise ValueError("No column %s" % col)
                    equalities.append((col, groups[1]))
                    continue
                m = in_re.match(clause)
                if m is not None:
                    groups = m.groups()
                    col = groups[0].upper()
                    if col not in table_columns:
                        raise ValueError("No column %s" % col)
                    vals = [unquote(v) for v in groups[1].split(',')]
                    members.append((col, vals))
                    continue
                raise ValueError("Unknown clause syntax %r" % clause)
        return {
            'equalities': equalities,
            'members': members,
            }

    def _matchLine(self, line, match_info):
        for col, val in match_info['equalities']:
            if line[col] != val:
                return False
        for col, vals in match_info['members']:
            for val in vals:
                if line[col] == val:
                    break
            else:
                return False
        return True
