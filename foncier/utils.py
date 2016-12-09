# -*- coding: utf-8 -*-

from ldap3 import Connection, LEVEL
from flask import current_app


def acces_foncier(roles):
    for role in roles:
        if role.startswith(current_app.config['ROLE_PREFIX']):
            return True
    return False


def extract_cp(org):
    cnx = Connection(current_app.config['LDAP_URI'],
                    current_app.config['LDAP_BINDDN'],
                    current_app.config['LDAP_PASSWD'],
                    auto_bind=True)

    cnx.search(search_base=current_app.config['LDAP_ORGS_BASEDN'],
               search_filter=current_app.config['LDAP_SEARCH_FILTER'] % org,
               search_scope=LEVEL,
               attributes=["businessCategory", "description"])

    for entry in cnx.entries:
        if len(entry['description']) == 0:
            res = []
        else:
            res = ','.join(entry['description']).split(',')
        cnx.unbind()
        return res

    if not cnx.closed:
        cnx.unbind()
    print('Error querying LDAP for org %s: entry does not exist' % org)
    return []
