from setuptools import setup

setup(
    name='beeworker',
    version='0.1',
    description='Beeworker component to Beekeeper',
    keywords='aws amazon parallel behat test beekeeper beeworker',
    url='https://github.com/jchin1968/beeworker',
    author='Joseph Chin',
    author_email='joe@beesuite.net',
    license='GPL2.0',
    packages=['beeworker'],
    install_requires=[
        'boto3',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        beeworker=beeworker.beeworker:work
    ''',
)
