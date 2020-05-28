from django.db import models
from django.core.mail import send_mail
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.base_user import BaseUserManager

import ast

class CustomUserManager(BaseUserManager):
    """ユーザーマネージャー"""
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('The given username and email must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """カスタムユーザーモデル."""
    username_validator = UnicodeUsernameValidator()

    email = models.EmailField(_('email address'), unique=True)

    username = models.CharField(
        _('username'),
        max_length=50,
        unique=True,
        help_text=_('Required. 50 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_(
            'Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    max_problem_num = models.IntegerField(
        _('max_problem_num'),
        default=20,
        help_text=_(
            'maximum number of problems that can create by the user.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    submit_history = models.CharField(
        _('submit_history'),
        max_length=50000,
        default="[]",
        help_text=_('submitted judgeID list')
    )

    problem_list = models.CharField(
        _('problem_list'),
        max_length=50000,
        default="[]",
        help_text=_('Created Problem List')
    )

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in
        between."""
        return self.username

    def get_short_name(self):
        """Return the short name for the user."""
        return self.username

    def get_submit_history(self):
        return ast.literal_eval(self.submit_history)

    def add_submit(self, id,name):
        val = ast.literal_eval(self.submit_history)
        if len(val) > 300:
            val.pop(0)
        val.append([id,name])
        self.submit_history = str(val)

    def get_problem_list(self):
        return ast.literal_eval(self.problem_list)

    def add_problem(self, ids, name):
        val = ast.literal_eval(self.submit_history)
        val.append([ids,name])
        self.problem_list = str(val)

    def remove_problem(self, problemID):
        val = self.problem_list.split(',,')
        val.remove(problemID)
        self.problem_list = ',,'.join(val)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
