# (C) Copyright 2005-2007 Nuxeo SAS <http://nuxeo.com>
# Authors:
# Olivier Grisel <og@nuxeo.com>
# M.-A. Darche <madarche@nuxeo.com>
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
"""FieldNamespace.

Register directory-related methods to CPSSchemas' FieldNamespace utility
so as to be able to make 'joins' with computed String List Fields.
"""
from logging import getLogger

from zLOG import LOG, DEBUG

LOG_KEY = 'FieldNamespace'

try:
    set
except NameError:
    # python 2.3 compat
    from sets import Set as set

import re

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.FieldNamespace import fieldStorageNamespace

def crossGetList(self, dir_id, field_id, value):
    """Return the list of entry ids of 'dir_id' such that 'value' is in
    'field_id'

    'field_id' is assumed to be a String List Field of 'dir_id'

    This method is used in the computed 'members' field of the groups
    directory's schema to list all members that belong to some group.
    """
    log_key = LOG_KEY + '.crossGetList'
    logger = getLogger(log_key)
    dtool = getToolByName(self, 'portal_directories')
    dir = dtool[dir_id]
    logger.debug("dir = %s" % dir)
    if field_id not in dir._getFieldIds():
        raise KeyError("%s not in %s's fields" % (field_id, dir_id))
    res = dir._searchEntries(**{field_id: [value]})
    logger.debug("res = %s" % res)
    return res

fieldStorageNamespace.register('dirCrossGetList', crossGetList)

def crossSetList(self, dir_id, field_id, value, entry_ids, value_search=None):
    """Update the field 'field_id' of 'dir_id' so that only entries of
    'dir_id' occuring in 'entry_ids' have 'value' in 'field_id'

    'field_id' is assumed to be a String List Field of 'dir_id'

    This method is used in the computed 'members' field of the groups
    directory's schema to write the list of members that belong to some
    group.

    'value_search' is used in cases where searches in 'dir_id' have different
    semantics than gets and sets. Namely, the lookup of entries that
    hold 'value' will be done using 'value_search'.
    """
    LOG_KEY = 'crossSetList'
    LOG(LOG_KEY, DEBUG, "dir_id = %s" % dir_id)
    dtool = getToolByName(self, 'portal_directories')
    dir = dtool[dir_id]
    entry_ids = set(entry_ids)
    if value_search is None:
        value_search = value
    with_value = dir._searchEntries(return_fields=[field_id],
                                    **{field_id: [value_search]})
    ids_with_value = [id for id, e in with_value]
    for id, entry in with_value:
        if id in entry_ids:
            continue
        # Remove the value from the field
        values = list(entry[field_id])
        if value not in values:
            # Sanity check, in case the search had weird semantics
            continue
        values.remove(value)
        new_entry = {
            dir.id_field: id,
            field_id: values,
            }
        entry = dir._editEntry(new_entry)
    #from pdb import set_trace; set_trace()
    for id in entry_ids.difference(ids_with_value):
        # Only retrieve the field in the entry that is interesting to us.
        # But unfortunately this seems to prevent some operations in some cases,
        # thus we use dir._getEntry(id) below. But this is an area of improvement.
        #entry = dir._getEntryKW(id, field_ids=[field_id])
        entry = dir._getEntry(id)
        # Add the value to the field
        values = list(entry[field_id])
        if value in values:
            # Sanity check, in case the search has weird semantics
            continue
        values.append(value)
        new_entry = {
            dir.id_field: id,
            field_id: values,
            }
        # Modify the entry with only the field that might have changed
        LOG(LOG_KEY, DEBUG, "Modifying entry = %s" % entry)
        entry = dir._editEntry(new_entry)
        LOG(LOG_KEY, DEBUG, "Modification done for entry = %s" % entry)

fieldStorageNamespace.register('dirCrossSetList', crossSetList)


# TODO: "cn" should not be hardcoded here
REGEXP_CN_DN = re.compile(u'cn=([a-zA-Z0-9_\.-]+),.+')
def crossLdapGetList(self, dir_id, field_id, value, base_dn):
    """Return the list of entry ids of 'dir_id' such that 'value' is in
    'field_id'

    'field_id' is assumed to be a String List Field of 'dir_id'

    This method is used in the computed 'members' field of the groups
    directory's schema to list all members that belong to some group.

    'base_dn' is the DN where the entries are to be found in the LDAP.
    """
    log_key = LOG_KEY + '.crossLdapGetList'
    logger = getLogger(log_key)
    dtool = getToolByName(self, 'portal_directories')
    dir = dtool[dir_id]
    logger.debug("dir = %s" % dir)
    if field_id not in dir._getFieldIds():
        raise KeyError("%s not in %s's fields" % (field_id, dir_id))
    # TODO: "uid" should not be hardcoded here
    value = 'uid=%s,%s' % (value, base_dn)
    res = dir._searchEntries(**{field_id: [value]})
    logger.debug("res = %s" % res)
    entries_ids = []
    for entry_dn in res:
        entry_id = entry_dn
        match = REGEXP_CN_DN.match(entry_dn)
        if match is not None:
            entry_id = match.group(1)
        entries_ids.append(entry_id)
    return entries_ids

fieldStorageNamespace.register('dirCrossLdapGetList', crossLdapGetList)


def mapIdsToFieldValues(self, dir_id, entry_ids, field_id):
    """Construct the list of values of 'field_id' from 'entry_ids' entries
    of directory 'dir_id'.

    Used in group ldap setup when the group is also a mail alias.
    """

    dtool = getToolByName(self, 'portal_directories')
    tdir = dtool[dir_id]
    # Using _getEntry to avoid problems with return_fields and computed fields
    return [tdir._getEntry(e_id)[field_id] for e_id in entry_ids]

fieldStorageNamespace.register('dirMapIdsToFieldValues', mapIdsToFieldValues)


# TODO: "uid" should not be hardcoded here
REGEXP_UID_DN = re.compile(u'uid=([a-zA-Z0-9_\.-]+),.+')
def mapDnToMemberIds(self, dn_field_ids):
    """Map LDAP DNs to member IDs.

    dn_field_ids is made of LDAP DNs from of the following form:
    'uid=joeuser,ou=people,dc=mysite,dc=net'
    """
    LOG_KEY = 'mapDnToMemberIds'
    LOG(LOG_KEY, DEBUG, "...")
    member_ids = []
    for dn_field_id in dn_field_ids:
        member_id = dn_field_id
        res = REGEXP_UID_DN.match(member_id)
        if res is not None:
            member_id = res.group(1)
        member_ids.append(member_id)
    return member_ids

fieldStorageNamespace.register('mapDnToMemberIds', mapDnToMemberIds)

def mapMemberIdsToDn(self, member_ids, base_dn, field_id, data):
    """Map CPS member IDs to LDAP DNs.

    'field_id' is the name of the entry field to set the DN to.

    The return DNs are the following form:
    'uid=joeuser,ou=people,dc=mysite,dc=net'
    """
    LOG_KEY = 'mapMemberIdsToDn'
    LOG(LOG_KEY, DEBUG, "member_ids = %s, field_id = %s, data = %s"
        % (member_ids, field_id, data))
    member_dns = ['%s,' + base_dn % x for x in member_ids]
    data[field_id] = member_dns
    LOG(LOG_KEY, DEBUG, "data = %s" % (data))
    return member_ids

fieldStorageNamespace.register('mapMemberIdsToDn', mapMemberIdsToDn)
