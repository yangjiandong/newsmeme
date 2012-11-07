# -*- coding: utf-8 -*-
from flask.ext.wtf import Form, HiddenField, BooleanField, TextField, \
        PasswordField, SubmitField, TextField, RecaptchaField, \
        ValidationError, required, email, equal_to, regexp

from flaskext.babel import gettext, lazy_gettext as _

from newsmeme.models import User
from newsmeme.extensions import db

from .validators import is_username

class LoginForm(Form):

    next = HiddenField()

    remember = BooleanField(u"保存登录信息")

    login = TextField(u"用户名或邮箱", validators=[
                      required(message=\
                               u"必须提供用户名或密码")])

    password = PasswordField(u"密码")

    submit = SubmitField(u"登录")

class SignupForm(Form):

    next = HiddenField()

    username = TextField(u"用户名", validators=[
                         required(message=_("Username required")),
                         is_username])

    password = PasswordField(u"密码", validators=[
                             required(message=_("Password required"))])

    password_again = PasswordField(u"密码确认", validators=[
                                   equal_to("password", message=\
                                            _("Passwords don't match"))])

    email = TextField(u"邮箱", validators=[
                      required(message=_("Email address required")),
                      email(message=_("A valid email address is required"))])

    recaptcha = RecaptchaField(_("Copy the words appearing below"))

    submit = SubmitField(u"注册")

    def validate_username(self, field):
        user = User.query.filter(User.username.like(field.data)).first()
        if user:
            raise ValidationError, u"改用户名已存在"

    def validate_email(self, field):
        user = User.query.filter(User.email.like(field.data)).first()
        if user:
            raise ValidationError, gettext("This email is taken")


class EditAccountForm(Form):

    username = TextField(u"用户名", validators=[
                         required(_("Username is required")), is_username])

    email = TextField(u"邮箱", validators=[
                      required(message=_("Email address required")),
                      email(message=_("A valid email address is required"))])

    receive_email = BooleanField(_("Receive private emails from friends"))

    email_alerts = BooleanField(_("Receive an email when somebody replies "
                                  "to your post or comment"))


    submit = SubmitField(u"保存")

    def __init__(self, user, *args, **kwargs):
        self.user = user
        kwargs['obj'] = self.user
        super(EditAccountForm, self).__init__(*args, **kwargs)

    def validate_username(self, field):
        user = User.query.filter(db.and_(
                                 User.username.like(field.data),
                                 db.not_(User.id==self.user.id))).first()

        if user:
            raise ValidationError, gettext("This username is taken")

    def validate_email(self, field):
        user = User.query.filter(db.and_(
                                 User.email.like(field.data),
                                 db.not_(User.id==self.user.id))).first()
        if user:
            raise ValidationError, gettext("This email is taken")


class RecoverPasswordForm(Form):

    email = TextField("Your email address", validators=[
                      email(message=_("A valid email address is required"))])

    submit = SubmitField(_("Find password"))


class ChangePasswordForm(Form):

    activation_key = HiddenField()

    password = PasswordField("Password", validators=[
                             required(message=_("Password is required"))])

    password_again = PasswordField(_("Password again"), validators=[
                                   equal_to("password", message=\
                                            _("Passwords don't match"))])

    submit = SubmitField(_("Save"))


class DeleteAccountForm(Form):

    recaptcha = RecaptchaField(_("Copy the words appearing below"))

    submit = SubmitField(_("Delete"))


