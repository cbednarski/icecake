templates = {
"content/articles.html":
"""{% extends "basic.html" %}

{% block title %}Articles :: My Site.com{% endblock %}

{% block content %}

<div class="article">

<h1>Articles</h1>

<ul class="articles">
{% for page in site.pages(path="articles/", order="-date") %}
	<li><a href="{{ page.url }}">{{ page.title }}</a></li>
{% endfor %}
</ul>

</div>

{% endblock %}
""",
"content/articles/hello-world.md":
"""title = Hello world!
date = 2016-04-02
tags = hello
++++

I'm building a website! When I do something cool that I'd like to share with you, I'm going to write about it here.

I'll write with [Markdown](https://daringfireball.net/projects/markdown/) and maybe even write some code:

```
# This is a title

And this is a list:

- cake
- chocolate
- candy
```

That's all for now!""",
"content/atom.xml":
"""{{
  site.atom(
    path="articles/",
    order="-date",
    site_url="https://example.com",
    feed_url="https://example.com"+url,
    feed_title="My Site",
    feed_subtitle=None,
    author="a smart person"
  )
}}""",
"content/index.html":
"""{% extends "basic.html" %}

{% block title %}My Site.com{% endblock %}

{% block content %}

<div class="article">

<p>Hi, this is my site.</p>

<p>Here's something interesting about me that you might not know.</p>

<p>Follow me on <a href="https://twitter.com/">Twitter</a></p>

<h2>Recent Articles</h2>
<ul class="articles">
{% for page in site.pages(path="articles/", limit=5, order="-date") %}
	<li><a href="{{ page.url }}">{{ page.title }}</a></li>
{% endfor %}
</ul>

<p><a href="/articles/">See all of them</a></p>

</div>

{% endblock %}
""",
"content/tags.html":
"""{% extends "basic.html" %}

{% block title %}My Site.com{% endblock %}

{% block content %}

<div class="article">

{% for tag in site.tags() %}
	<div id="tag-{{tag}}" class="tag-block">
	<h1>{{tag}}</h1>
	<ul>
	{% for page in site.pages(path="articles/", order="title", tag=tag) %}
		<li><a href="{{ page.url }}">{{ page.title }}</a></li>
	{% endfor %}
	</ul>
	</div>
{% endfor %}

</div>

{% endblock %}
""",
"layouts/basic.html":
"""<!DOCTYPE html>
<head>
  <title>{% block title %}{{ title }} :: My Site.com{% endblock %}</title>
  <link href="/css/main.css" rel="stylesheet" />
  <link href="/css/syntax.css" rel="stylesheet" />
  <link href="/atom.xml" rel="alternate" type="application/atom+xml" title="My Site" />
  <link href="//fonts.googleapis.com/css?family=Domine:400,700" rel="stylesheet" type="text/css" />
</head>
<body>

<nav id="main-nav">
  <a href="/">My Site</a>
  <a href="/articles/">Articles</a>
</nav>

<section id="main-content">
{% block content %}{% endblock %}
</section>

<footer id="main-footer">
  <p>Copyright &copy; 2016 A Smart Person. All rights reserved. | Proudly built with <a href="https://github.com/cbednarski/icecake">Icecake</a></p>
</footer>
{{ livejs }}
</body>
</html>
""",
"layouts/markdown.html":
"""{% extends "basic.html" %}

{% block title %}{{ title }} :: My Site.com{% endblock %}

{% block content %}

<div class="article">
  <h1 class="title">{{ title }}</h1>
  <p class="date">Published {{ date }}</p>

{{ content }}

<hr>

<h4>Related</h4>

<p>
{% for tag in tags %}
<a class="tag" href="/tags/#tag-{{ tag }}">{{ tag }}</a>
{% endfor %}
</p>

</div>

{% endblock %}
""",
"static/css/main.css":
"""body {
    background-color: #05b3e3;
    color: #000;
    font-family: Domine, "PT Serif", Georgia, "Times New Roman", serif;
    font-size: 18px;
    margin: 0;
}

h1, h2, h3, h4, h5 ,h6 {
    color: #444;
}

hr {
    border: 1px solid #777;
    margin:1.5em 0;
}

code,pre {
    font-family: Menlo, Monaco, "Source Sans Pro", "Ubuntu Mono", Consolas, "Courier New", monospace;
    background-color: #F5F5F5;
}

pre {
    font-size: .8em;
    line-height: 1.4em;
    padding: .5em;
    border-radius: 5px;
    overflow-wrap: break-word;
}

code {
    font-size: .8em;
    padding: 1px 4px;
    border-radius: 5px;
    overflow-wrap: break-word;
}

pre>code{
    padding: 0;
    background: transparent;
}

a {
    color: #37AFFF;
    text-decoration: none;
}

blockquote {
    font-style: italic;
    border-left: 4px solid #777;
    color: #555;
    margin: 0;
    padding: .01em 2em;
    background-color: #eee;
}

a:hover, #menu a:hover {
    border-bottom: 1px solid;
}

.box {
    background-color: #fff;
    color: #555;
}

.clear {
    clear: both;
}

.article {
    background: #fff;
    color: #000;
    margin: auto;
    line-height: 2em;
    max-width: 40em;
    padding: 100px;
    margin-top: 50px;
}

.article img {
    max-width: 100%;
    max-height: 100%;
}

.article h1.title {
    margin-top: 0;
    font-size: 2em;
}

.article h1.comments {
    margin-top: 3em;
}

.article-heading h2 a{
    display: block;
    padding: 20px 30px;
    margin-bottom: 20px;
    background-color: #fff;
    transition: background .3s;
    border: none;
}

.article-heading h2 a:hover {
    background-color: #ddd;
    text-decoration: none;
}

.article .date {
    color: #aaa;
    font-style: italic;
}

.chaser h3 {
    margin-top: .7em;
    margin-bottom: .5em;
}

.chaser a {
    margin-right: .2em;
}

.datetime {
    font-style: italic;
    color: #bbb;
    font-size: .8em;
}

.prevnext {
    width: 100%;
}

.prevnext>div {
    width: 48%;
    background-color: #333;
    color: #fff;
}

.prevnext>div a {
    display: block;
    padding: 10px;
    border-bottom: 0;
}

.prevnext>div a:hover {
    color: #80CC15;
}

.prevnext .prev {
    float: left;
}

.prevnext .next {
    float: right;
}

.tag {
    padding: 0 .2em;
}

.tag-block {
    padding: 5px;
    border-radius: 5px;
    margin-bottom: 10px;
    border: 1px solid #fff;
}

.tag-block h2 {
    margin-top: 0;
}

ul.articles, .tag-block ul {
    margin: 0;
    padding: 0;
}

ul.articles li, .tag-block li {
    list-style: none;
}

.tag-block:target {
    border: 1px dashed #37AFFF;
}

#main-nav {
    height: 3em;
    font-size: 1.4em;
    line-height: 3em;
    color: #000;
    padding-left: 2.5em;
}

#main-nav a {
    border: 0;
    color: #000;
    display: inline-block;
    padding: 6px 10px;
}

#main-nav a:hover {
    color: #fff;
    text-decoration: none;
}

#main-footer {
    background-color: transparent;
    clear: both;
    color: #555;
    display: block;
    height: inherit;
    margin: 60px 0 30px;
    text-align: middle;
    vertical-align: bottom;
    width: 100%;
    z-index: 1;
    font-size: .8em;
}

#main-footer p {
    text-align: center;
}

#main-footer a {
    color: #000;
    border-bottom: 1px solid #000;
}
""",
"static/css/syntax.css":
""".codehilite .hll { background-color: #ffffcc }
.codehilite .c { color: #0099FF; font-style: italic } /* Comment */
.codehilite .err { color: #AA0000; background-color: #FFAAAA } /* Error */
.codehilite .k { color: #006699; font-weight: bold } /* Keyword */
.codehilite .o { color: #555555 } /* Operator */
.codehilite .cm { color: #0099FF; font-style: italic } /* Comment.Multiline */
.codehilite .cp { color: #009999 } /* Comment.Preproc */
.codehilite .c1 { color: #0099FF; font-style: italic } /* Comment.Single */
.codehilite .cs { color: #0099FF; font-weight: bold; font-style: italic } /* Comment.Special */
.codehilite .gd { background-color: #FFCCCC; border: 1px solid #CC0000 } /* Generic.Deleted */
.codehilite .ge { font-style: italic } /* Generic.Emph */
.codehilite .gr { color: #FF0000 } /* Generic.Error */
.codehilite .gh { color: #003300; font-weight: bold } /* Generic.Heading */
.codehilite .gi { background-color: #CCFFCC; border: 1px solid #00CC00 } /* Generic.Inserted */
.codehilite .go { color: #AAAAAA } /* Generic.Output */
.codehilite .gp { color: #000099; font-weight: bold } /* Generic.Prompt */
.codehilite .gs { font-weight: bold } /* Generic.Strong */
.codehilite .gu { color: #003300; font-weight: bold } /* Generic.Subheading */
.codehilite .gt { color: #99CC66 } /* Generic.Traceback */
.codehilite .kc { color: #006699; font-weight: bold } /* Keyword.Constant */
.codehilite .kd { color: #006699; font-weight: bold } /* Keyword.Declaration */
.codehilite .kn { color: #006699; font-weight: bold } /* Keyword.Namespace */
.codehilite .kp { color: #006699 } /* Keyword.Pseudo */
.codehilite .kr { color: #006699; font-weight: bold } /* Keyword.Reserved */
.codehilite .kt { color: #007788; font-weight: bold } /* Keyword.Type */
.codehilite .m { color: #FF6600 } /* Literal.Number */
.codehilite .s { color: #CC3300 } /* Literal.String */
.codehilite .na { color: #330099 } /* Name.Attribute */
.codehilite .nb { color: #336666 } /* Name.Builtin */
.codehilite .nc { color: #00AA88; font-weight: bold } /* Name.Class */
.codehilite .no { color: #336600 } /* Name.Constant */
.codehilite .nd { color: #9999FF } /* Name.Decorator */
.codehilite .ni { color: #999999; font-weight: bold } /* Name.Entity */
.codehilite .ne { color: #CC0000; font-weight: bold } /* Name.Exception */
.codehilite .nf { color: #CC00FF } /* Name.Function */
.codehilite .nl { color: #9999FF } /* Name.Label */
.codehilite .nn { color: #00CCFF; font-weight: bold } /* Name.Namespace */
.codehilite .nt { color: #330099; font-weight: bold } /* Name.Tag */
.codehilite .nv { color: #003333 } /* Name.Variable */
.codehilite .ow { color: #000000; font-weight: bold } /* Operator.Word */
.codehilite .w { color: #bbbbbb } /* Text.Whitespace */
.codehilite .mf { color: #FF6600 } /* Literal.Number.Float */
.codehilite .mh { color: #FF6600 } /* Literal.Number.Hex */
.codehilite .mi { color: #FF6600 } /* Literal.Number.Integer */
.codehilite .mo { color: #FF6600 } /* Literal.Number.Oct */
.codehilite .sb { color: #CC3300 } /* Literal.String.Backtick */
.codehilite .sc { color: #CC3300 } /* Literal.String.Char */
.codehilite .sd { color: #CC3300; font-style: italic } /* Literal.String.Doc */
.codehilite .s2 { color: #CC3300 } /* Literal.String.Double */
.codehilite .se { color: #CC3300; font-weight: bold } /* Literal.String.Escape */
.codehilite .sh { color: #CC3300 } /* Literal.String.Heredoc */
.codehilite .si { color: #AA0000 } /* Literal.String.Interpol */
.codehilite .sx { color: #CC3300 } /* Literal.String.Other */
.codehilite .sr { color: #33AAAA } /* Literal.String.Regex */
.codehilite .s1 { color: #CC3300 } /* Literal.String.Single */
.codehilite .ss { color: #FFCC33 } /* Literal.String.Symbol */
.codehilite .bp { color: #336666 } /* Name.Builtin.Pseudo */
.codehilite .vc { color: #003333 } /* Name.Variable.Class */
.codehilite .vg { color: #003333 } /* Name.Variable.Global */
.codehilite .vi { color: #003333 } /* Name.Variable.Instance */
.codehilite .il { color: #FF6600 } /* Literal.Number.Integer.Long */""",
}