# -*- coding: utf-8 -*-

import ldap
from flask import current_app

def acces_foncier(roles):
    ok = False
    for role in roles:
        if role.startswith(current_app.config['ROLE_PREFIX']):
            ok = True
            break
    return ok


def extract_cp(org):
    cnx = ldap.initialize(current_app.config['LDAP_URI'])
    try:
        cnx.protocol_version = ldap.VERSION3
        cnx.simple_bind_s(current_app.config['LDAP_BINDDN'], current_app.config['LDAP_PASSWD'])
        print 'Successfully connected to LDAP'
    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key('desc'):
            print 'Error binding to LDAP with dn: {0}'.format(current_app.config['LDAP_BINDDN'])
        else:
            print e
        return []
    
    try:
        results = cnx.search_s(current_app.config['LDAP_ORGS_BASEDN'], ldap.SCOPE_ONELEVEL, current_app.config['LDAP_SEARCH_FILTER'].format(org), ["businessCategory","description"])
        if len(results) == 0:
            print 'Error querying LDAP for org {0}: entry does not exist'.format(org)
            return []

        (dn, entry) = results[0]
        return ','.join(entry['description']).split(',')

    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key('desc'):
            print 'Error querying LDAP for org {0}: {1}'.format(org, e.message['desc'])
        else:
            print e
        return []

    cnx.unbind_s()
