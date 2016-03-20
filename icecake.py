# -*- coding: utf8 -*-
"""
Icecake

This module provides a simple static site builder, similar to pelican or
octopress. It is intended to be small, light, and easy to modify. Out of the box
it supports the following features:

- Markdown formatting
- Pygments source code highlighting
- Jinja 2 templates
"""
# 2/3 compat
from __future__ import absolute_import, division, print_function, unicode_literals
__metaclass__ = type

import argparse
import platform
import logging
import os
# 2/3 compat
if platform.python_version_tuple()[0] == '2':
    import ConfigParser as configparser
    import io
else:
    import configparser


import click
import jinja2
import markdown
from dateutil.parser import parse as dateparse
from werkzeug.contrib.atom import AtomFeed


logging.basicConfig(level=logging.INFO)


class Page:
    """
    A page is any discrete piece of content that will appear in your output
    folder. At minimum a page should have a body, title, and slug so it can be
    rendered. However, a page may have additional metadata like date or tags.
    """
    metadata = ["tags", "date", "title", "slug", "template"]
    metadelimiter = "++++"

    def __init__(self, filepath):
        # These are set when the page is initialized (step 1)
        self.filepath = os.path.normpath(filepath)  # This is the path of the file relative to content
        self.folder = self._get_folder()  # This is the leading part of the URL
        self.slug = self._get_default_slug()      # This is the final part of the URL
        self.ext = self._get_extension()  # This is the extension (markdown or html)

        # These maybe set when the page is parsed for metadata (step 2)
        self.date = None     # This is the date the page was published
        self.tags = None     # This is a list of tags, used to build links
        self.template = None # This is the template we'll use to render the page
        self.title = None    # This is the title of the page

        # These are always set when the page is parsed for metadata (step 2)
        self.parsed = False
        self.url = None      # This is the full, final URL path

        # These are set when the page is rendered (step 3)
        self.body = None      # This is the raw body of the page
        self.content = None   # This is the content string for markdown pages
        self.rendered = None  # This is the HTML content of the page

    def _get_folder(self):
        return os.path.dirname(self.filepath)

    def _get_default_slug(self):
        """
        Get the slug for this page, which is used for the final part of the URL
        path. For a file like cakes/chocolate.html this will be "chocolate". If
        the slug is "index" we special case to "" so index.md and index.html can
        be used as you would expect without going into a folder called "index".
        If you want a folder called "index" you can specify the slug manually.
        """
        slug = os.path.splitext(os.path.basename(self.filepath))[0]
        if slug == "index":
            slug = ""
        return slug

    def _get_extension(self):
        """
        This is the file's extention, which is primarily used to identify
        markdown files.
        """
        return os.path.splitext(self.filepath)[1]

    def _get_url(self):
        """
        Get the url for this page, based on its filepath. This is path + slug.
        Something like cakes/chocolate.html will become /cakes/chocolate/
        """
        return '/%s/' % (self.folder + self.slug)

    def get_target(self):
        """
        Get the target filename for this page. This is the containing folder +
        slug, which may have been customized.
        """
        # Note that we may have customized slug so we should only run this after
        # metadata has been parsed.
        if not self.parsed:
            raise RuntimeError("This should not be called before metadata is parsed")
        output_filename = os.path.normpath(os.path.join(self.folder, self.slug + self.ext))
        if self.ext in [".html", ".md", ".markdown"]:
            output_filename = os.path.normpath(os.path.join(self.folder, self.slug, "index.html"))
        return output_filename

    def render(self, site):
        """
        Render the page. All files will be rendered using Jinja. Markdown files
        with .md or .markdown extension will also use the markdown renderer. By
        default the base template is markdown.html for markdown and basic.html
        for everything else. Customize this via the "template" metadata field.
        """
        if self.ext in [".md", ".markdown"]:
            self.content = markdown.markdown(self.body, extensions=site.markdown_plugins)
            if self.template is not None:
                template = site.renderer.get_template(self.template)
            else:
                template = site.renderer.get_template("markdown.html")
        else:
            template = site.renderer.get_template(self.filepath)

        self.rendered = template.render(self.__dict__, site=site)
        return self.rendered

    def parse_metadata(self, text):
        """
        Parse a metadata string into object properties tags, date, title, etc.
        """
        logging.debug("Parsing metadata %s", text)
        text = "[Metadata]\n" + text
        parser = configparser.ConfigParser()
        if platform.python_version_tuple()[0] == '2':
            parser.readfp(io.StringIO(text))
        else:
            parser.read_string(text)

        # This is super ugly because of 2/3 compat
        values = {}
        for k, v in parser.items("Metadata"):
            values[k] = v
        for key in self.metadata:
            value = None
            if key in values:
                value = values[key]
            if key == "tags":
                if value is not None:
                    value = value.split(" ")
                else:
                    value = []
            # If we have a default metadata value and the user did not override
            # it, leave it alone
            if value is None and getattr(self, key, None) is not None:
                continue
            setattr(self, key, value)
            if value == None:
                logging.warning("Metadata '%s' not specified in %s", key,
                                self.filepath)
        self.parsed = True

    @classmethod
    def parse_string(cls, filepath, text):
        """
        Parse a raw string and separate the front matter so we can turn it into
        a page object with metadata and body.
        """
        page = cls(filepath)
        parts = text.split(cls.metadelimiter, 1)

        if len(parts) == 2:
            page.parse_metadata(parts[0])
            page.body = parts[1].strip()
        else:
            page.body = parts[0].strip()
            logging.warning("No metadata detected; expected %s separator %s",
                            cls.metadelimiter, page.filepath)
            # Say we already parsed the metadata
            page.parsed=True
        return page

    @classmethod
    def parse_file(cls, filepath):
        """
        Read a file and return the Page created by passing it into parse_string
        """
        text = open(filepath).read()
        page = cls.parse_string(filepath, text)

        return page


