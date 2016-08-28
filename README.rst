===============
 sanpai (参拝)
===============

*visit to a shrine or temple; paying homage at a shrine or temple*

**:warning: UNDER CONSTRUCTION :warning:**

`Jinja2`_ + `YAML`_ based config templater.

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
  deprecation of shallow evaluation (``{` ... `}`` syntax).
- Filters: You can now do ``{{ colors.black.bold | hex2rgb }}``. A lot better
  than Mustache's syntax.
- Better whitespace control: This means increased readability.

To help ease the transition to sanpai, there are some resources under
`migration`_.

Installation
------------

Currently, the easiest method of installation is to move ``sanpai.py``
to somewhere in your ``$PATH``. Be warned, you must install the
dependencies in the following section manually.

Pip installation coming soon™

Dependencies
------------

-  Python (2 or 3)

The below are Python libraries that should be installed via ``pip``.
Alternatively, if you did ``pip install sanpai``, these should have been
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

   grep 'PYTHON_ARGCOMPLETE_OK' "$(which sanpai)" &>/dev/null || sudo sed -i "1a # PYTHON_ARGCOMPLETE_OK" "$(which sanpai)"

Usage
-----

Check the `example`_ folder for some sample usage!

::

   usage: sanpai.py [-h] [-l] [-t TEMPLATE_DIR] [-d DEST_DIR] [-s VAR_SET_DIR]
                   [-f FILTERS] [-i IGNORES_FILE] [-e] [-w]
                   [--watch-command WATCH_COMMAND] [--diff] [--dry]
                   [variable_files [variable_files ...]]

   A Jinja2 + YAML based config templater.

   Searches for an optional yaml file with a variable mapping in
   ~/.config/sanpai/defaults.yaml,

   an optional python file with filters in (by default)
   ~/.config/sanpai/filters.py,

   an optional yaml file with an ignore scalar of regexes in (by default)
   ~/.config/sanpai/ignores.yaml,

   and uses the Jinja2 templates in (by default)
   ~/.config/sanpai/templates/

   to render into your home directory (by default).

   Additional variable files can be applied
   by supplying them as arguments, in order of application.

   They can either be paths or, if located in (by default)
   ~/.config/sanpai/variable_sets/,
   extension-less filenames.

   Environment variable support is available;
   simply run with the `-e` flag and
   put the name of the variable in Jinja2 brackets.

   The default Jinja2 globals and filters are available.

   Order of precedence is:
   last YAML variable defined >
   first YAML variable defined >
   environment variables.

   Autocomplete support available, but only for the default
   variable set directory.

   A file watcher is available via the -w flag.
   Whenever a variable file in use, the ignores file,
   or a template file changes, the templates are rendered
   if there are any differences.

   Diffs between the current destination files and
   template renderings are available via the --diff flag.

   positional arguments:
    variable_files        additional variable files

   optional arguments:
    -h, --help            show this help message and exit
    -l                    list variable sets.
    -t TEMPLATE_DIR       template directory. Default:
                          /Users/echan/.config/sanpai/templates
    -d DEST_DIR           destination directory. Default: /Users/echan
    -s VAR_SET_DIR        variable set directory. Default:
                          /Users/echan/.config/sanpai/variable_sets
    -f FILTERS            filters file. Default:
                          /Users/echan/.config/sanpai/filters.py
    -i IGNORES_FILE       ignores file. Default:
                          /Users/echan/.config/sanpai/ignores.yaml
    -e                    whether or not to use environment variables. Default:
                          don't use environment variables
    -w                    start file watcher.
    --watch-command WATCH_COMMAND
                          what to execute when a change occurs. Default: Nothing
    --diff                show diff between template renderings and current
                          destination files
    --dry                 do a dry run

    For help on designing templates, refer to
    http://jinja.pocoo.org/docs/dev/templates/

    For help on creating filters, refer to
    http://jinja.pocoo.org/docs/dev/api/#custom-filters

Thanks to
---------

- https://gist.github.com/coleifer/33484bff21c34644dae1
- http://jinja.pocoo.org/
- http://pyyaml.org/
- `fullsalvo`_ for ideas, opinions, contributing to documentation,
  shilling, and overall being a good guy

.. _Jinja2: http://jinja.pocoo.org/
.. _YAML: http://yaml.org/
.. _Jinja2 Template Designer Documentation:
     http://jinja.pocoo.org/docs/dev/templates/
.. _whizkers: https://github.com/metakirby5/whizkers
.. _migration: migration
.. _example: example
.. _fullsalvo: https://github.com/fullsalvo
