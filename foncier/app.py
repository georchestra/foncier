# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, Response, g
from werkzeug.datastructures import Headers
from utils import acces_foncier, extract_cp
from rights_decorator import rights_required
from tasks import taskmanager
import celery.states as states
import os
import logging

# create the app:
app = Flask(__name__)

ROLE_PREFIX = os.environ.get('ROLE_PREFIX', 'ROLE_FONCIER_')
DEBUG = os.environ.get('DEBUG', 'False')
logger = logging.getLogger('app')


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
    # get LDAP org object, extract description field with list of areas:
    g.cities = extract_cp(g.org)
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
        return render_template('sorry.html')


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
        headers = Headers()
        headers.add('Content-Type', 'application/zip')
        headers.add('Content-Disposition', 'attachment', filename='%s.zip' % uuid)
        return Response(generate(str(res.result)), headers=headers)
    elif res.state == states.STARTED:
        return render_template('started.html', uuid=uuid)
    elif res.state == states.FAILURE:
        return render_template('failure.html', error=res.result)
    else: # PENDING and other states (include unknown UUID)
        return render_template('pending.html', uuid=uuid)

if __name__ == '__main__':
    app.run(debug=DEBUG=="True")
