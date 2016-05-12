import pytest
from icecake import cli
import jinja2
from templates import templates
from os.path import abspath, dirname, isdir, isfile, join


module_root = dirname(dirname(abspath(__file__)))
test_root = dirname(abspath(__file__))


class TestFunctions:
    def test_ls_relative(self):
        items = cli.ls_relative(join(test_root, 'fixtures', 'ls'))
        assert items == [
            'a.txt',
            'b.md',
            'c.html',
            'd/e.css'
        ]


class TestContentCache:
    def test_read(self):
        cache = cli.ContentCache(join(module_root, 'templates'))

        # Read from content
        helloworld = open(join(module_root, 'templates', 'content', 'articles', 'hello-world.md')).read()
        assert cache.read('content/articles/hello-world.md') == helloworld
        assert cache.get('content/articles/hello-world.md') == helloworld
        cache.set('content/articles/hello-world.md', 'b')
        assert cache.get('content/articles/hello-world.md') == 'b'

        # Read from layouts
        basic = open(join(module_root, 'templates', 'layouts', 'basic.html')).read()
        assert cache.read('layouts/basic.html') == basic

        # Read missing file
        assert cache.read('layouts/nope.html') is None

    def test_missing(self):
        cache = cli.ContentCache(join(module_root, 'templates'))
        assert cache.get('nope') is None

    def test_delete(self):
        cache = cli.ContentCache(join(module_root, 'templates'))
        cache.set('content/pie.md', 'delicious')
        assert cache.get('content/pie.md') == 'delicious'
        cache.delete('content/pie.md')
        assert cache.get('content/pie.md') is None

    def test_move(self):
        cache = cli.ContentCache(join(module_root, 'templates'))
        cache.set('content/pie.md', 'delicious')
        cache.move('content/pie.md', 'content/cake.md')
        assert cache.get('content/pie.md') is None
        assert cache.get('content/cake.md') == 'delicious'

        # Doesn't exist; no-op
        cache.move('nope', 'yep')
        assert cache.get('yep') is None

    def test_warm(self):
        cache = cli.ContentCache(join(module_root, 'templates'))
        cache.warm()
        basic = open(join(module_root, 'templates', 'layouts', 'basic.html')).read()
        assert cache.get('layouts/basic.html') == basic


class TestPage:
    def test_init(self):
        site = cli.Site('.')
        page = cli.Page("./content/this/file/does/not/exist.html", site)
        assert page.slug == "exist"
        assert page.folder == "this/file/does/not"
        assert page.ext == ".html"
        assert page.url == "/this/file/does/not/exist/"

    def test_parse_checker(self):
        site = cli.Site('.')
        with pytest.raises(RuntimeError):
            page = cli.Page("./content/this/file/does/not/exist.html", site)
            page.get_target()

    def test_parse_metadata(self):
        meta = """
title = Some title
date = 2013-01-02
tags = pie cake chocolate
slug = some-title
template = myfile.html
        """

        site = cli.Site('.')
        page = cli.Page("./content/this/file/does/not/exist.html", site)
        page.parse_metadata(meta)

        assert page.title == "Some title"
        assert page.date == "2013-01-02"
        assert page.tags == ['pie', 'cake', 'chocolate']
        assert page.slug == "some-title"
        assert page.template == "myfile.html"
        assert page.url == "/this/file/does/not/some-title/"

    def test_get_target(self):
        # Test basic case
        site = cli.Site('.')
        page = cli.Page("./content/this/file/does/not/exist.html", site)
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/exist/index.html"
        assert page.url == "/this/file/does/not/exist/"

        # Test not html / markdown case
        page = cli.Page("./content/this/file/does/not/exist.css", site)
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/exist.css"
        assert page.url == "/this/file/does/not/exist.css"

        # Test index case
        page = cli.Page("./content/this/file/does/not/index.md", site)
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/index.html"
        assert page.url == "/this/file/does/not/"

        # Test customized slug case
        meta = """
slug = some-title
        """
        page = cli.Page("./content/this/file/does/not/exist.md", site)
        page.parse_metadata(meta)
        assert page._get_folder() == "this/file/does/not"
        assert page.get_target() == "this/file/does/not/some-title/index.html"
        assert page.url == "/this/file/does/not/some-title/"

    def test_parse_string(self):
        raw = """
title = My Title
date = 2013-01-02
tags = pie
++++

This is the beginning of my page!
        """

        site = cli.Site('.')
        page = cli.Page.parse_string("this/file/does/not/exist.md", site, raw)
        assert page.body == "This is the beginning of my page!"

    def test_render(self):
        site = cli.Site(".")
        site.renderer = jinja2.Environment(loader=jinja2.DictLoader({
            "markdown.html": "MARKDOWN{{title}}{{content}}",
            "basic.html": "HTML{{content}}",
            "just.html": "Waka"
        }))

        page = cli.Page("filename.md", site)
        page.parse_metadata("title=My Title")
        page.body = "#This is awesome!"
        assert page.render() == "MARKDOWNMy Title<h1>This is awesome!</h1>"

        page.template = "basic.html"
        assert page.render() == "HTML<h1>This is awesome!</h1>"

        # This case is a bit odd. We don't actually use the page content we
        # parsed, we just let Jinja find the template on disk and render it
        # as-is. This is inconsistent from the markdown case, but works. There
        # may be some opportunity to clean up the API here and remove body or
        # content since only one is actually used.
        page = cli.Page("content/just.html", site)
        assert page.render() == "Waka"


