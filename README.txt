CPSDirectory

  $Id$

  This is a directory manager.

  A directory knows how to access and display entries. It uses a schema
  (from CPSSchemas) to describe an entry, and a layout and some widgets
  to specify how to display the entry and do validation.

  There are several directory types:

  - Members Directory: deals with members from acl_users and their data
    from portal_memberdata. Knows how to create them and assign special
    attributes (password, roles, groups).

  - Roles Directory: deals with the roles from acl_users.

  - Groups Directory: deals with the groups from acl_users (if the user
    folder knows about groups).

  - ZODB Directory: stores its entries directly as objects in the ZODB.

  - LDAP Directory: stores its entries in an LDAP directory.
