if not session.token and not request.function=='rss': redirect(LOGIN)

def index():
    announcements=accessible('announcement')\
         (db.announcement.expires_on>=today)\
         (db.user.id==db.announcement.owner)\
         (~db.announcement.id.belongs(db(db.ignore_announcement.user==user_id)\
                               ._select(db.ignore_announcement.announcement)))\
         .select(orderby=~db.announcement.posted_on|db.announcement.id)
    return dict(announcements=find_groups(announcements))

def ignore_announcement():
    if len(request.args)==1:
        id=request.args[0]
        db.ignore_announcement.insert(user=user_id,announcement=id)
    redirect(URL(r=request,f='index'))

def post_announcement():
    form=SQLFORM(db.announcement,fields=db.announcement.public_fields)
    form.vars.owner=user_id
    if form.accepts(request.vars,session):
        print g_tuple
        id=db.access.insert(users_group=g_tuple[1],table_name='announcement',\
                            record_id=form.vars.id,access_type='read')
        session.flash='announcement posted'
        redirect_change_permissions(db.announcement,form.vars.id)
    return dict(form=form)

def edit_announcement():
    if len(request.args)<1: redirect(URL(r=request,f='index'))
    rows=db(db.announcement.id==request.args[0])\
           (db.announcement.owner==user_id).select()
    if not len(rows): redirect(URL(r=request,f='index'))
    form=SQLFORM(db.announcement,rows[0],deletable=True,\
                 fields=db.announcement.public_fields,showid=False)
    if form.accepts(request.vars,session):
        if request.vars.delete_this_record=='on':
            session.flash='announcement deleted'
        else:
            session.flash='announcement saved'
        redirect(URL(r=request,f='index'))
    return dict(form=form)

def rss():
    response.headers['Content-Type']='application/rss+xml'
    import gluon.contrib.rss2 as rss2
    requested_groups=request.vars.groups or '1'
    try: requested_groups=tuple([int(i) for i in requested_groups.split(',')])
    except: return ''
    entries=db(db.announcement.id==db.access.record_id)\
            (db.access.table_name=='announcement')\
            (db.access.users_group.belongs(requested_groups))\
            (db.announcement.to_rss==True)\
            (db.user.id==db.announcement.owner)\
            .select(groupby=db.announcement.id)
    items = [rss2.RSSItem(
               title=entry.announcement.title,
               link=MAIN,
               author=entry.user.email,
               description = entry.announcement.body,
               pubDate = entry.announcement.posted_on) for entry in entries]
    rss = rss2.RSS2(title='public rss for groups '+str(requested_groups),
       link = MAIN,
       description = str(requested_groups),
       lastBuildDate = datetime.datetime.now(),
       items=items)
    return rss2.dumps(rss)
