# -*- coding: utf8 -*-
"""
Icecake

This module provides a simple static site builder, similar to pelican or
octopress. It is intended to be small, light, and easy to modify. Out of the box
it sports the following features:

- Markdown formatting
- Pygments source code highlighting
- Jinja templates
- Automatically rebuilds when you edit things
"""
from __future__ import absolute_import, division, print_function, unicode_literals
import platform
import logging
import os
from os.path import abspath, basename, dirname, exists, isdir, isfile, join, normpath, relpath, splitext
from multiprocessing import Process
import time
import shutil


import click
import jinja2
import jinja2.meta
import markdown
from dateutil.parser import parse as dateparse
from werkzeug.contrib.atom import AtomFeed
import watchdog.observers
import watchdog.events


from .templates import templates
from .livejs import livejs
if platform.python_version_tuple()[0] == '2':
    import ConfigParser as configparser
    import io
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from SocketServer import TCPServer
else:
    import configparser
    from http.server import SimpleHTTPRequestHandler
    from socketserver import TCPServer


__metaclass__ = type
logging.basicConfig(level=logging.ERROR)
click.disable_unicode_literals_warning = True
curdir = abspath(os.getcwd())


def ui(*args, **kwargs):
    pass


def ls_relative(list_path):
    """
    List files relative to the specified path
    """
    found = []
    # Guard against dir doesn't exist
    if not isdir(list_path):
        return found
    for path, dirs, files in os.walk(list_path):
        for file in files:
            filepath = join(path, file)
            found.append(relpath(filepath, list_path))
    found.sort()  # Make sure the sort order is deterministic
    return found


class ContentCache:
    def __init__(self, root):
        self.root = root
        self.files = {}
        self.pages = {}
        self.templates = {}
        self.rebuild_index = {}

    def peek(self, filename):
        """
        peek when you want to get fresh data from disk but NOT store it in the cache
        """
        file = join(self.root, filename)
        if isfile(file):
            content = open(file).read()
            return content
        return None

    def read(self, filename):
        """
        read when you want to get fresh data from disk and store it in the cache
        """
        content = self.peek(filename)
        if content is not None:
            self.set(filename, content)
        return content

    def set(self, filename, content):
        if filename.startswith('content'):
            # Markdown files are not templates so let's skip those
            if splitext(filename)[1] != '.md':
                self.templates[relpath(filename, 'content')] = content
        if filename.startswith('layouts'):
            self.templates[relpath(filename, 'layouts')] = content
        self.files[filename] = content

    def get(self, filename):
        if filename in self.files:
            return self.files[filename]
        return None

    def delete(self, filename):
        del(self.files[filename])

    def move(self, old, new):
        if old not in self.files:
            return
        self.set(new, self.get(old))
        self.delete(old)

    def warm(self):
        for path in ['content', 'layouts']:
            for file in ls_relative(join(self.root, path)):
                self.read(join(path, file))


