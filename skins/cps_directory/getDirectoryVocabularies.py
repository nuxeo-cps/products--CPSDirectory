##parameters=loadcustom=1
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

global_roles_vocabulary = {
    'type': 'CPS Vocabulary',
    'data': {
        'tuples': (
            ('Member', "Member", 'label_cpsdir_roles_Member'),
            ('Manager', "Manager", 'label_cpsdir_roles_Manager'),
            )
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
    'global_roles': global_roles_vocabulary,
    'groups': groups_vocabulary,
    }

if loadcustom:
    cvocabularies = context.getCustomDirectoryVocabularies()
    vocabularies.update(cvocabularies)

return vocabularies
