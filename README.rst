===============
 sanpai (参拝)
===============

*visit to a shrine or temple; paying homage at a shrine or temple*

whizkers 2.0
============

**THIS IS A WORK IN PROGRESS**

`Jinja2`_ + `YAML`_ based config templater.

Why leave pystache?
-------------------

While the use of mustache worked well, the largest contributing factor to
the switch was the logic-less approach to templating.

Installation
============

Currently, the easiest method of installation is to move ``sanpai.py``
to somewhere in your ``$PATH``. Be warned, you must install the dependencies in the following section manually.

Dependencies
============

-  Python (2 or 3)

The below are Python libraries that should be installed via ``pip``.

-  argcomplete
-  colorlog
-  Jinja2
-  PyYAML
-  termcolor
-  watchdog

Usage
=====

Check the `example`_ folder for some sample usage!

::

    usage: sanpai [-h] [-l] [-t TEMPLATE_DIR] [-d DEST_DIR] [-s VAR_SET_DIR]
                    [-i IGNORES_FILE] [-e] [-w] [--watch-command WATCH_COMMAND]
                    [--diff] [--dry]
                    [variable_files [variable_files ...]]

    A Jinja2 + YAML based config templater.

    Searches for an optional yaml file with a variable mapping in
    ~/.config/sanpai/variables.yaml,

    an optional yaml file with an ignore scalar of regexes in (by default)
    ~/.config/sanpai/ignores.yaml,

    and uses the mustache templates in (by default)
    ~/.config/sanpai/templates/

    to render into your home directory (by default).

    Additional variable files can be applied
    by supplying them as arguments, in order of application.

    They can either be paths or, if located in (by default)
    ~/.config/sanpai/variable_sets/,
    extension-less filenames.

    Environment variable support is available;
    simply put the name of the variable in mustache brackets.

    Order of precedence is:
    last YAML variable defined >
    first YAML variable defined >
    environment variables.

    Variables are shallowly resolved once, then anything in
    {%...%} is eval'd in Python.

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
                            /home/echan/.config/sanpai/templates
      -d DEST_DIR           destination directory. Default: /home/echan
      -s VAR_SET_DIR        variable set directory. Default:
                            /home/echan/.config/sanpai/variable_sets
      -i IGNORES_FILE       ignores file. Default:
                            /home/echan/.config/sanpai/ignores.yaml
      -e                    whether or not to use environment variables. Default:
                            don't use environment variables
      -w                    start file watcher.
      --watch-command WATCH_COMMAND
                            what to execute when a change occurs. Default: Nothing
      --diff                show diff between template renderings and current
                            destination files
      --dry                 do a dry run

Thanks to
=========

- https://gist.github.com/coleifer/33484bff21c34644dae1
- http://jinja.pocoo.org/
- http://pyyaml.org/
- `fullsalvo`_ for ideas, opinions, contributing to documentation,
  shilling, and overall being a good guy

.. _Jinja2: http://jinja.pocoo.org/
.. _YAML: http://yaml.org/
.. _fullsalvo: https://github.com/fullsalvo
