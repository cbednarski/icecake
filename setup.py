from setuptools import setup

setup(
    name='icecake',
    version='0.4.0',
    py_modules=['icecake', 'templates'],
    url="https://github.com/cbednarski/icecake",
    author="Chris Bednarski",
    author_email="banzaimonkey@gmail.com",
    description="An easy and cool static site generator",
    license="MIT",
    long_description=open('README.rst').read(),
    install_requires=[
        'Click',
        'Jinja2',
        'Markdown',
        'Pygments',
        'python-dateutil',
        'watchdog',
        'Werkzeug',
    ],
    entry_points='''
        [console_scripts]
        icecake=icecake:cli
    ''',
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
