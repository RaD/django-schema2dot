# -*- coding: utf-8 -*-
# (c) 2010 Ruslan Popov <ruslan.popov@gmail.com>

# Implementation of the export database schema to .dot format for manage.py.

from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import connections, DEFAULT_DB_ALIAS
from django.utils.importlib import import_module


digraph = """
digraph G {
graph [rankdir = "TB", ratio=auto, ranksep=0.2, nodesep=0.5];
node [shape="plaintext", color="black", fontname="Verdana", fontsize="8"];
edge [arrowsize="1", color="red", fontname="Verdana", fontsize="8"];
%(content)s
}
"""

def dot_cluster(model_name, field_list):
    cluster = """
    subgraph cluster_%(model_name)s {label="%(model_name)s"; labelloc="t";
    fontname="Verdana"; fontsize="12"; %(model_name)s};
    %(model_name)s [shape="record", label="{%(field_list)s}"];
    """

    columns = []
    map(lambda x:
        columns.append('<%(column_name)s> %(column_name)s %(data_type)s (%(data_length)s)' % x),
        field_list)

    return cluster % {'model_name': model_name,
                      'field_list': '|'.join(columns)}

class Command(NoArgsCommand):
    help = 'Creates the database schema diagram in .dot format. Use before syncdb command.'

    def handle_noargs(self, **options):

        for app_name in settings.INSTALLED_APPS:
            print 'importing %s' % app_name,
            try:
                import_module('.models', app_name)
                print 'ok'
            except ImportError, e:
                print 'failed'

        connection = connections[DEFAULT_DB_ALIAS]
        cursor = connection.cursor()

        tables = connection.introspection.table_names()
        models = connection.introspection.installed_models(tables)

        dot = []
        cluster_list = []
        fk_list = []
        for model in list(models):
            model_name = model._meta.object_name
            field_list = []
            for field in model._meta.fields:
                field_name = field.name
                field_list.append({'column_name': field_name,
                                   'data_type': field.get_internal_type(),
                                   'data_length': field.max_length or ''})
                if field.rel:
                    rel_model = field.rel.to._meta.object_name
                    rel_field = field.rel.field_name
                    fk_list.append('%(model_name)s:%(field_name)s -> %(rel_model)s:%(rel_field)s;' % locals())
            cluster_list.append(dot_cluster(model_name, field_list))

        cursor.close()
        connection.close()

        map(lambda x: dot.append(x), cluster_list)
        map(lambda x: dot.append(x), fk_list)

        f = open('schema.dot', 'w')
        f.writelines(digraph % {'content': '\n'.join(dot)})
        f.close()

        print 'Usage:'
        print '  dot -Tsvg schema.dot > schema.dot.svg'
        print ' or'
        print '  fdp -Tsvg schema.dot > schema.dot.svg'
