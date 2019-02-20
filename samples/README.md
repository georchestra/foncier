## Samples for working with foncier

### 1. Read its README file

### 2. headers
Use the extension proposed in the readme.

### 3. Database
The docker-compose deploys a database, but it is empty. To have some data to extract, you need to fill it a bit:

 - create schemas foncier_2014, foncier_2015 etc (one at least). The years must match with the header config.

 - push some data inside. The app will make exports of pretty much every table in the database, but to get some data, the tables must have a 'idcom' attribute, which values will have to match (at least for some entries) with the zones listed in the LDAP entry.
 You can push the /samples/parcelles.sql file, containing some cadaster data on some communes in Ariege. The idcom attribute has been properly adusted
 ```psql -h localhost -p 54322 -U geoserver -d geoserver -f parcelles.sql```
(password _geoserver_)
 - adjust the LDAP settings: log into the LDAP container (```docker ps |grep ldap  then docker xec -it LDAP_CONTAINER_ID /bin/bash```) and then, change the active zone for PSC organization (description lists the idcom values accepted for this profile):

    ```
    echo 'dn: cn=psc,ou=orgs,dc=georchestra,dc=org
    changetype: modify
    replace: description
    description: 09015,09045,09099,09196,09210' > mods.ldif && \
    ldapmodify -x -D "cn=admin,dc=georchestra,dc=org" -w secret -H ldap:// -f mods.ldif
    ```

### 4. Testing
- Open http://localhost:8080/foncier/ as suggested,
- configure the headers,
- Try some extraction, it should work.
