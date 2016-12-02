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


Notez pour finir qu'il est possible de surcharger la [configuration par défaut](foncier/config.py) par d'autres valeurs (un exemple [ici](resources/config.py)) via:
```
export FLASK_APP=foncier/app.py
export FONCIER_SETTINGS=/path/to/config.py
flask run
```
