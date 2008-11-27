# (C) Copyright 2005 Nuxeo SAS <http://nuxeo.com>
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
"""Directory interfaces.
"""

from zope.interface import Interface

_marker = object()


class IDirectoryTool(Interface):
    """Directory tool.
    """

    def listVisibleDirectories():
        """List directories visible by the current user.

        Returns a list of directory ids.
        """

class IDirectory(Interface):
    """Directory.
    """

    #
    # Public API
    #

    def hasEntry(id):
        """Does the directory have a given entry?
        """

    def createEntry(entry):
        """Create an entry in the directory.

        Returns the id given to the entry if different from the one given
        or None.
        """

    def getEntry(id, default=_marker):
        """Get entry filtered by acls and processes.

        A default argument can be specified so that KeyError is not
        raised if the entry does not exist.
        """

    def searchEntries(return_fields=None, **kw):
        """Search for entries in the directory.

        The keyword arguments specify the search to be done.
        It is of the form field1=value1, field2=[value21, value22], etc.

        The search is done:

          - As a substring case-independent search for fields in
            search_substring_fields, if the directory has a property with this
            id (MetaDirectory doesn't, see its documentation)

          - As an exact search for all other fields.

          - Searches done for a list values are always OR exact searches.

        If return_fields is None, returns a list of ids:
          ['member1', 'member2']

        If return_fields is not None, it must be sequence of field ids.
        The method will return a list of tuples containing the member id
        and a dictionary of available fields:
          [('member1', {'email': 'foo', 'age': 75}), ('member2', {'age': 5})]

        return_fields=['*'] means to return all available fields.
        """

    def editEntry(entry):
        """Edit an entry in the directory.
        """

    def deleteEntry(id):
        """Delete an entry in the directory.
        """

    def isAuthenticating():
        """Check if this directory does authentication.

        Returns a boolean.
        """

    #
    # Other basic API, usually overriden in implementation classes
    #

    # should be private
    def listEntryIds():
        """List all the entry ids.
        """

    # should be private
    def listEntryIdsAndTitles():
        """List all the entry ids and titles.

        Returns a list of tuples (id, title).
        """

    def _hasEntry(id):
        """Does the directory have a given entry?

        This method doesn't do security checks.
        """

    def _createEntry(entry):
        """Create an entry in the directory, unrestricted.

        Returns the id given to the entry if different from the one given
        or None.
        """

    def _deleteEntry(id):
        """Delete an entry in the directory, unrestricted.
        """

    def _getEntry(id, **kw):
        """Get entry filtered by processes but not acls.
        """

    def _getEntryKW(id, **kw):
        """Get entry filtered by acls and processes.

        Passes additional **kw to _getDataModel.
        """

    def getEntryAuthenticated(id, password, **kw):
        """Get and authenticate an entry.

        Doesn't check ACLs.

        Returns the entry if authenticated.
        Raises KeyError if the entry doesn't exist.
        Raises AuthenticationFailed if authentication failed.
        """

    def _searchEntries(return_fields=None, **kw):
        """Search for entries in the directory, unrestricted.

        See documentation on searchEntries().
        This private method does not do ACL checks.
        """

    def _editEntry(entry, check_acls=False):
        """Edit an entry in the directory, unrestricted.
        """

    #
    # Storage adapter, overriden in each implementation class
    #

    def _getAdapters(id, search=0, **kw):
        """Get the adapters for an entry.

        If search is true, return the search adapters.
        Passes additional **kw to the adapters.
        """

    #
    # Hierarchical support
    #

    def _isHierarchical():
        """Return True if the directory support hierarchical methods.
        """

    def _listChildrenEntryIds(id, field_id=None):
        """Return a children entries ids for entry 'id'.

        Return a list of field_id if not None or self.id_field.
        Available only if directory is hierarchical.
        """

    def _getParentEntryId(id, field_id):
        """Return Parent Id of 'id'.

        Return None if 'id' have no parent.
        Return a field_id if not None or a self.id_field.
        Available only if directory is hierarchical.
        """

    #
    # Visibility API
    #

    # should be private
    def isEntryAclAllowed(acl_roles, id=None, entry=None):
        """Check if the user has correct ACL on an entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        Returns a boolean.
        """

    def isVisible():
        """Check if the user can view the directory.

        Uses the computed entry local roles.

        Returns a boolean.
        """

    def isCreateEntryAllowed(id=None, entry=None):
        """Check if the user can create an entry.

        Uses the computed entry local roles.

        Returns a boolean.
        """

    def isDeleteEntryAllowed(id=None, entry=None):
        """Check if the user can delete an entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        Returns a boolean.
        """

    def isViewEntryAllowed(id=None, entry=None):
        """Check if the user can view an entry.

        Returns a boolean.
        """

    def isEditEntryAllowed(id=None, entry=None):
        # TODO: should also have a new_entry arg.
        """Check if the user can edit a given entry.

        Uses the computed entry local roles.
        If no entry is passed, uses an empty one.

        Returns a boolean.
        """

    def isSearchEntriesAllowed():
        # TODO: should also have a new_entry arg.
        """Check if the user can search entries within the directory.

        Equivalent to isVisible, because it uses directory view roles.
        Uses the computed entry local roles.

        Returns a boolean.
        """

    def checkCreateEntryAllowed(id=None, entry=None):
        """Check that the user can create an entry.

        Raises Unauthorized if not.
        """

    def checkDeleteEntryAllowed(id=None, entry=None):
        """Check that the user can delete a given entry.

        Raises Unauthorized if not.
        """

    def checkViewEntryAllowed(id=None, entry=None):
        """Check that the user can view a given entry.

        Raises Unauthorized if not.
        """

    def checkEditEntryAllowed(id=None, entry=None):
        """Check that the user can edit a given entry.

        Raises Unauthorized if not.
        """

    def checkSearchEntriesAllowed():
        """Check that the user can search entries.

        Actually checks if the user can view entries.
        Raises Unauthorized if not.
        """

    #
    # Public rendering API
    #

    def renderEntryDetailed(id, layout_mode='view', **kw):
        """Render the entry.

        Returns (rendered, datastructure):
        - rendered is the rendered HTML,
        - datastructure is the resulting datastructure.
        """

    def renderEditEntryDetailed(id, request=None,
                                layout_mode='edit', layout_mode_err='edit',
                                **kw):
        """Modify the entry from request, returns detailed information
        about the rendering.

        If request is None, the entry is not modified and is rendered
        in layout_mode.

        If request is not None, the parameters are validated and the
        entry modified, and rendered in layout_mode. If there is
        a validation error, the entry is rendered in layout_mode_err.

        Returns (rendered, ok, datastructure):
        - rendered is the rendered HTML,
        - ok is the result of the validation,
        - datastructure is the resulting datastructure.
        """

    def renderCreateEntryDetailed(request=None, validate=1,
                                  layout_mode='create',
                                  created_callback=None, **kw):
        """Render an entry for creation, maybe create it.

        Returns (rendered, ok, datastructure):
        - rendered is the rendered HTML,
        - ok is the result of the validation,
        - datastructure is the resulting datastructure.
        """

    def renderSearchDetailed(request=None, validate=0,
                             layout_mode='search', callback=None,
                             **kw):
        """Rendering for search.

        Calls callback when data has been validated.
        """

    #
    # Other helpers for implementation classes
    #

    def _getSchemas(search=False):
        """Get the schemas for this directory.

        If search=True, get the schemas for a search.

        Returns a sequence of Schema objects.
        """

    def _getFieldItems(search=False):
        """Get the schemas fields for this directory

        If search=True, get the schemas keys for a search.

        Returns a sequence of fields items (field_id, field)

        Doesn't return duplicate field ids coming from differents schemas.
        """

    def _getFieldIds(search=False):
        """Get the schemas keys for this directory

        If search=True, get the schemas keys for a search.

        Returns a sequence of field ids.

        Doesn't return duplicate field ids coming from differents schemas.
        """

    def _getUniqueSchema(search=False):
        """Return a unique schema for this directory.

        We have two cases here:

         * Only one schema specified:

           simply return it

         * Several schemas specified:

           Generate dynamicaly a *non* persistent CPSSchema instance
           that aggregates all the fields from the different schemas of
           this directory.

           It the different schemas define fields with the same id, then
           the field defined on the first schema will be kept.

        This is used by the directory adapter storage because only one
        exists right now for a given directory.
        """

    def _getSchemaFieldById(field_id, search=False):
        """Return a field from the directory's schemas.
        """

    def _getSearchFields(return_fields=None):
        """Get the fields dict used in search from return fields, and the
        updated return fields

        Also compute dependant fields.
        """

    def _getDataModel(id, check_acls=1, **kw):
        """Get the datamodel for an entry.

        Passes additional **kw to _getAdapters.
        """

    #
    # Entry Local Roles API
    #

    # Overriden by some subclasses
    def _getAdditionalRoles(id):
        """Get additional user roles provided to ACLs.

        The default implementation returns no additional roles.
        """

    def getEntryLocalRoles(entry):
        """Get the effective entry local roles for an entry.

        Returns the list of roles whose condition evaluates to true.
        """

    def listEntryLocalRoles():
        """List entry local roles.

        Returns a list of tuples (role, expr).
        """

    def addEntryLocalRole(role, expr):
        """Add an entry local role.

        Returns '' if no error, 'exists' if the role already exists, or
        the error text if a compilatione error occured.
        """

    def delEntryLocalRole(role):
        """Delete an entry local role.
        """

    def changeEntryLocalRole(role, expr):
        """Change an entry local role.

        Returns '' if no error, or the error text if a compilation
        error occured.
        """

class IContentishDirectory(IDirectory):
    """Directory with content
    """

class IMetaDirectory(IDirectory):
    """Meta Directory

    A directory that redirects requests to other backing directories and does
    field rename and aggregation.
    """

    def manage_changeBacking(dir_id, field_ignore, field_renames,
                             missing_entry_expr, delete=0, REQUEST=None):
        """Change mappings from ZMI.

        field_renames is a list of dicts of type
              {'b_id' : <id in backing>, 'id': <id in meta>}
        """

    def manage_addBacking(dir_id, field_ignore, field_renames,
                          missing_entry_expr, REQUEST=None):
        """Change mappings from ZMI.

        field_renames is a list of dicts of type
              {'b_id' : <id in backing>, 'id': <id in meta>}
        """

    def getBackingDirectories(self, no_dir=0):
        """Get the list of backing directories and their infos."""

class IBatchable(Interface):
    """Directory that understands limit/offset/count query_options.
    """

class IOrderable(Interface):
    """Directory that understands order_by query_option.
    """

class ILDAPServerAccess(Interface):
    """Object storing bind parameters."""

    def getLdapUrl():
        """Return the full LDAP URL."""
