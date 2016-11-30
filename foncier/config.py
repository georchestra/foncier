# -*- coding: utf-8 -*-

class Config(object):
    # General config
    ROLE_PREFIX = 'ROLE_FONCIER_'
    # LDAP-related keys:
    LDAP_BINDDN = 'cn=admin,dc=georchestra,dc=org'
    LDAP_PASSWD = 'secret'
    LDAP_ORGS_BASEDN = 'ou=orgs,dc=georchestra,dc=org'
    LDAP_SEARCH_FILTER = '(&(cn={0})(objectClass=groupOfMembers))'

class ProductionConfig(Config):
    DEBUG = False
    LDAP_URI = 'ldap://ldap:389'

class DevelopmentConfig(Config):
    DEBUG = True
    LDAP_URI = 'ldap://localhost:10389'
