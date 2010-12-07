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
        mm_list = []

        for model in list(models):
            model_name = '%s_%s' % (model._meta.app_label, model._meta.object_name)
            field_list = []

            for field in model._meta.fields:
                field_name = field.name
                field_list.append({'column_name': field_name,
                                   'data_type': field.get_internal_type(),
                                   'data_length': field.max_length or ''})
                if field.rel:
                    rel_model = '%s_%s' % (field.rel.to._meta.app_label, field.rel.to._meta.object_name)
                    rel_field = field.rel.field_name
                    fk_list.append('%(model_name)s:%(field_name)s -> %(rel_model)s:%(rel_field)s;' % locals())

            for m2m in model._meta.get_m2m_with_model():
                mo, unknown = m2m

                field_name = mo.name
                # print
                # print dir(mo.rel)
                # print model_name, mo.rel.get_related_field().name
                # print
                rel_model = '%s_%s' % (mo.related.model._meta.app_label, mo.rel.to._meta.object_name)
                rel_field = mo.rel.get_related_field().name

                field_list.append({'column_name': field_name,
                                   'data_type': 'ManyToMany',
                                   'data_length': ''})

                mm_list.append('%(model_name)s:%(field_name)s -> %(rel_model)s:%(rel_field)s[color=blue, dir=both];' % locals())

            cluster_list.append(dot_cluster(model_name, field_list))

        cursor.close()
        connection.close()

        dot.append('\n# clusters definition\n')
        map(lambda x: dot.append(x), cluster_list)
        dot.append('\n# foreign keys definition\n')
        map(lambda x: dot.append(x), fk_list)
        dot.append('\n# manytomany keys definition\n')
        map(lambda x: dot.append(x), mm_list)

        f = open('schema.dot', 'w')
        f.writelines(digraph % {'content': '\n'.join(dot)})
        f.close()

        print 'Usage:'
        print '  dot -Tsvg schema.dot > schema.dot.svg'
        print ' or'
        print '  fdp -Tsvg schema.dot > schema.fdp.svg'
