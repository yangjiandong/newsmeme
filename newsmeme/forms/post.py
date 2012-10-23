# -*- coding: utf-8 -*-
from flask.ext.wtf import Form, TextField, TextAreaField, RadioField, \
        SubmitField, ValidationError, optional, required, url

from flaskext.babel import gettext, lazy_gettext as _

from newsmeme.models import Post
from newsmeme.extensions import db

class PostForm(Form):

    #title = TextField(_("Title of your post"), validators=[
    #                  required(message=_("Title required"))])
    title = TextField(u"发表标题", validators=[
                      required(message=u"必须有标题")])

    link = TextField(_("Link"), validators=[
                     optional(),
                     url(message=_("This is not a valid URL"))])

    description = TextAreaField(_("Description"))

    tags = TextField(_("Tags"))

    access = RadioField(_("Who can see this post ?"),
                        default=Post.PUBLIC,
                        coerce=int,
                        choices=((Post.PUBLIC, _("Everyone")),
                                 (Post.FRIENDS, _("Friends only")),
                                 (Post.PRIVATE, _("Just myself"))))

    submit = SubmitField(_("Save"))

    def __init__(self, *args, **kwargs):
        self.post = kwargs.get('obj', None)
        super(PostForm, self).__init__(*args, **kwargs)

    def validate_link(self, field):
        posts = Post.query.public().filter_by(link=field.data)
        if self.post:
            posts = posts.filter(db.not_(Post.id==self.post.id))
        if posts.count():
            raise ValidationError, gettext("This link has already been posted")


