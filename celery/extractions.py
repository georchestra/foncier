# -*- coding: utf-8 -*-

import os
import tempfile
import shutil
import logging
import time
from zipfile import ZipFile
from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from celery import Celery
from distutils.dir_util import copy_tree
import psycopg2
from subprocess import Popen, PIPE
from os import remove, listdir
from os.path import join, isfile


logger = logging.getLogger('worker')

env=os.environ
CELERY_BROKER_URL = env.get('CELERY_BROKER_URL', 'redis://localhost:6379'),
CELERY_RESULT_BACKEND = env.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379')

# CAUTION - SMTP_PORT env var might have value tcp://172.17.0.2:25
# in docker container linked with another "smtp" container.
# Reason why we're using LOCAL_SMTP_PORT instead
SMTP_HOST = env.get('LOCAL_SMTP_HOST', 'localhost')
SMTP_PORT = env.get('LOCAL_SMTP_PORT', 25)

MAIL_FROM = env.get('MAIL_FROM', 'ppige@epf-npdc.fr')
MAIL_SUBJECT = env.get('MAIL_SUBJECT', '[PPIGE - Fichiers fonciers] Votre extraction')

BASE_URL = env.get('BASE_URL', 'http://localhost:8080')

FONCIER_EXTRACTS_DIR = env.get('FONCIER_EXTRACTS_DIR', '/tmp')
FONCIER_EXTRACTS_RETENTION_DAYS = int(env.get('FONCIER_EXTRACTS_RETENTION_DAYS', 1))
FONCIER_STATIC_DIR = env.get('FONCIER_STATIC_DIR')

PG_CONNECT_STRING = env.get("PG_CONNECT_STRING")

PROCESS_TIMEOUT = env.get("PROCESS_TIMEOUT", 3600)

taskmanager = Celery('extractions',
                     broker=CELERY_BROKER_URL,
                     backend=CELERY_RESULT_BACKEND)

# Configure celery to report 'started' state (disable by default in celery)
taskmanager.conf.task_track_started = True


def run_command(args):
    """
    Run command specified by args. If exit code is not 0 then full command line, STDOUT, STDERR are printed and an
    Exception is raised
    :param args: array of argument
    :return: None
    """
    p = Popen(args, stdout=PIPE, stderr=PIPE)
    p.wait(int(PROCESS_TIMEOUT))

    if p.returncode != 0:
        logger.error("Command: %s" % " ".join(args))
        logger.error("Exit code: %s" % p.returncode)
        logger.error("STDOUT: %s" % p.stdout.read().decode())
        logger.error("STDERR: %s" % p.stderr.read().decode())
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


def export_schema_to_shapefile_or_mapinfo(year, proj, cities, output_dir, format, conn, pg_connect_string):
    """
    Extract all table in schema foncier_<year> where 'year' is the first argument and generates files according to
    'format' in 'output_dir' folder.
    :param year: numeric year to append to 'foncier_' to build schema name
    :param proj: output projection
    :param cities: array of INSEE numeric identifier to filter extraction, field 'idcom' will be used
    :param output_dir: folder where files will be writen
    :param format: ogr2ogr file format like : "ESRI Shapefile" or "MapInfo File"
    :param conn: a psycopg connection instance
    :param pg_connect_string: a string that contains option to connect to database with ogr2ogr. 'schema' option will
    be added
    :return: None
    """

    for table in get_all_tables(conn, year):
        args = ["ogr2ogr",
                "-where", "idcom IN (%s)" % ",".join(cities),
                "-a_srs", "EPSG:%s" % proj,
                "-t_srs", "EPSG:%s" % proj,
                "-f", format, output_dir,
                "PG:%s schemas=foncier_%s" % (pg_connect_string, year),
                table]
        run_command(args)


def export_schema_to_sql(year, proj, cities, output_dir, conn, pg_connect_string):
    """
    Extract all table in schema foncier_<year> where 'year' is the first argument and one sql file to create schema,
    tables and inserts data
    :param year: numeric year to append to 'foncier_' to build schema name
    :param proj: output projection
    :param cities: array of INSEE numeric identifier to filter extraction, field 'idcom' will be used
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
                    "-where", "idcom IN (%s)" % ",".join(cities),
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
        logger.info('Successfully sent email to %s' % to)
    except SMTPException:
        logger.error('Error: unable to send email to %s' % to)


@taskmanager.task(name='extraction.do')
def do(year, format, proj, email, cities):

    # clean older files
    now = time.time()
    for f in os.listdir(FONCIER_EXTRACTS_DIR):
        file = join(FONCIER_EXTRACTS_DIR, f)
        if not f.startswith('foncier_') or not isfile(file):
            continue
        try:
            creation = os.path.getctime(file)
        except Exception:
            pass
        if (now - creation) // (24 * 3600) >= FONCIER_EXTRACTS_RETENTION_DAYS:
            try:
                os.unlink(file)
                logger.info('Removed file %s because it was older than %s day(s)' % (f, FONCIER_EXTRACTS_RETENTION_DAYS))
            except Exception:
                pass

    # process request
    uuid = do.request.id
    extraction_id = 'foncier_{0}_{1}_{2}_{3}'.format(year, format, proj, uuid)
    sendmail(email, "Bonjour,\n\nL'extraction de vos fichiers fonciers a commencée. Vous pouvez suivre son cours à cette adresse : %s/retrieve/%s?login\n\nBien cordialement,\nL'équipe PPIGE"
             % (BASE_URL, uuid))
    tmpdir = tempfile.mkdtemp(dir=FONCIER_EXTRACTS_DIR, prefix="%s-" % extraction_id)
    logger.info('Created temp dir %s' % tmpdir)
    datadir = join(tmpdir, 'data')

    # format cities parameter it's stored as string in database
    cities = ["'%s'" % c for c in cities]

    if (FONCIER_STATIC_DIR is not None):
        try:
            copy_tree(FONCIER_STATIC_DIR, tmpdir)
        except IOError as e:
            logger.error('IOError copying %s to %s' % (FONCIER_STATIC_DIR, tmpdir))

    # launch extraction
    with psycopg2.connect(PG_CONNECT_STRING) as conn:
        if format == "shp":
            export_schema_to_shapefile_or_mapinfo(year, proj, cities, datadir, "ESRI Shapefile", conn, PG_CONNECT_STRING)
        elif format == "mifmid":
            export_schema_to_shapefile_or_mapinfo(year, proj, cities, datadir, "MapInfo File", conn, PG_CONNECT_STRING)
        elif format == "postgis":
            export_schema_to_sql(year, proj, cities, datadir, conn, PG_CONNECT_STRING)
        else:
            raise Exception("Invalid format: %s" % format)

    # create ZIP archive
    try:
        zip_name = join(FONCIER_EXTRACTS_DIR, "%s.zip" % extraction_id)
        with ZipFile(zip_name, 'w') as myzip:
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    myzip.write(join(root, file), arcname=join(root[len(FONCIER_EXTRACTS_DIR)+1:], file))

    except IOError as e:
        logger.error('IOError while zipping %s' % tmpdir)

    # delete directory after zipping:
    shutil.rmtree(tmpdir)
    logger.info('Removed dir %s' % tmpdir)
    # send email with a link to download the generated archive:
    sendmail(email, "Bonjour,\n\nVotre extraction est terminée. Vous pouvez la télécharger à l'adresse suivante : %s/retrieve/%s?login\n\nBien cordialement,\nL'équipe PPIGE" % (BASE_URL, uuid))
    # return zip file name
    return zip_name