class Page:
    """
    A page is any discrete piece of content that will appear in your output
    folder. At minimum a page should have a body, title, and slug so it can be
    rendered. However, a page may have additional metadata like date or tags.
    """
    metadata = ["tags", "date", "title", "slug", "template"]
    required = ["date", "title"]
    metadelimiter = "++++"

    def __init__(self, filepath, site):
        # These are set when the page is initialized (step 1)
        self.parsed = False  # This is a special flag that helps us avoid bugs
        self.site = site
        self.abspath = abspath(filepath)
        # This is the path of the file relative to content
        self.filepath = relpath(filepath, join(site.root, 'content'))
        self.folder = self._get_folder()      # This is the leading part of the URL
        self.slug = self._get_default_slug()  # This is the final part of the URL
        self.ext = self._get_extension()      # This is the extension (markdown or html)

        # Note! We are going to evaluate this now to make sure it is always
        # evaluated. However, we will evaluate this again after the metadata is
        # parsed in case the user specifies a custom slug, which will change the
        # url. This way, though, we always have url defined even for pages
        # without metadata.
        self.url = self._get_url()           # This is the URL path

        # These maybe set when the page is parsed for metadata (step 2)
        self.date = None      # This is the date the page was published
        self.tags = None      # This is a list of tags, used to build links
        self.template = None  # This is the template we'll use to render the page
        self.title = None     # This is the title of the page

        # These are set when the page is rendered (step 3)
        self.body = None      # This is the raw body of the page
        self.content = None   # This is the content string for markdown pages
        self.rendered = None  # This is the HTML content of the page

    def _get_folder(self):
        return dirname(self.filepath)

    def _get_default_slug(self):
        """
        Get the slug for this page, which is used for the final part of the URL
        path. For a file like cakes/chocolate.html this will be "chocolate". If
        the slug is "index" we special case to "" so index.md and index.html can
        be used as you would expect without going into a folder called "index".
        If you want a folder called "index" you can specify the slug manually.
        """
        slug = splitext(basename(self.filepath))[0]
        if slug == "index":
            slug = ""
        return slug

    def _get_extension(self):
        """
        This is the file's extention, which is primarily used to identify
        markdown files.
        """
        return splitext(self.filepath)[1]

    def _get_url(self):
        """
        Get the url for this page, based on its filepath. This is path + slug.
        Something like cakes/chocolate.html will become /cakes/chocolate/
        """
        if self.ext in [".html", ".md", ".markdown"]:
            return '/%s/' % normpath(join(self.folder, self.slug))
        return '/%s' % join(self.folder, self.slug + self.ext)

    def get_target(self):
        """
        Get the target filename for this page. This is the containing folder +
        slug, which may have been customized.
        """
        # Note that we may have customized slug so we should only run this after
        # metadata has been parsed.
        if not self.parsed:
            raise RuntimeError("This should not be called before metadata is parsed")
        # If we find a .html or .md we will use .html instead, and will convert
        # the name to a folder containing index.html so we get a clean URL.
        if self.ext in [".html", ".md", ".markdown"]:
            return normpath(join(self.folder, self.slug, "index.html"))
        # We default to path/name.extension in case there is a file like CSS or
        # XML where the filename is important.
        return normpath(join(self.folder, self.slug + self.ext))

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

        # This is super ugly because of 2/3 compat. There's probably a cleaner
        # way to factor this code.
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
            # it, leave it alone. Currently this only applies to slug, which has
            # a default based on the filepath.
            if value is None and getattr(self, key, None) is not None:
                continue
            setattr(self, key, value)
            if value is None and key in self.required:
                logging.warning("Metadata '%s' not specified in %s", key,
                                self.filepath)
        self.url = self._get_url()
        self.parsed = True

    def render(self):
        """
        Render the page. All files will be rendered using Jinja. Markdown files
        with .md or .markdown extension will also use the markdown renderer. By
        default the base template is markdown.html for markdown and basic.html
        for everything else. Customize this via the "template" metadata field.
        """
        logging.debug("Rendering %s" % self.filepath)
        if self.ext in [".md", ".markdown"]:
            self.content = markdown.markdown(self.body,
                                             extensions=self.site.markdown_plugins,
                                             extension_configs=self.site.markdown_options)
            if self.template is not None:
                template = self.site.renderer.get_template(self.template)
            else:
                template = self.site.renderer.get_template("markdown.html")
        else:
            template = self.site.renderer.get_template(self.filepath)
        # Inject livejs code (optional)
        if self.site.preview_mode:
            livejs_code = "<script>"+livejs+"</script>"
        else:
            livejs_code = ""
        self.rendered = template.render(self.__dict__, site=self.site, livejs=livejs_code)
        return self.rendered

    def render_to_disk(self):
        output = self.render()
        target = join(self.site.root, 'output', self.get_target())
        logging.debug('Writing to %s' % target)
        ui('Generating %s' % target)
        target_dir = dirname(target)
        if not isdir(target_dir):
            os.makedirs(target_dir)
        file = open(target, mode='w')
        file.write(output)
        file.close()

    @classmethod
    def parse_string(cls, filepath, site, text):
        """
        Parse a raw string and separate the front matter so we can turn it into
        a page object with metadata and body.
        """
        page = cls(filepath, site)
        parts = text.split(cls.metadelimiter, 1)

        if len(parts) == 2:
            page.parse_metadata(parts[0].strip())
            page.body = parts[1].strip()
        else:
            page.body = parts[0].strip()
            if page.ext in ['.md', '.markdown']:
                logging.warning("No metadata detected; expected %s separator %s",
                                cls.metadelimiter, page.filepath)
            # Say we already parsed the metadata
            page.parsed = True
        return page

    @classmethod
    def parse_file(cls, filepath, site):
        """
        Read a file and return the Page created by passing it into parse_string
        """
        content = open(filepath).read()
        page = cls.parse_string(filepath, site, content)
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

    def __init__(self, root, preview_mode=False):
        """
        Keyword Arguments:
        root -- The path to the static site folder which includes the pages,
                layouts, and static folders.
        """
        self.preview_mode = preview_mode
        self.root = abspath(root)
        self.cache = ContentCache(root)
        self.cache.warm()
        self.markdown_plugins = ["markdown.extensions.fenced_code", "markdown.extensions.codehilite"]
        self.markdown_options = {
            "codehilite": {
                "linenums": False,
                "guess_lang": False,
            }
        }
        self.renderer = jinja2.Environment(loader=jinja2.DictLoader(self.cache.templates))
        self.pagedata = {}
        self.get_pages()

    def get_target(self, path):
        """Convert a path from static to output"""
        path = self.relpath(path)
        if path.startswith('static'):
            return join(self.root, 'output', relpath(path, 'static'))
        raise ValueError('Invalid path %s; expected a path under static')

    def relpath(self, path):
        """Get path relative to the site root"""
        return relpath(join(self.root, getattr(path, 'src_path', path)), self.root)

    def is_content(self, path):
        return self.relpath(path).startswith('content')

    def is_layout(self, path):
        return self.relpath(path).startswith('layouts')

    def is_static(self, path):
        return self.relpath(path).startswith('static')

    def copy_static(self, path):
        source = join(self.root, 'static', path)
        target = self.get_target(source)
        target_dir = dirname(target)
        if not isdir(target_dir):
            logging.debug('Creating directory %s' % target_dir)
            os.makedirs(target_dir, mode=0o755)
        logging.debug('Copying static file to %s' % target)
        shutil.copy(source, target)

    def copy_all_static(self):
        logging.debug('Copying static files')
        static_dir = join(self.root, 'static')
        sources = ls_relative(static_dir)
        for source in sources:
            if isfile(join(self.root, 'static', source)):
                self.copy_static(source)

    def get_pages(self):
        """
        Enumerate and parse all the page files in the static site.
        """
        logging.debug("Getting pages")
        pages = {}
        for file in self.cache.files:
            if not file.startswith('content'):
                continue
            source_file = join(self.root, file)
            if isfile(source_file):
                logging.debug("Parsing %s", source_file)
                page = Page.parse_file(source_file, self)
                page.render()
                pages[page.filepath] = page
        self.pagedata = pages
        return self.pagedata

    def list_dependents(self, filepath):
        depset = set()
        # If the page is markdown.html then we need to add all of the markdown
        # pages.
        # TODO add support for markdown pages that specify a custom template
        if filepath == 'markdown.html':
            for _, page in self.pagedata.items():
                if page.ext in ['.md', '.markdown']:
                    depset.add(page.filepath)
        else:
            for path, body in self.cache.templates.items():
                ast = self.renderer.parse(body)
                pagedeps = jinja2.meta.find_referenced_templates(ast)
                if filepath in pagedeps:
                    for item in self.list_dependents(path):
                        depset.add(item)
            for _, page in self.pagedata.items():
                ast = self.renderer.parse(page.body)
                pagedeps = jinja2.meta.find_referenced_templates(ast)
                if filepath in list(pagedeps):
                    depset.add(page.filepath)
                    for item in self.list_dependents(page.filepath):
                        depset.add(item)
        deplist = list(depset)
        deplist.sort()
        return deplist

    def render_dependents(self, filepath):
        for item in self.list_dependents(filepath):
            self.pagedata[item].render_to_disk()

    def build(self):
        """
        Build the site. This method originates all of the calls to discover,
        render, and place pages in the output directory. If you want to
        customize how your site is built, this is a good place to start.
        """
        self.clean_output()
        self.pagedata = self.get_pages()
        for _, page in self.pagedata.items():
            page.render_to_disk()
        self.copy_all_static()

    def tags(self):
        tagnames = set()
        for path, page in self.pagedata.items():
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
        items = self.pagedata.values()
        for page in items:
            logging.debug(page.filepath)
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

    def atom(self, feed_title, feed_url, feed_subtitle, site_url, author, *args, **kwargs):
        items = self.pages(*args, **kwargs)

        atom = AtomFeed(title=feed_title,
                        subtitle=feed_subtitle,
                        feed_url=feed_url,
                        url=site_url)
        for item in items:
            item.render()
            atom.add(title=item.title,
                     content=item.content,
                     content_type='html',
                     author=author,
                     url=site_url+item.url,
                     published=dateparse(item.date),
                     updated=dateparse(item.date),
                     xml_base=None)
        return atom.to_string()

    def clean_output(self):
        """
        Delete everything in the output folder so we can perform a clean build
        """
        output_dir = join(self.root, 'output')
        if isdir(output_dir):
            shutil.rmtree(output_dir)

    @classmethod
    def initialize(cls, root):
        if not isdir(root):
            os.makedirs(root)
        for path, contents in templates.items():
            target = join(root, path)
            target_dir = dirname(target)
            if not isdir(target_dir):
                os.makedirs(target_dir)

            with open(target, mode="w") as f:
                logging.debug("Writing %s" % target)
                f.write(contents)
                f.close()
        return Site(root)


