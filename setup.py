from setuptools import setup, find_packages

setup(
    name='icecake',
    version='0.1',
    py_modules=['icecake'],
    install_requires=[
        'Click',
        'Jinja2',
        'Markdown',
        'Pygments',
        'python-dateutil',
        'Werkzeug',
    ],
    entry_points='''
        [console_scripts]
        icecake=icecake:cli
    '''
)