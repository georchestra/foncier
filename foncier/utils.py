import ldap

def acces_foncier(roles):
    ok = False
    for role in roles:
        if role.startswith('ROLE_FONCIER_'):
            ok = True
            break
    return ok


def extract_cp(cfg, org):
    cnx = ldap.initialize(cfg['LDAP_URI'])
    try:
        cnx.protocol_version = ldap.VERSION3
        cnx.simple_bind_s(cfg['LDAP_BINDDN'], cfg['LDAP_PASSWD'])
    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key('desc'):
            print e.message['desc']
        else:
            print e
        sys.exit(0)
    
    try:
        results = cnx.search_s(cfg['LDAP_ORGS_BASEDN'], ldap.SCOPE_ONELEVEL, cfg['LDAP_SEARCH_FILTER'].format(org), ["businessCategory","description"])
        if len(results) == 0:
            print "User has no org - this is an issue !"
            sys.exit(0)
            
        (dn, entry) = results[0]
        return ';'.join(entry['description']).split(';')

    except ldap.LDAPError, e:
        print e
    cnx.unbind_s()
