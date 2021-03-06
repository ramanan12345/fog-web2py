from gluon.admin import apath
# ###########################################################
# ## make sure administrator is on localhost or https
# ###########################################################

http_host = request.env.http_host.split(':')[0]

try:
    from gluon.contrib.gql import GQLDB
    session_db = GQLDB()
    session.connect(request, response, db=session_db)
    hosts = (http_host, )
except Exception:
    hosts = (http_host, socket.gethostname(),
             socket.gethostbyname(http_host),
             '::1','127.0.0.1','::ffff:127.0.0.1')

remote_addr = request.env.remote_addr

if request.env.http_x_forwarded_for or request.env.wsgi_url_scheme\
     in ['https', 'HTTPS']:
    session.secure()
elif not remote_addr in hosts:
    raise HTTP(200, T('Admin is disabled because insecure channel'))

try:
    _config = {}
    port = int(request.env.server_port)
    restricted(open(apath('../parameters_%i.py' % port, request), 'r').read(), _config)

    if not 'password' in _config or not _config['password']:
        raise HTTP(200, T('admin disabled because no admin password'))
except IOError:
    import gluon.fileutils
    if request.env.web2py_runtime_gae:
        if gluon.fileutils.check_credentials(request):
            session.authorized = True
            session.last_time = time.time()
        else:
            raise HTTP(200,
                       T('admin disabled because not supported on google apps engine'))
    else:
        raise HTTP(200, T('admin disabled because unable to access password file'))

# ###########################################################
# ## session expiration
# ###########################################################

t0 = time.time()
if session.authorized:

    if session.last_time and session.last_time < t0 - EXPIRATION:
        session.flash = T('session expired')
        session.authorized = False
    else:
        session.last_time = t0

if not session.authorized and not \
    (request.controller == 'default' and \
     request.function == 'index'):

    if request.env.query_string:
        query_string = '?' + request.env.query_string
    else:
        query_string = ''

    url = request.env.path_info + query_string
    redirect(URL(request.application, 'default', 'index', vars=dict(send=url)))
elif session.authorized and \
     request.controller == 'default' and \
     request.function == 'index':
    redirect(URL(request.application, 'default', 'site'))


