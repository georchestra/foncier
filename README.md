# Application d'extraction du Foncier pour la PPIGE

Cette application, bâtie pour fonctionner comme module de l'IDS [geOrchestra](https://github.com/georchestra/georchestra), permet à des utilisateurs authentifiés de commander des extraits de la base de données foncières.

## Pré-requis

Pour fonctionner, l'application nécessite:
 * un LDAP au standard geOrchestra, écoutant sur `localhost:10389` (ceci peut être modifié dans le fichier `config.py`, cf ci-dessous)
 * une base PostgreSQL+PostGIS dans laquelle se trouvent autant de schémas `foncier_XXXX` (où XXXX est un numérique représentant une année) qu'il y a de millésimes de données foncières.

## Installation

### dans un contexte docker
```
docker-compose up
```
Puis RDV sur [http://localhost:8080/](http://localhost:8080/)


### dans un contexte classique

Installons les dépendances:
```
sudo apt-get install python-dev libldap2-dev libsasl2-dev python-virtualenv
virtualenv env
source env/bin/activate
pip install -r resources/requirements.txt
```

Puis lançons l'application avec
```
export FLASK_APP=foncier/app.py
flask run
```
Puis RDV sur [http://localhost:5000/](http://localhost:5000/)


## Utilisation

Si la requête entrante est munie d'un header `sec-roles` composé d'une suite de chaînes de caractères du type `ROLE_FONCIER_XXXX`, séparées par des points virgules (eg: `sec-roles = ROLE_FONCIER_2009;ROLE_FONCIER_2011`) alors la page d'accueil présente un formulaire d'extraction permettant de choisir un millésime à extraire (à choisir parmi les années composant `sec-roles`).

Si de plus, la requête est munie d'un header `sec-org` égalant le `cn` d'un organisme du LDAP (ex: `sec-org = psc`), alors l'extraction est autorisée sur l'ensemble des communes de codes INSEE renseignés dans le champ `description` du dit organisme.

Dans le cas contraire, la réponse de l'application est une page indiquant les modalités d'accès aux fichiers fonciers.
