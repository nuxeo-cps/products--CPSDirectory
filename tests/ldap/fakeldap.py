#!/usr/bin/python
# -*- encoding: iso-8859-15 -*-
# Author: Tarek Ziadé <tz@nuxeo.com>
#
#  split_tokens and extract_tokens are taken from python-ldap :
#  written by Michael Stroeder <michael@stroeder.com>
#  See http://python-ldap.sourceforge.net for details.
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
"""
    FakeLdap

    A fake ldap server for testing purpose.
    see README file
"""

import sys,string
from os import path

MODULE_DIR = path.dirname(__file__) + '/'
CONF_FILE = MODULE_DIR + 'fakeldap.conf'



class LogFile:
    """ a log class"""
    def __init__(self, filename=''):
        self.logfilename = filename

    def write(self, msg):
        # todo
        pass

class LdifReader:
    """ this class reads an ldif file
        loads it into memory
        and implements a search
    """
    ldif_file = ''

    def vislog(self, msg):
        print msg

    def __init__(self, owner, filename=''):
        self.owner = owner

        if filename == '':
            filename = MODULE_DIR + LDIF_FILENAME

        self.ldif_file = open(filename, 'r')
        try:
            self.ldif_content = self.ldif_file.readlines()
            self.load_ldif()
        finally:
            self.ldif_file.close()

    def split_tokens(self, s):
        """
        Returns list of syntax elements with quotes and spaces
        stripped.
        """
        result = []
        result_append = result.append
        s_len = len(s)
        i = 0
        while i<s_len:
          start = i
          while i<s_len and s[i]!="'":
            if s[i]=="(" or s[i]==")":
              if i>start:
                result_append(s[start:i])
              result_append(s[i])
              i +=1 # Consume parentheses
              start = i
            elif s[i]==" ":
              if i>start:
                result_append(s[start:i])
              # Consume space chars
              while i<s_len and s[i]==" ":
                i +=1
              start = i
            else:
              i +=1
          if i>start:
            result_append(s[start:i])
          i +=1
          if i>=s_len:
            break
          start = i
          while i<s_len and s[i]!="'":
            i +=1
          if i>=start:
            result_append(s[start:i])
          i +=1
        return result # split_tokens()


    def load_ldif(self):
        """ load ldif file onto memory """
        self.ldif_entries = []
        ldif_entries = self.ldif_entries
        content = self.ldif_content
        step = 0
        length = len(content)

        #self.vislog(str(length))

        while (step < length):
            currentline = content[step].strip()
            element = {}
            #self.vislog(currentline)
            while (currentline <> '') and (step < length):
                # ugly splitting, should use regexpr here
                parts = currentline.split(': ')
                try:
                    key = parts[0]
                    value = parts[1]
                except IndexError:
                    # this happens on compressed fields
                    # ie images
                    # TODO : parse it
                    # self.vislog('IndexError :' + str(parts))
                    pass
                else:
                    if element.has_key(key):
                        element[key].append(value)
                    else:
                        element[key] = [value]
                step +=1
                if step < length :
                    currentline = content[step].strip()

            ldif_entries.append(element)
            #self.vislog(str(element))
            step+=1


    def addEntry(self,lines):
        content = self.ldif_content

        # adding empty line
        last_line = len(content) - 1

        if last_line >= 0:
            if content[last_line].strip() <> '':
                content.append('\n')

        # adding entry
        # no control is made at all here
        content = content + lines

        # resync memory
        self.ldif_content = content
        self.load_ldif()
        # XXX see if we want to resync file
        #print str(self.ldif_entries)


    def render_entries(self,entries):
        content = ''
        for entry in entries:
            for line in entry:
                line = line['key'] + ': '+ line['value']
                content += line+'\n'
            content += '\n'

        return content

    def deleteEntry(self,dn):
        entry = self._findEntry(dn)
        if entry is not None:
            self.ldif_entries.remove(entry)
            # we need to resync the content
            self.ldif_content = self.render_entries(self.ldif_entries)

    def _findEntry(self,dn):
        item_number = 0
        for ldif_entry in self.ldif_entries:
            current_dn = ldif_entry['dn'][0]
            if dn.find(',') >= 0:
                found = current_dn == dn
            else:
                part_dn = current_dn.split(',')[0]
                explode_dn = part_dn.split('=')[1]
                found = explode_dn == dn

            if found:
                return ldif_entry

        return None

    def search(self, base, scope, filter, attributes):
        """ let's try to find the entry using the dn
            no regexpr, we will use sequential search
            using empty lines it will be faster
        """

        content = self.ldif_content
        base = string.lower(base)

        ldif_entries = self.ldif_entries


        filtered_entries = []

        # filtering entries with base
        for ldif_entry in ldif_entries:
            current_dn = ldif_entry['dn'][0]
            # we need to compare last part based on scope
            part_dn = current_dn.split(',')
            # homemade scope (upside down)
            scope = len(part_dn) - len(base.split(','))
            step = scope
            made_dn = ''

            while step < len(part_dn):
                made_dn = made_dn + part_dn[step]
                if step < len(part_dn) - 1:
                    made_dn = made_dn + ','
                step += 1


            #print made_dn + ' <--> ' + base
            if made_dn == base:

                # we don't use scope
                # filtering entry if it has the filter
                # each filter is separated by ( )
                # for now we just use ObjectClass
                # self.owner.ldap_logcall(str(self.split_tokens(filter)))
                filters = []

                # XXXX this is not parsing the search query
                # at all
                # with all options (wild chars, etc..)
                # needs to be done
                for item in self.split_tokens(filter):
                    if (item <> '(') and (item <> ')') and (item <> '&')\
                        and (item <> '|') :
                        cfilter = {}
                        sitem = item.split('=')
                        cfilter['key'] = sitem[0]
                        cfilter['value'] = sitem[1]
                        filters.append(cfilter)

                # we want to find the object class
                # in the entry objectClass list
                numpoints = 0

                for cfilter in filters:
                    if ldif_entry.has_key(cfilter['key']):
                        for lfilter in ldif_entry[cfilter['key']]:
                            if cfilter['value'] == lfilter:
                                numpoints += 1
                                break


                if numpoints>=len(filters):
                    #self.vislog('found entry : %s' %str(ldif_entry))
                    filtered_entries.append(ldif_entry)

        results = []
        for filtered_entry in filtered_entries:
            # adding fields

            result_entry = {}
            for attribute in attributes:
                if filtered_entry.has_key(attribute):
                    result_entry[attribute] = filtered_entry[attribute]

            result = (filtered_entry['dn'][0], result_entry)
            results.append(result)


        #print('base %s scope %s filter %s attributes %s results %s'
         #   %(base, scope, str(filter), str(attributes), str(results)))

        return results