class Handler(watchdog.events.FileSystemEventHandler):
    site = None

    def is_watched(self, event):
        """
        Whether we are watching this path at all. This guards against
        triggering logic on the output folder or other folders the user may
        have created here.
        """
        return self.site.is_content(event) or self.site.is_layout(event) or self.site.is_static(event)

    def on_created(self, event):
        if isfile(event.src_path):
            if self.site.is_content(event):
                data = self.site.cache.read(event.src_path)
                page = Page.parse_string(event.src_path, self.site, data)
                page.render_to_disk()
            elif self.site.is_static(event):
                self.site.copy_static(event.src_path)

    def on_deleted(self, event):
        if self.is_watched(event.src_path):
            logging.debug('Deletion detected for %s', event.src_path)
            shutil.rmtree(event.src_path)

    def on_modified(self, event):
        if isfile(event.src_path) and self.is_watched(event):
            path = self.site.relpath(event.src_path)
            logging.debug('Change detected for %s', event.src_path)
            if self.site.is_content(event):
                if self.site.cache.get(path) != self.site.cache.read(path):
                    data = self.site.cache.get(path)
                    page = Page.parse_string(path, self.site, data)
                    page.render_to_disk()
                    self.site.render_dependents(relpath(self.site.relpath(event.src_path), 'content'))
            elif self.site.is_static(event):
                self.site.copy_static(event.src_path)
            elif self.site.is_layout(event):
                if self.site.cache.get(path) != self.site.cache.read(path):
                    self.site.render_dependents(relpath(self.site.relpath(event.src_path), 'layouts'))

    def on_moved(self, event):
        if isfile(event.dest_path) and self.is_watched(event):
            self.on_deleted(event)
            # This is a hack and probably has some bad consequence I'm not
            # thinking about right now.
            event.src_path = event.dest_path
            self.on_created(event)


