import pytest
import icecake

class TestPage:
    def test_basic(self):
        page = icecake.Page("this/file/does/not/exist.html")
        assert page.slug == "exist"
        assert page.folder == "this/file/does/not"
        assert page.ext == ".html"

    def test_basic(self):
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

    def test_get_target(self):
        # Test basic case
        page = icecake.Page("this/file/does/not/exist.html")
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/exist/index.html"

        # Test html / markdown case
        page = icecake.Page("this/file/does/not/exist.css")
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/exist.css"

        # Test index case
        page = icecake.Page("this/file/does/not/index.md")
        page.parse_metadata("")
        assert page.get_target() == "this/file/does/not/index.html"

        # Test customized slug case
        meta = """
        slug = some-title
        """
        page = icecake.Page("this/file/does/not/exist.md")
        page.parse_metadata(meta)
        assert page._get_folder() == "this/file/does/not"
        assert page.get_target() == "this/file/does/not/some-title/index.html"
