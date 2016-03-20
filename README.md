# Icecake

A cool and easy static site builder.

Jinja templates. Markdown. Pygments source code higlighting. Blog-aware. Atom feeds. Live preview. Clean URLs. MIT license. Minimal design.

## Designed for Simplicity

Icecake aims to be simple. It has a simple license. It does not support lots of features. For example, it does not support plugins, themes, different templating backends, or any of a long list of other features.

Icecake is less than 500 lines of python and still has everything you need to have a pleasant time writing and updating your personal website or blog.

I hope that this simplicity makes it easy for you to read the code and add any feature(s) you can't live without.

If you are already familiar with how static site builders work and you're comfortable with Jinja templates, you can use the following commands to get started:

    pip install icecake
    icecake init mysite.com
    cd mysite.com
    icecake preview

If these topics are new to you, keep reading for more details!

## Installation

    pip install icecake

> How do I get `pip`?

`pip` usually comes with Python. If it's missing, you can get it [here](https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip).

# Creating a Website

First, we'll setup a site:

    icecake init mysite
    cd mysite

It will look something like this:

```
.
├── content
│   ├── articles
│   │   └── hello-world.md
│   ├── articles.html
│   ├── atom.xml
│   └── index.html
├── layouts
│   ├── basic.html
│   └── markdown.html
├── output (empty for now)
└── static
    └── css
        ├── main.css
        └── syntax.css
```

The starter site includes a minimal theme and the articles folder will help you start blogging right away (if you want to do that).

Run `icecake preview` to view the site. The site will be automatically regenerated when you make changes.

## Generating the Site

There is a 3 step process for generating the site.

1. Icecake reads all of the files under `content` and renders them. Markdown is converted to HTML and Jinja templates are evaluated.
2. Icecake writes all of the rendered files into `output`. `articles/hello-world.md` becomes `articles/hello-world/index.html` so you get nice URLs on any hosting platform.
3. Files from `static` are copied as-is to `output` (using the same directory structure as the originals).

A page's URL is based on the filename, without the file extension. For example, `articles/hello-world.md` becomes `articles/hello-world/`. There is a special exception for files named `index.html` or `index.md`. We usually don't want these to end up as e.g. `articles/index/`. If you do actually want "index" to be in the URL you can explicitly set this by specifying the `slug`.

When you're ready, you can use `rsync` or `s3cmd` or an FTP client to publish `output` to the web.

## Editing Content

You can write content in either [Markdown](https://daringfireball.net/projects/markdown/syntax) or HTML. Markdown files (idenfified by `.md` or `.markdown`) are automatically parsed and rendered using the `markdown.html` template. Source code blocks are highlighted using [Pygments](http://pygments.org).

HTML files are evaluating using Jinja. Refer to the [Jinja Template Designer documentation](http://jinja.pocoo.org/docs/dev/templates/#template-designer-documentation) for details. We will also highlight some important Icecake-specific features related to templates below.

Markdown files are handled as a special case inside Icecake, so you can't mix Markdown and Jinja in the same file. However, you can customize the markdown template by editing `markdown.html` or by overriding the `template` metadata field and specifying a new template. See the **Page Metadata** section for more info.

## Page Metadata

At the top of each file you can add some metadata. You should add this to all your markdown pages. Metadata is usually not needed for HTML pages.

```
title = Installing Ruby the Correct Way
date = 2013-03-27
tags = ruby bundler rbenv ruby-build
slug = installing-ruby
template = custom-markdown.html
++++

Your content starts here!
```

- `title` (required)
- `date` (required)
- `tags` (optional) Space-separated list of tags, which can be used to categorize your page.
- `slug` (optional) This will be used instead of the filename in the URL
- `template` (optional) This overrides the template (`markdown.html` by default) used to render the page

Some other metadata are generated for you automatically:

- `filepath` Relative path of the file inside `content`, such as `articles/hello-world.md`
- `folder` Just the folder part like `articles/`
- `ext` The file extension (`.html` or `.md` for example)
- `url` The path part of the URL, such as `/articles/hello-world/`

These metadata are important not just to make your page display correctly, but also to query other pages in your templates. You will do this to make a list of all your pages, for example.

### Rendering Metadata

Whenever you are writing a template the current page's metadata is available via `page`, so you can show the page title via `{{ page.title }}` or the publish date via `{{ page.date }}`. You can also write `if` statements that reference this information.

To show a list of tags for your page you can write something like this:

```
<p>Tagged
{% for tag in page.tags %}
    <span class="tag">{{ tag }}</span>
{% endfor %}
</p>
```

### When Is Metadata **Required**?

Metadata is only required if you reference it somewhere. I recommend always using it on Markdown files and only using it on HTML if you have to. The default Markdown templates assume that you have provided titles, tags, and publish dates in your metadata and won't work properly if these are missing.

**Warning:** if you try to query a page using Finder (below) and a piece of metadata is missing, your query will fail.

# The Finder

The Finder is a special feature available in templates that allows you to query other pages and tags across your site. For example, if you want to incldue a list of your 5 latest blog entries on your homepage, the Finder can do this for you.

## Querying Pages

You can search across the pages on your site using `find.pages`.

    find.pages(option=value, ...)

With no arguments, `find.pages` includes _all_ pages on your site. You can filter this list using the following filter options:

- `path` Filter based on the path under `content/`. The `path` string is compared using `startswith()` so `cake` will match `cake/chocolate` but not `chocolate/cake`.
- `tag` Filter based on a tag
- `order` Sort the results based on the specified metadata, like `date`. Use `-date` to reverse the order.
- `limit` Limit the number of items you get back.

You can combine these options much like SQL. They are evaluated in the order listed above, so a `path` filter is applied, then `order`, and finally `limit`.

Warning: If you try to sort based on a metadata property that is not specified on every item, sort will fail! Icecake does not enforce that all of your pages have the same metadata so this is up to you.

We'll show two examples of how to use this below.

#### List Articles Tagged "Blog"

You can use this to create a blog index page, for example:

```
{% for page in find.pages(tag="blog", order="title") %}
    <a href="{{ page.url }}">{{ page.title }}</a>
{% endfor %}
```

#### List 5 Recent Articles

```
{% for page in find.pages(path="articles/", order="-date", limit=5) %}
    <a href="{{ page.url }}">{{ page.title }}</a>
{% endfor %}
```

If you want to match a folder named `articles/` but not a file named `articles.html`, make sure to include `/` at the end!

## Generating an Atom Feed

You can use `find.atom` to create an Atom feed for specific pages on your site. The query behavior works exactly the same way as `find.pages` so please refer to that for details.

Unlike `find.pages` the atom feed is simply printed out -- you don't need to iterate over it.

    {{ find.atom(path="articles/", order="-date") }}

## Listing Tags

You can use `find.tags` to list all of the tags in use on your site. You cannot currently query or filter the list of tags.

```
{% for tag in find.tags() %}
    ...
{% endfor %}
```

Don't confuse this with `page.tags`!
