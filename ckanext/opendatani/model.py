from ckan.model.domain_object import DomainObject
from ckan.model.meta import  metadata, mapper, Session, engine
from sqlalchemy import Table, Column, Index, types
from ckan.model.types import make_uuid
from sqlalchemy.engine.reflection import Inspector

sftp_logs_table = None

def setup():
    if sftp_logs_table is None:
        define_sftp_logs_table()
    if not sftp_logs_table.exists():
        sftp_logs_table.create()

    inspector = Inspector.from_engine(engine)

    index_names = \
        [index['name'] for index in
         inspector.get_indexes('ckanext_sftp_logs')]

    if 'ckanext_sftp_logs_id_idx' not in index_names:
        Index('ckanext_sftp_logs_id_idx',
              sftp_logs_table.c.id).create()


class CkanextSFTPLogs(DomainObject):
    @classmethod
    def get(self, **kwds):
        '''Finds a single entity in the table.
        '''

        query = Session.query(self).autoflush(False)
        query = query.filter_by(**kwds).first()
        return query

    @classmethod
    def search(self, **kwds):
        '''Finds entities in the table that satisfy certain criteria.
        :param order: Order rows by specified column.
        :type order: string
        '''

        query = Session.query(self).autoflush(False)
        query = query.filter_by(**kwds)

        return query.all()


def define_sftp_logs_table():
    global sftp_logs_table

    sftp_logs_table = Table('ckanext_sftp_logs', metadata,
                            Column('id', types.UnicodeText,
                                   primary_key=True,
                                   default=make_uuid),
                            Column('message',
                                   types.UnicodeText,
                                   nullable=False),
                            Index('ckanext_sftp_logs_id_idx',
                                  'id'))

    mapper(
        CkanextSFTPLogs,
        sftp_logs_table
    )