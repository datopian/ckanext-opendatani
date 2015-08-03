from ckan.common import OrderedDict
from pylons import config
from ckan.plugins import toolkit
import ckanapi


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
      create_default_groups             - create default groups
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
