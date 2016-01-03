whizkers
========

Mustache + YAML based config templater.

|Sample usage|

Installation
============

::

   pip install whizkers

or just move ``whizkers.py`` to somewhere in your ``$PATH``.

Dependencies
============

-  Python (2 or 3)

The below are Python libraries that should be installed via ``pip``.
Alternatively, if you did ``pip install whizkers``,
these should have been automatically installed.

-  argcomplete
-  colorlog
-  pystache
-  PyYAML
-  termcolor
-  watchdog

Autocomplete
============

::

    sudo activate-global-python-argcomplete

If you installed via pip, you may need to run the following before autocompletion works:

::

   grep 'PYTHON_ARGCOMPLETE_OK' "$(which whizkers)" &>/dev/null || sudo sed -i "1a # PYTHON_ARGCOMPLETE_OK" "$(which whizkers)"

Usage
=====

::

    usage: whizkers [-h] [-l] [-t TEMPLATE_DIR] [-d DEST_DIR] [-s VAR_SET_DIR]
                    [-i IGNORES_FILE] [-e] [-w] [--watch-command WATCH_COMMAND]
                    [--diff] [--dry]
                    [variable_files [variable_files ...]]

    A pystache + YAML based config templater.

    Searches for an optional yaml file with a variable mapping in
    ~/.config/whizkers/variables.yaml,

    an optional yaml file with an ignore scalar of regexes in (by default)
    ~/.config/whizkers/ignores.yaml,

    and uses the mustache templates in (by default)
    ~/.config/whizkers/templates/

    to render into your home directory (by default).

    Additional variable files can be applied
    by supplying them as arguments, in order of application.

    They can either be paths or, if located in (by default)
    ~/.config/whizkers/variable_sets/,
    extension-less filenames.

    Environment variable support is available;
    simply put the name of the variable in mustache brackets.

    Order of precedence is:
    last YAML variable defined >
    first YAML variable defined >
    environment variables.

    Variables are shallowly resolved once, then anything in
    {`...`} is eval'd in Python.

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
                            /home/echan/.config/whizkers/templates
      -d DEST_DIR           destination directory. Default: /home/echan
      -s VAR_SET_DIR        variable set directory. Default:
                            /home/echan/.config/whizkers/variable_sets
      -i IGNORES_FILE       ignores file. Default:
                            /home/echan/.config/whizkers/ignores.yaml
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

-  https://gist.github.com/coleifer/33484bff21c34644dae1
-  https://github.com/defunkt/pystache
-  http://pyyaml.org/

.. |Sample usage| image:: https://u.teknik.io/u8Au4P.gif
   :target: https://u.teknik.io/lCAD1H.webm
