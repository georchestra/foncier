## Samples for working with foncier

### 1. Read its README file

### 2. headers
Use the extension proposed in the readme.

### 3. Database
The docker-compose deploys a database, and deploys some sample data : it creates foncier_2014 schema and pushes some cadaster data on it

To be eligible to download this data, you need to adjust the LDAP settings: log into the LDAP container (```docker ps |grep ldap  then docker xec -it LDAP_CONTAINER_ID /bin/bash```) and then, change the active zone for PSC organization (description lists the idcom values accepted for this profile):

    ```
echo 'dn: cn=psc,ou=orgs,dc=georchestra,dc=org
changetype: modify
replace: description
description: 62053,62267,62565,62685,62696,62862,62562' > mods.ldif && \
ldapmodify -x -D "cn=admin,dc=georchestra,dc=org" -w secret -H ldap:// -f mods.ldif
    ```

### 4. Testing
- Open http://localhost:8080/foncier/
- configure the headers as suggested in main README,
- Try some extraction on year 2014
- check your mail at http://localhost:8081/webmail/
- you should have received an email with the download link. It should allow you to download an archive containing your  extracted data