class Watcher:
    def __init__(self, site):
        self.site = site
        Handler.site = site

    def watch(self):
        obs = watchdog.observers.Observer()
        obs.schedule(Handler(), join(self.site.root), recursive=True)
        logging.debug('Watching for changes in %s' % self.site.root)
        ui('Watching for changes in %s' % self.site.root)
        obs.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            obs.stop()
        obs.join()


class HTTPHandler(SimpleHTTPRequestHandler):
    site = None

    def translate_path(self, path):
        if platform.python_version_tuple()[0] == '2':
            path = SimpleHTTPRequestHandler.translate_path(self, path)
        else:
            path = super().translate_path(path)
        # Since we are serving from the project root instead of content root
        # we want to insert 'content' into the filepath.
        path = abspath(join('output', relpath(path)))
        return path

    def log_request(self, code='-', size='-'):
        # Don't log HEAD requests because these are very spammy with livejs turned on
        if self.command == 'HEAD':
            return
        if platform.python_version_tuple()[0] == '2':
            SimpleHTTPRequestHandler.log_request(self, code, size)
        else:
            super().log_request(code, size)


class HTTPServer(TCPServer):
    def server_activate(self):
        ui('Server started successfully')
        logging.debug('Listening on http://%s:%s/' % self.server_address)
        if platform.python_version_tuple()[0] == '2':
            TCPServer.server_activate(self)
        else:
            super().server_activate()


