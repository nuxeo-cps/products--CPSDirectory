# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel <og@nuxeo.com>
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
"""FieldNamespace

Register directory-related methods to CPSSchemas' FieldNamespace utility
so as to be able to make 'joins' with computed String List Fields
"""

from Products.CPSSchemas.FieldNamespace import fieldStorageNamespace
from Products.CMFCore.utils import getToolByName

def crossGetList(self, dir_id, field_id, value):
    """Return the list of entry ids of 'dir_id' such that 'value' is in
    'field_id'

    'field_id' is assumed to be a String List Field of 'dir_id'

    This method is used in the computed 'members' field of the groups
    directory's schema to list all members that belong to some group.
    """
    dtool = getToolByName(self, 'portal_directories')
    stool = getToolByName(self, 'portal_schemas')
    dir = dtool[dir_id]
    if field_id not in stool[dir.schema].keys():
        raise KeyError("%s not in %s's fields" % (field_id, dir_id))
    return dir._searchEntries(**{field_id: [value]})

fieldStorageNamespace.register('dirCrossGetList', crossGetList)

def crossSetList(self, dir_id, field_id, value, entry_ids):
    """Update the field 'field_id' of 'dir_id' so that only entries of
    'dir_id' occuring in 'entry_ids' have 'value' in 'field_id'

    'field_id' is assumed to be a String List Field of 'dir_id'

    This method is used in the computed 'members' field of the groups
    directory's schema to write the list of members that belong to some
    group.
    """
    dtool = getToolByName(self, 'portal_directories')
    dir = dtool[dir_id]
    entry_ids = set(entry_ids)
    with_value = dir._searchEntries(return_fields=[field_id],
                                    **{field_id: [value]})
    ids_with_value = [id for id, e in with_value]
    for id, entry in with_value:
        if id in entry_ids:
            continue
        # Remove the value from the field
        values = entry[field_id]
        if value not in values:
            # Sanity check, in case the search had weird semantics
            continue
        values.remove(value)
        new_entry = {
            dir.id_field: id,
            field_id: values,
            }
        entry = dir._editEntry(new_entry)
    for id in entry_ids.difference(ids_with_value):
        entry = dir._getEntryKW(id, field_ids=[field_id])
        # Add the value to the field
        values = entry[field_id]
        if value in values:
            # Sanity check, in case the search had weird semantics
            continue
        values.append(value)
        new_entry = {
            dir.id_field: id,
            field_id: values,
            }
        entry = dir._editEntry(new_entry)

fieldStorageNamespace.register('dirCrossSetList', crossSetList)
