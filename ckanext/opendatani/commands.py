from ckan.common import OrderedDict
from pylons import config
from ckan.plugins import toolkit
import ckanapi
import logging
import ckan.lib.helpers as h
from ckan import model
import datetime as dt
import emailer

groups = OrderedDict([
    ('health', 'Health'),
    ('education', 'Education'),
    ('finance', 'Finance'),
    ('transport', 'Transport'),
    ('environment', 'Environment & agriculture'),
    ('property', 'Property & land'),
    ('economy', 'Economy, industry & employment'),
    ('tourism', 'Tourism, leisure, culture & arts'),
    ('population', 'Population & society'),
])


class CreateFeaturedGroups(toolkit.CkanCommand):
    '''Create the nine featured groups

    Usage:
      create_featured_groups             - create featured groups
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):
        self._load_config()

        url = config['ckan.site_url']
        ni = ckanapi.LocalCKAN()

        for name, title in groups.items():
            try:
                result = ni.action.group_create(
                    name=name,
                    title=title,
                    image_url='{url}/images/{image}.png'.format(url=url,
                                                                image=name)
                )
                print result
            except ckanapi.ValidationError, e:
                print e


class CheckUpdateFrequency(toolkit.CkanCommand):
    ''' Check update frequency for datasets. '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 0
    min_args = 0

    def command(self):
        self._load_config()
        log = logging.getLogger('ckanext.opendatani')

        log.info('Daily dataset update frequency check started...')

        def frequency_to_timedelta(frequency):
            frequency_periods = {

                "daily": dt.timedelta(days=2),  # 2 so as not to spam dataset maintainers every day
                "weekly": dt.timedelta(days=7),
                "fortnightly": dt.timedelta(days=14),
                "monthly": dt.timedelta(days=30),
                "quarterly": dt.timedelta(days=91),
                "annually": dt.timedelta(days=365),
            }
            if not frequency:
                pass
            else:
                return frequency_periods[frequency]

        data = toolkit.get_action('package_search')(
            {'ignore_auth': True}, {'include_private': True, 'rows': 10000000}
        )
        if data['results']:
            for pkg in data['results']:
                if 'frequency' in pkg:
                    pkg['metadata_created'] = h.date_str_to_datetime(
                        pkg['metadata_created'])
                    pkg['metadata_modified'] = h.date_str_to_datetime(
                        pkg['metadata_modified'])
                    pkg['frequency'] = pkg.get('frequency', '')
                    if pkg['frequency']:
                        if pkg['frequency'] != 'irregular' and pkg['frequency'] != 'notPlanned':
                            if pkg['metadata_modified'].date() != pkg['metadata_created'].date():
                                now = dt.datetime.now()
                                diff = now - pkg['metadata_modified']
                                if diff > frequency_to_timedelta(pkg['frequency']):
                                    try:
                                        content = "Dataset " + pkg['title'] + " has not been updated in its planned update frequency (" + pkg['frequency'] + ")."
                                        to = pkg['contact_email']
                                        subject = "Open Data NI: Update dataset notification"
                                        emailer.send_email(content, to, subject)
                                        log.info('Package "' + pkg['title'] + '" has not been updated. Sending e-mail to maintainer.')
                                    except Exception as e:
                                        log.error(e)
        log.info('Daily dataset update frequency check completed.')
