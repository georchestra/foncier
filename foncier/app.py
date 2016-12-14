# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, Response, g, stream_with_context
from utils import acces_foncier, extract_cp
from rights_decorator import rights_required
from tasks import taskmanager
from celery.result import AsyncResult
import celery.states as states
import os

# create the app:
app = Flask(__name__)

ROLE_PREFIX = os.environ.get('ROLE_PREFIX', 'ROLE_FONCIER_')
DEBUG = os.environ.get('DEBUG', 'False')

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
    g.years = sorted([r[len(prefix):] for r in g.roles if r.startswith(prefix)])


@app.route('/', methods=['GET'])
def index():
    if acces_foncier(g.roles) and len(g.cities) > 0:
        return render_template('index.html')
    else:
        return render_template('sorry.html')


@app.route('/submit', methods=['POST'])
@rights_required
def submit():
    values = request.form
    task = taskmanager.send_task('extraction.do', args=[
        values.get('year'),
        values.get('format'),
        values.get('proj'),
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

    # TODO: handle erroneous uuids
    if res.state == states.PENDING:
        return render_template('retrieve.html', uuid=uuid)
    else:
        return Response(generate(str(res.result)), mimetype='application/zip')

if __name__ == '__main__':
    app.run(debug=DEBUG=="True")
