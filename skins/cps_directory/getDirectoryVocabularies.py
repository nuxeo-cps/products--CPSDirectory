##parameters=
"""
Get the vocabularies used for the directories.
"""
#$Id$

members_vocabulary = {
    'type': 'CPS Directory Vocabulary',
    'data': {
        'directory': 'members',
        },
    }

roles_vocabulary = {
    'type': 'CPS Directory Vocabulary',
    'data': {
        'directory': 'roles',
        },
    }

groups_vocabulary = {
    'type': 'CPS Directory Vocabulary',
    'data': {
        'directory': 'groups',
        },
    }

vocabularies = {
    'members': members_vocabulary,
    'roles': roles_vocabulary,
    'groups': groups_vocabulary,
    }

cvocabularies = context.getCustomDirectoryVocabularies()
vocabularies.update(cvocabularies)

return vocabularies
