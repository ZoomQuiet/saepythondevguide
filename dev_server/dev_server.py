#!/usr/bin/env python

"""Simple development server

Make sure you're use python 2.6 for developing

"""
import sys
import os
import os.path
import re
import imp
import yaml
from werkzeug.serving import run_simple
from optparse import OptionParser

def setup_sae_environ(options):
    # Add dummy pylibmc module
    import sae.memcache
    sys.modules['pylibmc'] = sae.memcache

    # Add app_root to sys.path
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    conf_path = os.path.join(cwd, 'config.yaml')
    conf = yaml.load(open(conf_path, "r"))
    appname = conf['name']
    appversion = str(conf['version'])

    if options.mysql:
        import sae.const

        p = re.compile('^(.+):(.+)@(.+):(\d+)$')
        m = p.match(options.mysql)
        if not m:
            raise Exception("Invalid mysql configuration")

        user, password, host, port = m.groups()
        dbname = 'app_' + appname
        sae.const.MYSQL_DB = dbname
        sae.const.MYSQL_USER = user
        sae.const.MYSQL_PASS = password
        sae.const.MYSQL_PORT = port
        sae.const.MYSQL_HOST = host

        print 'MySQL: %s.%s' % (options.mysql, dbname)
    else:
        print 'MySQL config not found'

    if options.storage:
        os.environ['STORAGE_PATH'] = os.path.abspath(options.storage)
        
    # Add custom environment variable
    os.environ['HTTP_HOST'] = 'localhost:%d' % options.port
    os.environ['APP_NAME'] = appname
    os.environ['APP_VERSION'] = appversion

def main(options):
    setup_sae_environ(options)

    try:
        index = imp.load_source('index', 'index.wsgi')
    except IOError:
        print "Seems you don't have an index.wsgi"
        return

    if not hasattr(index, 'application'):
        print "application not found in index.wsgi"
        return

    if not callable(index.application):
        print "application is not a callable"
        return

    app_root = os.getcwd()
    statics = {
        '/static': os.path.join(app_root,  'static'),
        '/media': os.path.join(app_root,  'media'),
        '/favicon.ico': os.path.join(app_root,  'favicon.ico'),
    }
    if options.storage:
        # stor dispatch: for test usage only
        statics['/stor-stub'] = os.path.abspath(options.storage)

    # FIXME: All files under current directory
    files = ['index.wsgi']

    try:
        run_simple('localhost', options.port, index.application,
                    use_reloader = True,
                    use_debugger = True,
                    extra_files = files,
                    static_files = statics, threaded=True)
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-p", "--port", type="int", dest="port", default="8080",
                      help="Which port to listen")
    parser.add_option("--mysql", dest="mysql", help="Mysql configuration: user:password@host:port")
    parser.add_option("--storage-path", dest="storage", help="Directory used as local stoarge")
    (options, args) = parser.parse_args()

    main(options)
