from setuptools import setup, find_packages

setup(
    # packaging information that is likely to be updated between versions
    name='icecake',
    version='0.6.0',
    packages=['icecake'],
    py_modules=['cli', 'templates', 'livejs'],
    entry_points='''
        [console_scripts]
        icecake=icecake.cli:cli
    ''',
    install_requires=[
        'Click',
        'Jinja2',
        'Markdown',
        'Pygments',
        'python-dateutil',
        'watchdog',
        'Werkzeug',
    ],

    # pypy stuff that is not likely to change between versions
    url="https://github.com/cbednarski/icecake",
    author="Chris Bednarski",
    author_email="banzaimonkey@gmail.com",
    description="An easy and cool static site generator",
    license="MIT",
    long_description=open('README.rst').read(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
    ],
    keywords="static site generator builder icecake"
)
