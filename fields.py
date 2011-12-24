# Copyright (c) 2009 Association Paris-Montagne
# Author: Georges Racinet <georges@racinet.fr>
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
"""Directory specific fields
"""

#$Id$

import logging

from Globals import InitializeClass
from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Field import FieldRegistry
from Products.CPSSchemas.BasicFields import CPSStringListField
from Products.CPSSchemas.BasicFields import CPSStringField
from Products.CPSSchemas.BasicFields import toUTF8, fromUTF8

logger = logging.getLogger('Products.CPSDirectory.DirectoryFields')

def attribute_to_dn(value, attr, directory=None):
    """Resolve an attribute value to provide a Dn."""
    logger.debug("attribute_to_dn : %s='%s'", attr, value)
    s_entries = directory._searchEntries(return_fields=['dn', attr],
                                         **{attr: value})

    # some directories can have a substring behaviour, enforcing exact match
    entries = [ (eid, entry) for eid, entry in s_entries
                if entry[attr] == value]

    if len(entries) == 1:
        return entries[0][1]['dn']

    msg = "in directory '%s' with '%s=%s" % (directory.getId(), attr, value)
    if not entries:
        logger.info("No entry " + msg)
    if len(entries) > 1:
        logger.info("More than one entry " + msg)

def attribute_to_entry(value, attr, directory=None, return_fields=()):
    """Resolve an attribute value to provide a partial entry."""
    logger.debug("attribute_to_entry : %s='%s'", attr, value)
    if attr not in return_fields:
        return_fields = list(return_fields)
        return_fields.append(attr)
    s_entries = directory._searchEntries(return_fields=return_fields,
                                         **{attr: value})

    # some directories can have a substring behaviour, enforcing exact match
    entries = [ (eid, entry) for eid, entry in s_entries
                if entry[attr] == value]

    if len(entries) == 1:
        return entries[0][1]

    msg = "in directory '%s' with '%s=%s" % (directory.getId(), attr, value)
    if not entries:
        logger.info("No entry " + msg)
    if len(entries) > 1:
        logger.info("More than one entry " + msg)

def dn_to_attribute(dn, attr, directory=None):
    """Find the attribute value for given dn."""
    logger.debug('dn_to_attribute : %s', dn)
    entries = directory._searchEntries(dn=dn, return_fields=[attr])
    if not entries:
        logger.info("In directory '%s', no entry with DN %s",
                    directory.getId(), dn)
        raise KeyError(dn)
    return entries[0][1][attr]


