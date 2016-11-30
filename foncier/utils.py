import ldap

def acces_foncier(roles):
    ok = False
    for role in roles:
        if role.startswith('ROLE_FONCIER_'):
            ok = True
            break
    return ok


def extract_cp(org):
    # OpenLDAP
    LDAP_URI    = 'ldap://localhost:10389'
    LDAP_BINDDN = 'cn=admin,dc=georchestra,dc=org'
    LDAP_PASSWD = 'secret'
    LDAP_ORGS_BASEDN = "ou=orgs,dc=georchestra,dc=org"
    LDAP_SEARCH_FILTER = "(&(cn="+org+")(objectClass=groupOfMembers))"

    # Connection to the LDAP
    cnx = ldap.initialize(LDAP_URI)
    try:
        cnx.protocol_version = ldap.VERSION3
        cnx.simple_bind_s(LDAP_BINDDN, LDAP_PASSWD)
    except ldap.LDAPError, e:
        if type(e.message) == dict and e.message.has_key('desc'):
            print e.message['desc']
        else:
            print e
        sys.exit(0)
    
    try:
        results = cnx.search_s(LDAP_ORGS_BASEDN, ldap.SCOPE_ONELEVEL, LDAP_SEARCH_FILTER, ["businessCategory","description"])
        if len(results) == 0:
            print "User has no org - this is an issue !"
            sys.exit(0)
            
        (dn, entry) = results[0]
        return ';'.join(entry['description']).split(';')

    except ldap.LDAPError, e:
        print e
    cnx.unbind_s()
