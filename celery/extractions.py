# -*- coding: utf-8 -*-

import os
import time
import tempfile
import shutil
from zipfile import ZipFile
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from celery import Celery
from distutils.dir_util import copy_tree
import psycopg2
from subprocess import Popen, PIPE
from os import remove, listdir
from os.path import isfile, join


env=os.environ
CELERY_BROKER_URL = env.get('CELERY_BROKER_URL', 'redis://localhost:6379'),
CELERY_RESULT_BACKEND = env.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379')

# CAUTION - SMTP_PORT env var might have value tcp://172.17.0.2:25
# in docker container linked with another "smtp" container.
# Reason why we're using LOCAL_SMTP_PORT instead
SMTP_HOST = env.get('LOCAL_SMTP_HOST', 'localhost')
SMTP_PORT = env.get('LOCAL_SMTP_PORT', 25)

MAIL_FROM = env.get('MAIL_FROM', 'ppige@epf-npdc.fr')
MAIL_SUBJECT = env.get('MAIL_SUBJECT', '[PPIGE - Foncier] Votre extraction')

BASE_URL = env.get('BASE_URL', 'http://localhost:8080')

FONCIER_EXTRACTS_DIR = env.get('FONCIER_EXTRACTS_DIR', '/tmp')
FONCIER_STATIC_DIR = env.get('FONCIER_STATIC_DIR')

PG_CONNECT_STRING = env.get("PG_CONNECT_STRING")

taskmanager = Celery('extractions',
                     broker=CELERY_BROKER_URL,
                     backend=CELERY_RESULT_BACKEND)


def run_command(args):
    """
    Run command specified by args. If exit code is not 0 then full command line, STDOUT, STDERR are printed and an
    Exception is raised
    :param args: array of argument
    :return: None
    """
    p = Popen(args, stdout=PIPE, stderr=PIPE)
    p.wait()

    if p.returncode != 0:
        print("Command: %s" % " ".join(args))
        print("Exit code: %s" % p.returncode)
        print("STDOUT: %s" % p.stdout.read().decode())
        print("STDERR: %s" % p.stderr.read().decode())
        raise Exception("Error running %s" % " ".join(args))


def get_all_tables(conn, year):
    """
    List tables in schema foncier_<year> where year is the second argument
    :param conn: a psycopg connection instance
    :param year: numeric year to append to 'foncier_' to build schema name
    :return: array of table name
    """
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'foncier_%s'" % year)
    res = [res[0] for res in cur.fetchall()]
    cur.close()
    return res


def export_schema_to_shapefile_or_mapinfo(year, proj, output_dir, format, conn, pg_connect_string):
    """
    Extract all table in schema foncier_<year> where 'year' is the first argument and generates files according to
    'format' in 'output_dir' folder.
    :param year: numeric year to append to 'foncier_' to build schema name
    :param proj: output projection
    :param output_dir: folder where files will be writen
    :param format: ogr2ogr file format like : "ESRI Shapefile" or "MapInfo File"
    :param conn: a psycopg connection instance
    :param pg_connect_string: a string that contains option to connect to database with ogr2ogr. 'schema' option will
    be added
    :return: None
    """
    for table in get_all_tables(conn, year):
        args = ["ogr2ogr", 
                "-a_srs", "EPSG:%s" % proj,
                "-t_srs", "EPSG:%s" % proj,
                "-f", format, output_dir,
                "PG:%s schemas=foncier_%s" % (pg_connect_string, year),
                table]
        run_command(args)


def export_schema_to_sql(year, proj, output_dir, conn, pg_connect_string):
    """
    Extract all table in schema foncier_<year> where 'year' is the first argument and one sql file to create schema,
    tables and inserts data
    :param year: numeric year to append to 'foncier_' to build schema name
    :param proj: output projection
    :param output_dir: folder where files will be writen
    :param conn: a psycopg connection instance
    :param pg_connect_string: a string that contains option to connect to database with ogr2ogr. 'schemas' option will
    be added
    :return: None
    """
    with open(join(output_dir, "foncier_%s.sql" % year), 'wb') as f:
        f.write(("CREATE SCHEMA foncier_%s;\n" % year).encode())

        for table in get_all_tables(conn, year):
            table_output_file = join(output_dir, "export_table_%s.sql" % table)
            args = ["ogr2ogr",
                    "-a_srs", "EPSG:%s" % proj,
                    "-t_srs", "EPSG:%s" % proj,
                    "-f", "PGDump", table_output_file,
                    "PG:%s schemas=foncier_%s" % (pg_connect_string, year),
                    table,
                    "-lco", "SCHEMA=foncier_%s" % year,
                    "-lco", "SRID=%s" % proj,
                    "-lco", "CREATE_SCHEMA=off",
                    "-lco", "DROP_TABLE=off"]
            run_command(args)

            # append result to the main SQL file
            with open(table_output_file, 'rb') as table_file:
                f.write(table_file.read())
            remove(table_output_file)


def sendmail(to, message):
    msg = MIMEText(message.encode('utf-8'), _charset='utf-8')
    msg['Subject'] = MAIL_SUBJECT
    msg['From'] = MAIL_FROM
    msg['To'] = to
    try:
        smtpObj = SMTP(SMTP_HOST, SMTP_PORT)
        smtpObj.sendmail(MAIL_FROM, [to], msg.as_string())
        smtpObj.quit()
        print('Successfully sent email to %s' % to)
    except SMTPException:
        print('Error: unable to send email to %s' % to)


@taskmanager.task(name='extraction.do')
def do(year, format, proj, email, cities):

    uuid = do.request.id
    extraction_id = 'foncier_{0}_{1}_{2}_{3}'.format(year, format, proj, uuid)
    sendmail(email, "Le traitement a commencé")
    tmpdir = tempfile.mkdtemp(dir=FONCIER_EXTRACTS_DIR, prefix="%s-" % extraction_id)
    print('Created temp dir %s' % tmpdir)

    if (FONCIER_STATIC_DIR is not None):
        try:
            copy_tree(FONCIER_STATIC_DIR, tmpdir)
        except IOError as e:
            print('IOError copying %s to %s' % (FONCIER_STATIC_DIR, tmpdir))

    # TODO sanitize input

    # launch extraction
    with psycopg2.connect(PG_CONNECT_STRING) as conn:
        if format == "shp":
            export_schema_to_shapefile_or_mapinfo(year, proj, tmpdir, "ESRI Shapefile", conn, PG_CONNECT_STRING)
        elif format == "mifmid":
            export_schema_to_shapefile_or_mapinfo(year, proj, tmpdir, "MapInfo File", conn, PG_CONNECT_STRING)
        elif format == "postgis":
            export_schema_to_sql(year, proj, tmpdir, conn, PG_CONNECT_STRING)
        else:
            raise Exception("Invalid format : %s" % format)

    # create ZIP archive
    try:
        zip_name = join(FONCIER_EXTRACTS_DIR, "%s.zip" % extraction_id)
        with ZipFile(zip_name, 'w') as myzip:
            for file in [f for f in listdir(tmpdir) if isfile(join(tmpdir, f))]:
                myzip.write(join(tmpdir, file), arcname=join(extraction_id, file))
    except IOError as e:
        print('IOError while zipping %s' % tmpdir)

    # delete directory after zipping:
    shutil.rmtree(tmpdir)
    print('Removed dir %s' % tmpdir)
    # send email with a link to download the generated archive:
    sendmail(email, 'Extraction terminée: %s/retrieve/%s' % (BASE_URL, uuid))
    # return zip file name
    return zip_name

