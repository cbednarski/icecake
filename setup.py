from setuptools import setup

setup(
    name="icecake",
    version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Jinja2',
        'Markdown',
        'Pygments',
        'python-dateutil',
        'Werkzeug',
    ],
    entry_points="""
        [console_scripts]
        icecake=icecake:cli
    """
)