class CPSDistinguishedNameListField(CPSStringListField):
    """ Stores a list of DNs in ldap while presenting attribute values to CPS.

    This assumes that the correspondance between the attribute (typically uid)
    value and the DB is one to one (bijection), through an auxiliary directory
    object.

    performance note: if the attribute is the entry RDN, no LDAP query is
    issued for read. On the other hand, every write will have to query ldap to
    deduce DN from attribute value.

    Remark: the auxiliary directory does not have to be an LDAP backing
    directory; it could be any directory with 'dn' and the attribute in the
    schema.

    In case there are also cross_dependent_fields it is recommended to put
    this field itself among them. That way, only one LDAP call will be issued
    to resolve both the dn to store and the other dependent fields. 

    Example:
       - one can use this field with field_id = 'member' for a groupOfNames
       - for a groupOfNames which is also a CourierMailAlias, use this field
       with cross_dependent_fields = [ 'member:dn', 'maildrop:mail']

    TODO: option for flat target ldap branch under assumption that the
    attribute is the RDN
    """

    meta_type = "CPS Distinguished Name List Field"

    _properties = CPSStringListField._properties + (
        {'id': 'ldap_attribute', 'type': 'string', 'mode': 'w',
         'label': 'LDAP attribute'},
        {'id': 'aux_directory', 'type': 'string', 'mode': 'w',
         'label': 'Directory to resolve DNs from attribute values'},
        {'id': 'cross_dependent_fields', 'type': 'tokens', 'mode': 'w',
         'label': 'Cross dependent fields',}
        )

    ldap_attribute = ''
    aux_directory = ''
    cross_dependent_fields = ''
    cross_dependent_fields_c = {}

    def _postProcessProperties(self):
        self.cross_dependent_fields_c = dict(
            (k.strip(), v.strip())
            for k, v in ( x.split(':') for x in self.cross_dependent_fields) )
        self._p_changed = True

    def computeDependantFields(self, schemas, data, context=None):
        """Apply the dependency mapping.
        """
        if not self.cross_dependent_fields_c:
            return
        attr = self.ldap_attribute
        aux_dir = getToolByName(self, 'portal_directories')[self.aux_directory]
        cdf = self.cross_dependent_fields_c
        target_fields = cdf.values()

        values = data[self.getFieldId()]

        for field in cdf: # might include self's id
            data[field] = []

        for v in values:
            entry = attribute_to_entry(v, attr, directory=aux_dir,
                                       return_fields=target_fields)
            if entry is None:
                continue
            for field, target_field in self.cross_dependent_fields_c.items():
                data.setdefault(field, list()).append(entry[target_field])

    def _getAllDependantFieldIds(self):
        return self.cross_dependent_fields_c.keys()

    def convertToLDAP(self, value):
        """Transform the list of attribute values into a dn list."""
        if self.getFieldId() in self.cross_dependent_fields_c:
            # already done by computeDependantFields
            return value
        attr = self.ldap_attribute
        aux_dir = getToolByName(self, 'portal_directories')[self.aux_directory]

        res = []
        for v in value:
            dn = attribute_to_dn(v, attr, directory=aux_dir)
            if dn:
                res.append(dn)
        return res

    def convertFromLDAP(self, values):
        """Convert the list of dns to attribute values
        """
        attr = self.ldap_attribute
        aux_dir = getToolByName(self, 'portal_directories')[self.aux_directory]

        res = []
        for dn in values:
            if dn.startswith(attr + '='): # fast case: attr is RDN
                res.append(fromUTF8(dn.split(',')[0].split('=')[1]))
                continue
            try:
                res.append(dn_to_attribute(dn, attr, directory=aux_dir))
            except KeyError:
                pass
        return res

InitializeClass(CPSDistinguishedNameListField)
FieldRegistry.register(CPSDistinguishedNameListField)

class CPSDistinguishedNameField(CPSStringField):
    """ Stores a DN in ldap while presenting an attribute value to CPS.

    See docstring for CPSDistinguishedNameListField for details.
    """

    meta_type = "CPS Distinguished Name Field"

    _properties = CPSStringListField._properties + (
        {'id': 'ldap_attribute', 'type': 'string', 'mode': 'w',
         'label': 'LDAP attribute'},
        {'id': 'aux_directory', 'type': 'string', 'mode': 'w',
         'label': 'Directory to resolve DNs from attribute values'},
        )

    ldap_attribute = ''
    aux_directory = ''

    def convertToLDAP(self, value):
        """Transform the list of attribute values into a dn list."""
        attr = self.ldap_attribute
        aux_dir = getToolByName(self, 'portal_directories')[self.aux_directory]

        try:
            return [attribute_to_dn(value, self.ldap_attribute,
                                    directory=aux_dir)]
        except KeyError:
            return [] # XXX default value ?

    def convertFromLDAP(self, values):
        """Convert the list of dns to attribute values
        """
        attr = self.ldap_attribute
        aux_dir = getToolByName(self, 'portal_directories')[self.aux_directory]

        dn = values[0]
        if dn.startswith(attr + '='): # fast case: attr is RDN
            return fromUTF8(dn.split(',')[0].split('=')[1])

        try:
            return dn_to_attribute(dn, attr, directory=aux_dir)
        except KeyError:
            return '' # XXX use default value ?

InitializeClass(CPSDistinguishedNameField)
FieldRegistry.register(CPSDistinguishedNameField)

