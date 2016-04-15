# 0.5.0 - April 14, 2016

- Added livejs to automatically reload pages while you are editing
- If the the listen socket is busy when running `preview`, icecake will retry
  until it is available

# 0.4.0 - April 4, 2016

- Added dynamic rebuilds of dependent resources when using `preview`. For
  example if you change a template all pages that include that template will be
  rebuilt.

# 0.3.4 - March 29, 2016

- Miscellaneous fixes for python 2/3 compatibility

# 0.3.0 - March 29, 2016

- Added the `preview` command, which automatically rebuilds changed pages and
  displays the site with a built-in HTTP server

# 0.2.2 - March 24, 2016

- Documentation fixes for pypi

# 0.2.0 - March 24, 2016

- Added the `init` command to bootstrap a site for you

# 0.1.0 - March 23, 2016

- Initial release to pypi
