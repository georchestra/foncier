# -*- coding: utf-8 -*-

from flask import Flask, Markup, render_template, request, Response, g
from werkzeug.datastructures import Headers
from utils import acces_foncier, extract_cp
from rights_decorator import rights_required
from tasks import taskmanager
import celery.states as states
import os
import logging

# create the app:
app = Flask(__name__)
logger = logging.getLogger('app')

env=os.environ
DEBUG = env.get('DEBUG', 'False')
ROLE_PREFIX = env.get('ROLE_PREFIX', 'ROLE_FONCIER_')
SORRY_PAGE_BODY = Markup(env.get('SORRY_PAGE_BODY', "<p>Cette application est réservée aux ayants droits PPIGE <a href='?login'>connectés</a> ayant signé un <a href='http://www.ppige-npdc.fr/portail/doc/Acte_Engagementdynamique2015_vF_cle6ca269.pdf'>acte d'engagement</a> en vue de la délivrance de fichiers fonciers.</p><p>Il semblerait que cette condition ne soit pas remplie pour votre compte, ou bien que le traitement de votre demande ne soit pas encore achevé.</p><p>Pour obtenir un accès à ces fichiers, vous devez obtenir l’autorisation de la Direction Générale de l'Aménagement, du Logement et de la Nature (DGALN). La procédure ci-dessous vous accompagne dans cette démarche.</p><p>Envoyer votre demande à la DGALN par un email remplissant les conditions suivantes :<ol><li>Objet du message : <b>[PPIGE] Demande de téléchargement de fichiers fonciers à partir du site de la PPIGE</b></li><li>Destinataire principal : <b>autorisations-fichiers-fonciers@developpement-durable.gouv.fr</b> </li><li>Destinataires en copie : <b>fichiers-fonciers@developpement-durable.gouv.fr, ppige@epf-npdc.fr</b></li><li>Pièce jointe : le <a href='http://www.ppige-npdc.fr/portail/doc/Acte_Engagementdynamique2015_vF_cle6ca269.pdf'>document DGALN-AD</a> dûment rempli. </li></ol></p><p>Votre demande sera traitée correctement et dans les plus brefs délais si vous respectez ces étapes.</p><p>Votre accès à l'extracteur des fichiers fonciers sera ouvert par la PPIGE dès réception de la validation de la DGALN.</p><p>Nous vous invitons à consulter également le document <a href='http://www.ppige-npdc.fr/portail/doc/AE-DGFIP-DGALN.pdf'>AE-DGFiP-DGALN</a></p>"))

@app.before_request
def load_user():
    # store username during request treatment
    g.username = request.headers.get('sec-username')
    g.firstname = request.headers.get('sec-firstname')
    g.lastname = request.headers.get('sec-lastname')
    g.email = request.headers.get('sec-email')
    # store org
    # if user is memberOf cn=psc,ou=orgs,dc=georchestra,dc=org then sec-org is "psc"
    g.org = request.headers.get('sec-org')
    # Nice org name:
    g.orgname = request.headers.get('sec-orgname')
    try:
        # get LDAP org object, extract description field with list of areas:
        g.cities = extract_cp(g.org)
    except ValueError:
        return render_template('sorry.html', body=SORRY_PAGE_BODY)
    # store user roles & available millésimes
    prefix = ROLE_PREFIX
    rolesHeader = request.headers.get('sec-roles')
    g.roles = rolesHeader.split(';') if rolesHeader is not None else []
    g.years = sorted([int(r[len(prefix):]) for r in g.roles if r.startswith(prefix)])


@app.route('/', methods=['GET'])
def index():
    if acces_foncier(g.roles) and len(g.cities) > 0:
        return render_template('index.html', years=[str(y) for y in g.years])
    else:
        return render_template('sorry.html', body=SORRY_PAGE_BODY)


@app.route('/submit', methods=['POST'])
@rights_required
def submit():
    values = request.form

    # Validate form, valid values for format : shp, mifmid, postgis
    year = int(values.get('year'))
    if year not in g.years:
        raise TypeError("year not allowed : '%s'" % year)
    if values.get('format') not in ['shp', 'mifmid', 'postgis']:
        raise TypeError("Invalid format : '%s'" % values.get('format'))
    proj = int(values.get('proj'))

    task = taskmanager.send_task('extraction.do', args=[
        year,
        values.get('format'),
        proj,
        g.email,
        g.cities], kwargs={})
    return render_template('thanks.html', values=values, uuid=task.id)


@app.route('/retrieve/<string:uuid>', methods=['GET'])
@rights_required
def retrieve(uuid):
    res = taskmanager.AsyncResult(uuid)

    def generate(filepath):
        with open(filepath, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                yield data
    if res.state == states.SUCCESS:
        filepath = str(res.result)
        headers = Headers()
        headers.add('Content-Type', 'application/zip')
        headers.add('Content-Disposition', 'attachment', filename='%s.zip' % uuid)
        headers.add('Content-Length', str(os.path.getsize(filepath)))
        return Response(generate(filepath), headers=headers)
    elif res.state == states.STARTED:
        return render_template('started.html', uuid=uuid)
    elif res.state == states.FAILURE:
        return render_template('failure.html', error=res.result)
    else: # PENDING and other states (include unknown UUID)
        return render_template('pending.html', uuid=uuid)

if __name__ == '__main__':
    app.run(debug=DEBUG=="True")
