# -*- coding: utf-8 -*-
from flask.ext.wtf import Form, TextAreaField, SubmitField, required
from flaskext.babel import lazy_gettext as _

class CommentForm(Form):

    comment = TextAreaField(validators=[
                            required(message=_("Comment is required"))])

    submit = SubmitField(_("Save"))
    cancel = SubmitField(_("Cancel"))


class CommentAbuseForm(Form):

    complaint = TextAreaField("Complaint", validators=[
                              required(message=\
                                       _("You must enter the details"
                                         " of the complaint"))])


    submit = SubmitField(_("Send"))
