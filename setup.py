import sys
from distutils.core import setup

setup(
      name='pysos',
      version='2.0.0',
      description='Parse a sosreport for specific information',
      long_description=('Pysos is a tool to parse through a sosreport and'
                        'report back desired information in a structured'
                        ' and human-readable fashion in order to make '
                        'troubleshooting easier and faster.'),
      author='Jake Hunsaker',
      author_email='jhunsaker@redhat.com',
      maintainer='Jake Hunsaker',
      maintainer_email='jhunsaker@redhat.com',
      license='GPL',
      url='https://github.com/TurboTurtle/pysos',
      packages=['pysosutils', 'pysosutils/plugins', 'pysosutils/utilities',
                'pysosutils/sostests'
                ],
      scripts=['pysos'],
     )
