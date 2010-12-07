from distutils.core import setup

setup(name='schema2dot',
      version='0.2',
      description='Django application that can export project's database schema into .dot format of Graphviz.',
      author='Ruslan Popov',
      author_email='ruslan.popov@gmail.com',
      url='http://github.com/RaD/django-schema2dot/tree/master',
      packages=['schema2dot',],
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Web Environment',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: BSD License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Utilities'],
      )
