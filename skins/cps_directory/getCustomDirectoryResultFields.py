##parameters=directory_id, default_field=None
"""
Get the list of fields to be displayed in the directory search result list.

This file should be override in your product

expected list format [{'id': 'sn', 'title': 'Name'}, ]
title will be i18n.

example:
if directory_id == 'ldap_people':
    fields = [{'id': 'sn', 'title': 'Nom'},
              {'id': 'givenName', 'title': 'Prénom'},]
elif directory_id == ...

"""
#$Id$

fields = []

return fields