class FakeLdap:
    """
        implements part of python-ldap
        api for testing purpose
        also log calls
        in a log file
    """
    options = {}

    def __init__(self):
        conffile = open(CONF_FILE, 'r')
        try:
            lines = conffile.readlines()
            # we'll do better later
            filename = MODULE_DIR + lines[1].split('=')[1].strip()
            logfilename =  MODULE_DIR + lines[2].split('=')[1].strip()
            self.logcalls =  lines[3].split('=')[1].strip()
        finally:
            conffile.close()

        self.dif_reader = LdifReader(self, filename)
        self.logger = LogFile(logfilename)


    def delete_s(self,dn):
        self.dif_reader.deleteEntry(dn)


    def add_s(self,dn,attrs_list):
        """ adds an entry
        """
        self.ldap_logcall('add_ds')
        entry = ['dn: '+ dn ]
        for attribute in attrs_list:
            line = attribute[0]+': '
            for element in attribute[1]:
                entry.append(line+element+'\n')

        self.dif_reader.addEntry(entry)


    def ldap_logcall(self, msg):
        self.logger.write(msg)


    def search_s(self, base, scope, filterstr='(objectClass=*)',
        attrlist=None, attrsonly=0):


        results =  self.dif_reader.search(base, scope, filterstr, attrlist)

        self.ldap_logcall('searching base %s scope %s results %s attributes %s'
%(base, str(scope), str(results), str(attrlist)))

        return results

    def simple_bind_s(self, bind_dn, bind_password):
        self.ldap_logcall('simple_bind_s')

    def add_ext(self, dn, modlist, serverctrls=None, clientctrls=None):
        self.ldap_logcall('add_ext')

    def bind(self, who, cred,method):
        self.ldap_logcall('bind')

    def sasl_bind_s(self, who,auth):
        self.ldap_logcall('sasl_bind_s')

    def compare_ext(self, dn, attr, value, serverctrls=None, clientctrls=None):
        self.ldap_logcall('compare_ext')

    def delete_ext(self, dn, serverctrls=None, clientctrls=None):
        self.ldap_logcall('delete_ext')

    def manage_dsa_it(self, enable, critical=0):
        self.ldap_logcall('manage_dsa_it')

    def modify_ext(self, dn, modlist, serverctrls=None, clientctrls=None):
        self.ldap_logcall('modify_ext')

    def rename(self, dn, newrdn, newsuperior=None,
        delold=1, serverctrls=None, clientctrls=None):
        self.ldap_logcall('abandon')

    def result(self, msgid=0, all=1, timeout=None):
        self.ldap_logcall('result')

    def search_ext(self, base, scope, filterstr='(objectClass=*)',attrlist=None,
       attrsonly=0,serverctrls=None,clientctrls=None,timeout=-1,sizelimit=0):
        self.ldap_logcall('search_ext')

    def set_cache_options(self, *args, **kwargs):
        self.ldap_logcall('set_cache_options')

    def set_rebind_proc(self, func):
        self.ldap_logcall('set_rebind_proc')

    def start_tls_s(self, *args,**kwargs):
        self.ldap_logcall('start_tls_s')

    def unbind_ext(self, serverctrls=None, clientctrls=None):
        self.ldap_logcall('unbind_ext')

    def get_option(self, option):
        if self.options.has_key(option):
            return options[option]
        else:
            return None

    def set_option(self, option, invalue):
        self.options[option] = invalue

    def abandon_ext(self, msgid, serverctrls=None, clientctrls=None):
        self.ldap_logcall('abandon_ext')

    def abandon(self, msgid):
        self.ldap_logcall('abandon')



if __name__ == '__main__':
    # tiny test
    ob = initialize('dummy')
    print ob.search_s('ou=personnes,o=bceao,c=int',2,
            '(objectClass=BCEAOPerson)',['uid'],0)
