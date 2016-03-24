import pytest
import icecake
import jinja2

class TestPage:
    def test_init(self):
        page = icecake.Page("this/file/does/not/exist.html")
        assert page.slug == "exist"
        assert page.folder == "this/file/does/not"
        assert page.ext == ".html"
        assert page.url == "/this/file/does/not/exist/"

    def test_parse_checker(self):
        with pytest.raises(RuntimeError):
            page = icecake.Page("this/file/does/not/exist.html")
            page.get_target()

    def test_parse_metadata(self):
        meta = """
title = Some title
date = 2013-01-02
tags = pie cake chocolate
slug = some-title
template = myfile.html
        """

        page = icecake.Page("this/file/does/not/exist.html")
        page.parse_metadata(meta)

        assert page.title == "Some title"
        assert page.date == "2013-01-02"
        assert page.tags == ['pie', 'cake', 'chocolate']
        assert page.slug == "some-title"
        assert page.template == "myfile.html"
        assert page.url == "/this/file/does/not/some-title/"

    def test_get_target(self):
        # Test basic case
        page = icecake.Page("this/file/does/not/exist.html")
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/exist/index.html"
        assert page.url == "/this/file/does/not/exist/"

        # Test not html / markdown case
        page = icecake.Page("this/file/does/not/exist.css")
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/exist.css"
        assert page.url == "/this/file/does/not/exist.css"

        # Test index case
        page = icecake.Page("this/file/does/not/index.md")
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/index.html"
        assert page.url == "/this/file/does/not/"

        # Test customized slug case
        meta = """
slug = some-title
        """
        page = icecake.Page("this/file/does/not/exist.md")
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

# This is the beginning of my page!
        """

        page = icecake.Page.parse_string("this/file/does/not/exist.md", raw)
        assert page.body == "# This is the beginning of my page!"

    def test_render(self):
        site = icecake.Site(".")
        site.renderer = jinja2.Environment(loader=jinja2.DictLoader({
            "markdown.html":"MARKDOWN{{title}}{{content}}",
            "basic.html":"HTML{{content}}",
            "just.html":"Waka"
            }))

        page = icecake.Page("filename.md")
        page.parse_metadata("title=My Title")
        page.body="#This is awesome!"
        assert page.render(site) == "MARKDOWNMy Title<h1>This is awesome!</h1>"

        page.template="basic.html"
        assert page.render(site) == "HTML<h1>This is awesome!</h1>"

        # This case is a bit odd. We don't actually use the page content we
        # parsed, we just let Jinja find the template on disk and render it
        # as-is. This is inconsistent from the markdown case, but works. There
        # may be some opportunity to clean up the API here and remove body or
        # content since only one is actually used.
        page = icecake.Page("just.html")
        assert page.render(site) == "Waka"
