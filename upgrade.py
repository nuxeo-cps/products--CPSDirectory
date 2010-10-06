# (C) Copyright 2008 Georges Racinet
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
# $Id: LDAPBackingDirectory.py 52825 2008-04-23 15:56:27Z madarche $
"""CPSDirectory upgrade steps.
"""

import logging
import transaction

from Acquisition import aq_base
from zExceptions import BadRequest
from Products.CPSDirectory.ZODBDirectory import ZODBDirectory
from Products.CPSSchemas.upgrade import upgrade_datamodel_unicode

try:
    from Products.CPSDirectory.LDAPBackingDirectory import LDAPBackingDirectory
    from Products.CPSDirectory.LDAPServerAccess import LDAPServerAccess
except ImportError, e:
    if str(e) == 'No module named ldap':
        LDAP_OK = False
    else:
        raise
else:
    LDAP_OK = True


def check_ldap_installed(portal):
    """Check if ldap module is there."""
    return LDAP_OK

def upgrade_ldap_server_access(portal):
    """Move bind params from LDAPBackingDirectory to LDAPServerAccess instances.
    """

    old_props = ('ldap_server', 'ldap_port', 'ldap_use_ssl', 
                 'ldap_bind_dn', 'ldap_bind_password')

    new_props = ('server', 'port', 'use_ssl', 'bind_dn', 'bind_password')

    dtool = portal.portal_directories

    # (Ldap Server Access objectS) dict params -> id
    lsas = dict(
        (tuple(lsa.getProperty(prop) for prop in new_props), lsa.getId())
        for lsa in dtool.objectValues([LDAPServerAccess.meta_type]))

    
    logger = logging.getLogger('CPSDirectory upgrade_ldap_server_access')
    for ldir in dtool.objectValues([LDAPBackingDirectory.meta_type]):
        # NB: PropertyManager API wouldn't work in general
        params = tuple(getattr(aq_base(ldir), prop, None) for prop in old_props)

        # filter out upgraded and inconsistent dirs
        if set(params) == set([None]):
            logger.info('Directory %s already upgraded', ldir.getId())
            continue
        if None in params:
            logger.warn(
                'Directory %s is in a mixed state and needs manual cleanup', 
                ldir.getId())
            continue

        # reuse existing LSA if possible
        lsa_id = lsas.get(params)
        if lsa_id is None:
            # create LSA instance to store params
            lsa_id = ldir.getId() + '_server_access'
            dtool._setObject(lsa_id, LDAPServerAccess(lsa_id))
            dtool[lsa_id].manage_changeProperties(
                **dict(zip(new_props, params)))
            lsas[params] = lsa_id

        # careful cleanup.
        for prop in old_props:
            try:
                ldir.manage_delProperties((prop,))
            except (BadRequest, KeyError):
                delattr(ldir, prop)

        ldir.manage_changeProperties(ldap_server_access=lsa_id)
        logger.info("Directory '%s' now refers to '%s'", ldir.getId(), lsa_id)

def upgrade_zodb_dirs_unicode(portal):
    dtool = portal.portal_directories

    logger = logging.getLogger('CPSDirectory upgrade_zodb_dirs_unicode')
    zdirs = dtool.objectValues(ZODBDirectory.meta_type)

    for z in zdirs:
        total = len(z)
        logger.info("Starting upgrade for %r (title: %s), with %d entries", z.getId(), z.title, total)
        # GR trying a memory efficient way to iterate on ids
        # maybe dangerous ?
        done = 0
        for eid in z._tree.iterkeys():
            dm = z._getDataModel(eid)
            upgrade_datamodel_unicode(dm)
            done += 1
            if done % 100 == 0:
                logger.info("Upgraded %d/%d entries for %r", done, total,
                            z.getId())
                transaction.commit()
        logger.info("Finished upgrade for %d/%d entries", done, total)
