##parameters=
"""
Get the vocabularies used for the directories.
"""
#$Id$

members_vocabulary = {
    'type': 'CPS Directory Reference Vocabulary',
    'data': {
        'directory': 'members',
        },
    }

roles_vocabulary = {
    'type': 'CPS Directory Reference Vocabulary',
    'data': {
        'directory': 'roles',
        },
    }

groups_vocabulary = {
    'type': 'CPS Directory Reference Vocabulary',
    'data': {
        'directory': 'groups',
        },
    }

vocabularies = {
    'members': members_vocabulary,
    'roles': roles_vocabulary,
    'groups': groups_vocabulary,
    }

return vocabularies