class TestSite:
    def test_initialize(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        files = cli.ls_relative(site.root)
        # Verify all the things we expected are present
        for name in templates.keys():
            assert name in files
        # Verify we didn't find any extra stuff
        for file in files:
            assert templates[file] is not None

    def test_get_target(self):
        site = cli.Site(dirname(__file__))
        assert site.get_target('static/pie.css') == join(dirname(__file__), 'output/pie.css')

    def test_is_content(self):
        site = cli.Site(dirname(__file__))
        assert site.is_content('content/blah.html')
        assert not site.is_content('output/blah.html')

    def test_is_layout(self):
        site = cli.Site(dirname(__file__))
        assert site.is_layout('layouts/blah.html')
        assert not site.is_layout('output/blah.html')

    def test_is_static(self):
        site = cli.Site(dirname(__file__))
        assert site.is_static('static/blah.html')
        assert not site.is_static('output/blah.html')

    def test_copy_static(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        site.copy_static('css/main.css')
        target = join(site.root, 'output', 'css', 'main.css')
        assert isdir(join(site.root, 'output'))
        assert isdir(join(site.root, 'output', 'css'))
        assert isfile(target)

    def test_render(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        site.get_pages()
        page = site.pages(path='articles/hello-world.md')[0]
        output = page.render()
        assert output == open(join(test_root, 'fixtures', 'render', 'hello-world.md.html')).read()

    def test_build(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        assert isfile(join(site.root, 'content', 'articles.html'))

        site.build()
        output_files = cli.ls_relative(join(site.root, 'output'))

        # Make sure all the files are there
        assert output_files == [
            'articles/hello-world/index.html',
            'articles/index.html',
            'atom.xml',
            'css/main.css',
            'css/syntax.css',
            'index.html',
            'tags/index.html'
        ]

    def test_clean_output(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        files = cli.ls_relative(site.root)
        assert 'output/index.html' not in files

        site.build()
        files = cli.ls_relative(site.root)
        assert 'output/index.html' in files

        site.clean_output()
        files = cli.ls_relative(site.root)
        assert 'output/index.html' not in files


class TestUpdates:
    def test_list_dependents(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        items = site.list_dependents('markdown.html')
        assert items[0] == 'articles/hello-world.md'

        items = site.list_dependents('basic.html')
        items.sort()
        # We expect to find all of the content pages that need to be
        # re-rendered. We DO NOT expect to find markdown.html because
        # we are not going to render that page (it's a template) but
        # we DO expect to find articles/hello-world.md because markdown
        # is affected.
        assert items == [
            'articles.html',
            'articles/hello-world.md',
            'index.html',
            'tags.html',
        ]

    def test_render_dependents(self, tmpdir):
        site = cli.Site.initialize(tmpdir.strpath)
        site.render_dependents('markdown.html')
        files = cli.ls_relative(site.root)
        assert 'output/articles/hello-world/index.html' in files


class TestCLI:
    # TODO add tests for the CLI
    pass


class TestTemplates:
    """
    Verify that the templates in templates.py match the ones on disk
    """
    def test_templates(self):
        for f in cli.ls_relative(join(module_root, 'templates')):
            contents = open(join(module_root, 'templates', f)).read()
            assert templates[f] == contents