class Site:
    """
    A site represents a collection of source files arranged under the following
    project structure:

    ├── content
    ├── layouts
    ├── static
    └── output

    Content represent pages on your site. Each page will be built into a
    corresponding file in your output directory. Layout files are used for
    shared templates but do not have a corresponding page in output. Files under
    static are copied directly, and is a good place to put images, css, and
    javascript.

    Methods on this class deal with configuration, discovering content and
    building your site.
    """

    def __init__(self, root=None):
        """
        Keyword Arguments:
        root -- The path to the static site folder which includes the pages,
                layouts, and static folders.
        """
        self.root = root
        self.markdown_plugins = ["markdown.extensions.fenced_code", "markdown.extensions.codehilite"]
        self.renderer = jinja2.Environment(loader=jinja2.FileSystemLoader([os.path.abspath("content"), os.path.abspath("layouts")]))
        self.pagedata = []

    def getpages(self):
        """
        Enumerate and parse all the page files in the static site.
        """
        logging.debug("Getting pages")
        content_dir = os.path.join(self.root, "content")
        curdir = os.getcwd()
        os.chdir(content_dir)
        files = self.list_files(".")
        for file in files:
            if not os.path.isdir(file):
                logging.debug("Parsing %s", file)
                page = Page.parse_file(file)
                page.render(self)
                self.pagedata.append(page)
        os.chdir(curdir)
        return self.pagedata

    def copystatic(self):
        logging.debug("Copying static files")
        static_dir = os.path.abspath(os.path.join(self.root, "static"))
        entries = os.walk(static_dir)
        for path, dirs, files in entries:
            for file in files:
                source_path = os.path.join(path, file)
                source_file = "." + source_path.replace(static_dir, "")
                output_file = os.path.normpath(os.path.join(self.root, "output", source_file))
                if os.path.isdir(source_path):
                    continue
                logging.debug("Copying static file %s", output_file)
                output_path = os.path.normpath(os.path.dirname(output_file))

                if not os.path.exists(output_path):
                    logging.debug("Making directory %s", output_path)
                    os.makedirs(output_path, mode=0o755)
                contents = open(source_path, "rb").read()
                open(output_file, "wb").write(contents)

    def build(self):
        """
        Build the site. This method originates all of the calls to discover,
        render, and place pages in the output directory. If you want to
        customize how your site is built, this is a good place to start.
        """
        template_path = os.path.join(self.root, "layouts")
        logging.debug("Loading templates from %s", template_path)
        templates = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_path))

        self.pagedata = self.getpages()
        for page in self.pagedata:
            output_filename = os.path.join("output", page.get_target())
            logging.debug("Preparing to write %s", output_filename)
            output_path = os.path.dirname(output_filename)
            if not os.path.exists(output_path):
                logging.debug("Making directory %s", output_path)
                os.makedirs(output_path, mode=0o755)

            open(output_filename, mode="w").write(page.render(self))
            logging.info("Wrote \"%s\" (%s)", page.title, page.filepath)

        self.copystatic()

    def tags(self):
        tagnames = set()
        for page in self.pagedata:
            if page.tags:
                tagnames = tagnames.union(set(page.tags))
        taglist = list(tagnames)
        taglist.sort()
        return taglist

    def pages(self, path=None, tag=None, limit=None, order=None):
        """
        Filter the pages on your site by path or tag, and (optionally) sort or
        limit the number of results. Path pages uses startswith. Tag pages
        uses exact match. Use -ORDER for reverse sort. Examples:

        finder.pages(path="articles", limit=5, order="-date")
        finder.pages(tag="family", order="title")
        """
        items = self.pagedata
        if path is not None:
            items = [page for page in items if page.filepath.startswith(path)]
        if tag is not None:
            items = [page for page in items if tag in page.tags]
        if order is not None:
            rev = False
            if order[0] == "-":
                rev = True
                order = order[1:]
            items.sort(key=lambda x: getattr(x, order), reverse=rev)
        if limit is not None and limit > 0:
            items = items[:limit]
        return items

    def atom(self, *args, **kwargs):
        items = self.pages(*args, **kwargs)

        atom = AtomFeed(title="Chris Bednarski", feed_url="https://cbednarski.com/atom.xml",
                    url="https://cbednarski.com/",
                    subtitle="Chris Bednarski")
        for item in items:
            item.render(Site("."))
            atom.add(title=item.title,
                     content=item.content,
                     content_type='html',
                     author="Chris Bednarski",
                     url="https://cbednarski.com"+item.url,
                     published=dateparse(item.date),
                     updated=dateparse(item.date),
                     xml_base=None)
        return atom.to_string()


    @classmethod
    def list_files(cls, list_path):
        found = []
        for path, dirs, files in os.walk(list_path):
            for file in files:
                found.append(os.path.join(path, file))
        return found


@click.group()
def cli():
    pass


@cli.command()
@click.option("--debug/--no-debug", default=False)
def init(debug):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


@cli.command()
@click.option("--debug/--no-debug", default=False)
def build(debug):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    Site(os.path.abspath(os.getcwd())).build()


@cli.command()
@click.option("--debug/--no-debug", default=False)
def preview(debug):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)


if __name__ == "__main__":
    cli()