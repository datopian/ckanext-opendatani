import re
from six import string_types, text_type
import logging

import ckan.model as model
# from ckan.lib import activity_streams
import ckan.logic as logic
import ckan.lib.helpers as h
from ckan.plugins import toolkit
import ckan.authz as authz
import ckan.lib.dictization.model_dictize as model_dictize
from ckanext.showcase.model import ShowcasePackageAssociation


log = logging.getLogger(__name__)


def get_user_name(user):
    if not isinstance(user, model.User):
        user_name = text_type(user)
        user = model.User.get(user_name)
        if not user:
            return user_name
    if user:
        name = user.name if model.User.VALID_NAME.match(user.name) else user.id
        displayname = user.display_name or user.fullname or user.name
        return displayname

def get_snippet_actor(activity, detail):
    return get_user_name(activity['user_id'])

def get_snippet_user(activity, detail):
    return get_user_name(activity['object_id'])

def get_snippet_dataset(activity, detail):
    data = activity['data']
    pkg_dict = data.get('package') or data.get('dataset')
    return pkg_dict.get('title') or pkg_dict['name']

def get_snippet_tag(activity, detail):
    return detail['data']['tag']['name']

def get_snippet_group(activity, detail):
    return activity['data']['group'].get('title') or activity['data']['group']['name']

def get_snippet_organization(activity, detail):
    return activity['data']['group'].get('title') or activity['data']['group']['name']

def get_snippet_extra(activity, detail):
    return detail['data']['package_extra']['key']

def get_snippet_resource(activity, detail):
    return detail['data']['resource'].get('title') or detail['data']['resource']['name']

def get_dataset_url(activity):
    data = activity['data']
    pkg_dict = data.get('package') or data.get('dataset')
    return h.url_for(controller='package', action='read', id=pkg_dict['name'])

activity_snippet_functions = {
    'actor': get_snippet_actor,
    'user': get_snippet_user,
    'dataset': get_snippet_dataset,
    'tag': get_snippet_tag,
    'group': get_snippet_group,
    'organization': get_snippet_organization,
    'extra': get_snippet_extra,
    'resource': get_snippet_resource,
}

# def activity_list_to_text(activity_stream):
#     activity_list = [] # These are the activity stream messages.
#     context = {'ignore_auth': True}
#     for activity in activity_stream:
#         detail = None
#         activity_type = activity['activity_type']
#         # Some activity types may have details.
#         if activity_type in activity_streams.activity_stream_actions_with_detail:
#             details = logic.get_action('activity_detail_list')(context=context,
#                 data_dict={'id': activity['id']})
#             # If an activity has just one activity detail then render the
#             # detail instead of the activity.
#             if len(details) == 1:
#                 detail = details[0]
#                 object_type = detail['object_type']

#                 if object_type == 'PackageExtra':
#                     object_type = 'package_extra'

#                 new_activity_type = '%s %s' % (detail['activity_type'],
#                                             object_type.lower())
#                 if new_activity_type in activity_streams.activity_stream_string_functions:
#                     activity_type = new_activity_type

#         if not activity_type in activity_streams.activity_stream_string_functions:
#             raise NotImplementedError("No activity renderer for activity "
#                 "type '%s'" % activity_type)

#         activity_msg = activity_streams.activity_stream_string_functions[activity_type](context,
#                 activity)
#         activity_msg = str(activity_msg.replace('{actor} ', ''))
#         activity_msg = activity_msg[0].upper() + activity_msg[1:]

#         # Get the data needed to render the message.
#         matches = re.findall('\{([^}]*)\}', activity_msg)
#         data = {}
#         for match in matches:
#             snippet = activity_snippet_functions[match](activity, detail)
#             data[str(match)] = snippet

#         activity_list.append({'msg': activity_msg.format(**data),
#                               'type': activity_type.replace(' ', '-').lower(),
#                               'timestamp': activity['timestamp'],
#                               'is_new': activity.get('is_new', False),
#                               'dataset_url': get_dataset_url(activity)})
#     return activity_list


def _get_action(action, context_dict, data_dict):
    return toolkit.get_action(action)(context_dict, data_dict)


def is_admin(user, org):
    """
    Returns True if user is site admin or admin of the
    organization and the given organization exists
    :param user: user name
    :type user: string
    :param org: organization name
    :type org: string
    :returns: True/False
    :rtype: boolean
    """

    user_orgs = _get_action(
        'organization_list_for_user',
        {'user': user}, {'user': user})

    return any(
        [(i.get('capacity') == 'admin')
         and i.get('name') == org for i in user_orgs]) \
        or authz.is_sysadmin(user)


def verify_datasets_exist(org):
    """
    Returns True if the number of datasets (including private)
    for a given organization is greater than 0.
    :param org: organization name
    :type org: string
    :returns: dataset count
    :rtype: integer
    """

    data_dict = {'include_private': True}

    if org:
        data_dict['q'] = 'organization:{0}'.format(org)

    return toolkit.get_action('package_search')({}, data_dict).get('count') > 0


def get_showcase_List(limit):
    q = model.Session.query(model.Package) \
    .filter(model.Package.type == 'showcase') \
    .filter(model.Package.state == 'active')

    showcase_list = []
    for pkg in q.limit(limit).all():
        showcase_list.append(model_dictize.package_dictize(pkg, { 'model' : model }))

    for idx, showcase in enumerate(showcase_list):
        # get a list of package ids associated with showcase id
        pkg_id_list = ShowcasePackageAssociation.get_package_ids_for_showcase(showcase['id'])
        showcase_list[idx]['package_count'] = len(pkg_id_list)
    return showcase_list