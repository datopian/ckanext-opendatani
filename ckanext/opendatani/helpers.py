import re
from six import string_types, text_type

import ckan.model as model
from ckan.lib import activity_streams
import ckan.logic as logic
import ckan.lib.helpers as h

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

def activity_list_to_text(activity_stream):
    activity_list = [] # These are the activity stream messages.
    context = {'ignore_auth': True}
    for activity in activity_stream:
        detail = None
        activity_type = activity['activity_type']
        # Some activity types may have details.
        if activity_type in activity_streams.activity_stream_actions_with_detail:
            details = logic.get_action('activity_detail_list')(context=context,
                data_dict={'id': activity['id']})
            # If an activity has just one activity detail then render the
            # detail instead of the activity.
            if len(details) == 1:
                detail = details[0]
                object_type = detail['object_type']

                if object_type == 'PackageExtra':
                    object_type = 'package_extra'

                new_activity_type = '%s %s' % (detail['activity_type'],
                                            object_type.lower())
                if new_activity_type in activity_streams.activity_stream_string_functions:
                    activity_type = new_activity_type

        if not activity_type in activity_streams.activity_stream_string_functions:
            raise NotImplementedError("No activity renderer for activity "
                "type '%s'" % activity_type)

        activity_msg = activity_streams.activity_stream_string_functions[activity_type](context,
                activity)
        activity_msg = str(activity_msg.replace('{actor} ', ''))
        activity_msg = activity_msg[0].upper() + activity_msg[1:]

        # Get the data needed to render the message.
        matches = re.findall('\{([^}]*)\}', activity_msg)
        data = {}
        for match in matches:
            snippet = activity_snippet_functions[match](activity, detail)
            data[str(match)] = snippet

        activity_list.append({'msg': activity_msg.format(**data),
                              'type': activity_type.replace(' ', '-').lower(),
                              'timestamp': activity['timestamp'],
                              'is_new': activity.get('is_new', False),
                              'dataset_url': get_dataset_url(activity)})
    return activity_list