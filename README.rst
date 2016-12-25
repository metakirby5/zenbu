==============
 zenbu (全部)
==============

|Sample Usage|

A setup-agnostic cascading theme engine. Uses Jinja2 for templates and YAML
for variable definition.

The above gif was brought to you by `wzb-utils`_.

Installation
------------

::

   pip install zenbu

or just move ``zenbu.py`` to somewhere in your ``$PATH``.
If you do the latter, you must install the dependencies in the
following section manually.

Dependencies
------------

-  Python (2 or 3)

The below are Python libraries that should be installed via ``pip``.
Alternatively, if you did ``pip install zenbu``, these should have been
automatically installed.

- argcomplete
- colorlog
- Jinja2
- PyYAML
- termcolor
- watchdog


Tab completion
--------------

::

  sudo activate-global-python-argcomplete

If you installed via pip, you may need to run the following before autocompletion works:

::

  grep 'PYTHON_ARGCOMPLETE_OK' "$(which zenbu)" &>/dev/null || sudo sed -i "1a # PYTHON_ARGCOMPLETE_OK" "$(which zenbu)"

Usage
-----

Check the `example`_ folder for some sample usage!

For a more detailed explanation, check out the `wiki homepage`_.

For common issues, check the `common gotchas wiki page`_.

For some neat tools (including automatic desktop reloads), check the
`tools wiki page`_.

::

  usage: zenbu [-h] [-l] [-t TEMPLATE_DIR] [-d DEST_DIR] [-s VAR_SET_DIR]
               [-f FILTERS_FILE] [-i IGNORES_FILE] [-e] [-w]
               [--watch-command WATCH_COMMAND] [--watch-dirs WATCH_DIRS]
               [--diff] [--dry]
               [variable_files [variable_files ...]]

  A Jinja2 + YAML based config templater.

  Searches for an optional yaml file with a variable mapping in
  ~/.config/zenbu/defaults.yaml,

  an optional python file with filters in (by default)
  ~/.config/zenbu/filters.py,

  an optional yaml file with an ignore scalar of regexes in (by default)
  ~/.config/zenbu/ignores.yaml,

  and uses the Jinja2 templates in (by default)
  ~/.config/zenbu/templates/

  to render into your home directory (by default).

  Additional variable files can be applied
  by supplying them as arguments, in order of application.

  They can either be paths or, if located in (by default)
  ~/.config/zenbu/variable_sets/,
  extension-less filenames.

  Environment variable support is available;
  simply run with the `-e` flag and
  put the name of the variable in Jinja2 brackets.

  The default Jinja2 globals and filters are available.

  Order of precedence is:
  last YAML variable defined >
  first YAML variable defined >
  environment variables.

  Variables are shallowly resolved once. Thus, for example you may have the
  following in your defaults.yaml for convenience:

  n_primary:  "{{ colors[colors.primary].normal }}"

  Autocomplete support available, but only for the default
  variable set directory.

  A file watcher is available via the -w flag.
  Whenever a variable file in use, the filters file, the ignores file,
  or a template file changes, the templates are rendered
  if there are any differences. This can be overridden with a custom list of
  directories via the --watch-dirs flag.

  Diffs between the current destination files and
  template renderings are available via the --diff flag.

  For help on designing templates, refer to
  http://jinja.pocoo.org/docs/dev/templates/

  For help on creating filters, refer to
  http://jinja.pocoo.org/docs/dev/api/#custom-filters

  positional arguments:
    variable_files        additional variable files

  optional arguments:
    -h, --help            show this help message and exit
    -l                    list variable sets.
    -t TEMPLATE_DIR       template directory. Default:
                          /Users/echan/.config/zenbu/templates
    -d DEST_DIR           destination directory. Default: /Users/echan
    -s VAR_SET_DIR        variable set directory. Default:
                          /Users/echan/.config/zenbu/variable_sets
    -f FILTERS_FILE       filters file. Default:
                          /Users/echan/.config/zenbu/filters.py
    -i IGNORES_FILE       ignores file. Default:
                          /Users/echan/.config/zenbu/ignores.yaml
    -e                    whether or not to use environment variables. Default:
                          don't use environment variables
    -w                    start file watcher.
    --watch-command WATCH_COMMAND
                          what to execute when a change occurs. Default: Nothing
    --watch-dirs WATCH_DIRS
                          override what directories to watch, colon-separated.
                          Default: Nothing
    --diff                show diff between template renderings and current
                          destination files
    --dry                 do a dry run

Zenbu in the wild
-----------------

|enju|

What happened to whizkers?
--------------------------

This project may seem awfully similar to `whizkers`_; in fact, this is a fork
of whizkers which swaps the Mustache backend out with Jinja2. I'm keeping
whizkers around for compatibility reasons. So what are the reasons for
switching?

- Comprehensive documentation: See the
  `Jinja2 Template Designer Documentation`_.
- Better logic: Everything from if/else to macros. I originally praised
  Mustache for its logic-less philosophy, but then I realized that there would
  be no place to put logic other than the variable sets, which is a nightmare.
- Expressions: You can now do ``{{ ':bold' if use_bold else '' }}``. You can
  even do ``{{ colors[colors.primary]['normal'] }}``, which has led to the
  deprecation of the ``{` ... `}`` eval syntax.
- Filters: You can now do ``{{ colors.black.bold | to_rgb }}``. A lot better
  than Mustache's syntax.
- Better whitespace control: This means increased readability.

To help ease the transition to zenbu, there are some tips under the
`migration wiki page`_.

Thanks to
---------

- https://gist.github.com/coleifer/33484bff21c34644dae1
- http://jinja.pocoo.org/
- http://pyyaml.org/
- `fullsalvo`_ for ideas, opinions, the readme gif, contributing to documentation,
  shilling, and overall being a good guy

.. |Sample Usage| image:: http://i.imgur.com/auBfvx0.gif
   :target: https://u.teknik.io/FUkHM.webm
   :alt: zenbu with fullsalvo's wzb-utils.
.. |enju| image:: http://i.imgur.com/EkT9OY5.gif
   :target: http://asator.xyz/img/dad9.webm
   :alt: enju on 2bwm.
.. _wzb-utils: https://github.com/fullsalvo/wzb-utils
.. _whizkers: https://github.com/metakirby5/whizkers
.. _Jinja2: http://jinja.pocoo.org/
.. _Jinja2 Template Designer Documentation:
    http://jinja.pocoo.org/docs/dev/templates/
.. _YAML: http://yaml.org/
.. _wiki homepage: https://github.com/metakirby5/zenbu/wiki
.. _migration wiki page: https://github.com/metakirby5/zenbu/wiki/Migration
.. _common gotchas wiki page:
    https://github.com/metakirby5/zenbu/wiki/Common-gotchas
.. _tools wiki page:
    https://github.com/metakirby5/zenbu/wiki/Tools
.. _example: example
.. _fullsalvo: https://github.com/fullsalvo