class Server:
    def __init__(self, site):
        self.site = site

    def serve(self, address, port):
        HTTPHandler.site = self.site
        ui('Starting server on http://%s:%s/' % (address, port))
        ui('HEAD requests are omitted from the logs')
        while True:
            try:

                httpd = HTTPServer((address, port), HTTPHandler)
                httpd.serve_forever()
            except OSError:
                ui('ERROR: Listen socket is busy; will retry in 5 seconds')
                time.sleep(5)
            except KeyboardInterrupt:
                httpd.shutdown()
                break


@click.group()
def cli():
    global ui
    ui = click.echo


@cli.command(help="""
    Initialize a project in the specified directory. The path will be created if
    it does not exist.
    """)
@click.option("--debug/--no-debug", default=False)
@click.option("-f/--force", help="Initialize even if the directory is not empty", default=False)
@click.argument("path", type=click.Path())
def init(debug, f, path):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if len(ls_relative(path)) > 0 and not f:
        click.echo("Path \"%s\" already contains files; use -f to force initialization" % path)
        exit(1)
    Site.initialize(path)


@cli.command()
@click.option("--debug/--no-debug", default=False)
def build(debug):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    Site(curdir).build()


@cli.command()
@click.option("--debug/--no-debug", default=False)
@click.option("--address", '-a', default="127.0.0.1", type=str)
@click.option("--port", '-p', default=8000, type=int)
def preview(debug, address, port):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)

    site = Site(curdir, preview_mode=True)
    site.build()

    watcher = Watcher(site)
    watcher_pid = Process(target=watcher.watch)
    watcher_pid.daemon = False
    watcher_pid.start()

    server = Server(site)
    server_pid = Process(target=server.serve, args=(address, port))
    server_pid.daemon = False
    server_pid.start()

    click.echo('Use Ctrl-C to quit')

    watcher_pid.join()
    server_pid.join()


@cli.command()
@click.option("--debug/--no-debug", default=False)
def watch(debug):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    Watcher(Site(curdir, preview_mode=True)).watch()


@cli.command()
@click.option("--debug/--no-debug", default=False)
def serve(debug):
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    Server(Site(curdir, preview_mode=True)).serve("127.0.0.1", 8000)


if __name__ == "__main__":
    cli()
