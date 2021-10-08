import datetime as dt
import requests
import os
import csv
from io import StringIO
import logging
import ckan.lib.base as base
from ckan import model
import ckan.lib.helpers as h
import ckan.lib.mailer as mailer
import ckan.logic as logic
from flask import Blueprint


log = logging.getLogger(__name__)

render = base.render
abort = base.abort

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
ValidationError = logic.ValidationError

static_blueprint = Blueprint('odni_static', __name__)

def cookies():
    return base.render('static/cookies.html')

def codeofconduct():
    return base.render('static/codeofconduct.html')

def termsandconditions():
    return base.render('static/termsandconditions.html')

def privacy():
    return base.render('static/privacy.html')

def privacy_notice_reg():
    return base.render('static/privacy_notice_reg.html')


static_blueprint.add_url_rule(
    rule='/privacy',
    view_func=privacy,
    methods=[u'GET'],
)


static_blueprint.add_url_rule(
    rule='/terms-and-conditions',
    view_func=termsandconditions,
    methods=[u'GET'],
)


static_blueprint.add_url_rule(
    rule='/cookies',
    view_func=cookies,
    methods=[u'GET'],
)


static_blueprint.add_url_rule(
    rule='/code-of-conduct',
    view_func=codeofconduct,
    methods=[u'GET'],
)


static_blueprint.add_url_rule(
    rule='/privacy_notice_reg',
    view_func=privacy_notice_reg,
    methods=[u'GET'],
)

