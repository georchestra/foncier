# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, Response, g, stream_with_context
from utils import acces_foncier, extract_cp
from rights_decorator import rights_required
app = Flask(__name__)
app.config.from_object('config.BaseConfig')
app.config.from_envvar('FONCIER_SETTINGS', silent=True)

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
    # get LDAP org object, extract description field with list of areas:
    g.cities = extract_cp(g.org)
    # store user roles & available millésimes
    prefix = app.config['ROLE_PREFIX']
    roles = []
    years = []
    rolesHeader = request.headers.get('sec-roles')
    if rolesHeader is not None:
        roles = rolesHeader.split(';')
        for role in roles:
            if (role.startswith(prefix)):
                years.append(role[len(prefix):])
    g.years = years
    g.roles = roles

@app.route('/', methods=['GET'])
def index():
    if acces_foncier(g.roles) == True:
        return render_template('index.html')
    else:
        return render_template('sorry.html')

@app.route('/submit', methods=['POST'])
@rights_required
def submit():
    values = request.form
    return render_template('thanks.html', values = values)


@app.route('/retrieve/<uuid>', methods=['GET'])
@rights_required
def retrieve(uuid):
    def generate():
        yield 'Hello '
        yield uuid
        yield ' !'
    return Response(stream_with_context(generate()))


if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
