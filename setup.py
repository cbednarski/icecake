from setuptools import setup, find_packages

setup(
    name='icecake',
    version='0.1.0',
    py_modules=['icecake'],
    url="https://github.com/cbednarski/icecake",
    author="Chris Bednarski",
    author_email="banzaimonkey@gmail.com",
    description="An easy and cool static site generator",
    license="MIT",
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
    ''',
    package_data={'': ['templates/*']},
    keywords="static site generator builder icecake"
)