#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

"""
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
"""

import collections
import logging
import os
import sys
import codecs
import yaml
import re
import argcomplete
import traceback
from importlib import import_module
from shutil import copystat
from subprocess import call, check_output
from threading import Timer
from time import sleep
from difflib import unified_diff
from pydoc import pipepager # Dangerously undocumented...
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from termcolor import colored
from colorlog import ColoredFormatter
from jinja2 import Environment, FileSystemLoader, StrictUndefined, \
     UndefinedError, TemplateSyntaxError, TemplateNotFound
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Constants
HOME = os.getenv('HOME')
CONFIG_DIR = os.getenv(
    'XDG_CONFIG_HOME',
    os.path.join(HOME, '.config'))
ZENBU_ROOT = os.path.join(
    CONFIG_DIR, 'zenbu')
ZENBU_DEFAULTS = os.path.join(
    ZENBU_ROOT, 'defaults.yaml')
ZENBU_VAR_SETS = os.path.join(
    ZENBU_ROOT, 'variable_sets')
ZENBU_FILTERS = os.path.join(
    ZENBU_ROOT, 'filters.py')
ZENBU_IGNORES = os.path.join(
    ZENBU_ROOT, 'ignores.yaml')
ZENBU_TEMPLATES = os.path.join(
    ZENBU_ROOT, 'templates')
TEMPLATE_EXT = 'yaml'
WATCH_TIMEOUT = 0.5

# Logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.NullHandler())

# Autocomplete
def variable_set_completer(prefix, **kwargs):
    # Use dummy template and dest directory
    # TODO: make this less janky
    DUMMY = '/tmp/'
    try:
        var_sets = Zenbu(
            DUMMY,
            DUMMY,
            ZENBU_VAR_SETS,
            ignores_path=ZENBU_IGNORES,
        ).var_sets
    except NotFoundError as e:
        # Try again with no ignores file
        try:
            var_sets = Zenbu(
                DUMMY,
                DUMMY,
                ZENBU_VAR_SETS,
            ).var_sets
        except NotFoundError as e:
            argcomplete.warn(e)
    except Exception as e:
        argcomplete.warn(e)
    else:
        return (v for v in var_sets if v.startswith(prefix))

def compgen_completer(prefix, **kwargs):
    out = check_output('compgen -A function -abck',
                       shell=True, universal_newlines=True)
    return (v for v in out.split() if v.startswith(prefix))

# Convenience functions
def make_dirs_and_open(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return codecs.open(path, 'w', 'utf-8')

def diff_colorify(line):
    if re.match(r'^(===|---|\+\+\+|@@)', line):
        return colored(line, attrs=['bold'])
    elif re.match(r'^\+', line):
        return colored(line, 'green')
    elif re.match(r'^-', line):
        return colored(line, 'red')
    elif re.match(r'^\?', line):
        return colored(line, 'yellow')
    else:
        return line

def deep_update_dict(d, u):
    for k, v in u.items():
        if isinstance(d, collections.Mapping):
            if isinstance(v, collections.Mapping):
                r = deep_update_dict(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}
    return d


# Exceptions
class PathException(Exception):
    def __init__(self, path, message=None):
        super(PathException, self).__init__()
        self.message = message
        self.path = path


class NotFoundError(PathException):
    def __str__(self):
        msg = "Was not found: \"%s\"" % self.path
        if self.message:
            msg += "\n    (%s)" % self.message
        return msg


class ParseError(PathException):
    def __str__(self):
        msg = "Could not parse: \"%s\"" % self.path
        if self.message:
            msg += "\n%s" % self.message
        return msg


class RenderError(PathException):
    def __str__(self):
        msg = "Could not render: \"%s\"" % self.path
        if self.message:
            msg += "\n    (%s)" % self.message
        return msg


class VariableRenderError(Exception):
    def __init__(self, variable_name, message=None):
        super(VariableRenderError, self).__init__(message)
        self.variable_name = variable_name
    def __str__(self):
        msg = "Could not render variable: \"%s\"" % self.variable_name
        if self.message:
            msg += "\n    (%s)" % self.message
        return msg


# Utility scope class
class Scope(object):
    pass


# Handler for all events
class AllEventsHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_any_event(self, event):
        self.callback(event)


class Zenbu:
    """
    A template manager.
    """
    def __init__(self,
                 templates_path,
                 dest_path,
                 var_set_path=None,
                 use_env_vars=False,
                 variables=None,
                 filters_path=None,
                 ignores_path=None,
                 watch_command=None,
                 watch_dirs=None):

        self.variables = variables or []  # Variable sets to apply
        self.use_env_vars = use_env_vars  # Whether or not to use env vars
        self.watch_paths = set()          # List of paths to watch

        # Check required paths
        if os.path.exists(templates_path):
            self.templates_path = templates_path
            self.templates_path_re = re.compile(
                '^{}'.format(templates_path))
            self.watch_paths.add(templates_path)
        else:
            raise NotFoundError(templates_path, "templates path")

        if os.path.exists(dest_path):
            self.dest_path = dest_path
        else:
            raise NotFoundError(dest_path, "destination path")

        # Watchdog
        self.observer = Observer()
        self.watch_command = watch_command

        # Jinja2
        self.env = Environment(loader=FileSystemLoader(templates_path),
                               keep_trailing_newline=True,
                               undefined=StrictUndefined,
                               autoescape=False,
                               cache_size=0)
        self.defaults = {
            'filters': self.env.filters,
            'globals': self.env.globals,
        }

        # Variables
        if var_set_path:
            if os.path.exists(var_set_path):
                self.var_set_path = var_set_path
                self.var_set_path_re = re.compile(
                    '^{}/?'.format(var_set_path or ''))
                self.watch_paths.add(var_set_path)
            else:
                raise NotFoundError(var_set_path, "variable set path")
        else:
            self.var_set_path = None

        # Filters
        if filters_path:
            if os.path.exists(filters_path):
                sys.path.append(os.path.dirname(filters_path))
                self.filters_module = os.path.splitext(
                    os.path.basename(filters_path))[0]
                self.watch_paths.add(filters_path)
            else:
                raise NotFoundError(filters_path, "filters path")
        else:
            self.filters_module = None

        # Ignores
        if ignores_path:
            if os.path.exists(ignores_path):
                self.ignores_path = ignores_path
                self.watch_paths.add(ignores_path)
            else:
                raise NotFoundError(ignores_path, "ignores file")
        else:
            self.ignores_path = None

        # Override watch_paths?
        if watch_dirs:
            self.watch_paths = watch_dirs

        # Initial setup
        self.refresh()

    def refresh(self):
        """
        Refresh ignores, variables, and filters.
        """
        # Get ignores
        self.ignores = set()
        if self.ignores_path:
            self.add_ignores(self.ignores_path)

        # Get filters
        self.env.filters = self.defaults['filters'].copy()
        if self.filters_module:
            try:
                deep_update_dict(
                    self.env.filters,
                    vars(import_module(self.filters_module)))
            except ImportError:
                pass

        # Get variables
        self.env.globals = self.defaults['globals'].copy()
        if self.use_env_vars:
            self.env.globals.update(dict(os.environ))
        for name in self.variables:
            self.add_variables(name)
        self.env.globals = self.render_variables(self.env.globals)

    def add_variables(self, name):
        """
        Add variables to the environment.
        """
        # If it might be just a name...
        if self.var_set_path and not os.path.exists(name):
            name = os.path.join(self.var_set_path, '{}.{}'.format(
                name, TEMPLATE_EXT))

        try:
            with codecs.open(name, 'r', 'utf-8') as f:
                to_merge = yaml.load(f.read())
        except IOError:
            raise NotFoundError(name, "variables file")
        except Exception as e:
            raise ParseError(name, e)
        else:
            self.watch_paths.add(name)
            if isinstance(to_merge, dict):
                logger.info("Using \"%s\"..." % name)
                deep_update_dict(self.env.globals, to_merge)
            else:
                raise ParseError(name, "  (not in mapping format)")

    def render_variables(self, vars):
        """
        Shallowly resolves variables within variables.
        """
        rendered = {} # to avoid rendering order problems
        for k, v in vars.items():
            # Recurse
            if isinstance(v, dict):
                rendered[k] = self.render_variables(v)
            # Render
            elif isinstance(v, str):
                try:
                    rendered[k] = self.env.from_string(v).render()
                except UndefinedError as e:
                    logger.error(VariableRenderError(k, e))
                except TemplateSyntaxError as e:
                    logger.error(VariableRenderError(k, e.message))
                # For all other errors in rendering
                except Exception as e:
                    logger.error(VariableRenderError(k, e))
            else:
                rendered[k] = v
        return rendered

    def add_ignores(self, name):
        """
        Add patterns to the ignore list.
        """
        try:
            with codecs.open(name, 'r', 'utf-8') as f:
                to_merge = yaml.load(f.read())
        except Exception as e:
            raise ParseError(e, name)
        else:
            self.watch_paths.add(name)
            if isinstance(to_merge, list):
                self.ignores |= set(re.compile(i) for i in to_merge)
            else:
                raise ParseError(name, "  (not in scalar format)")

    def should_ignore(self, name):
        """
        Check if a name should be ignored according to self.ignores
        """
        for pattern in self.ignores:
            if pattern.match(name):
                return True
        return False

    @property
    def var_sets(self):
        """
        Yield the available variable sets
        """
        # Does our folder exist?
        if self.var_set_path:

            # Get all the paths...
            for root, _, files in os.walk(self.var_set_path,
                                                followlinks=True):

                # Don't print the var set dir
                short_root = self.var_set_path_re.sub('', root)

                for name in files:
                    if not self.should_ignore(name):
                        path = os.path.join(short_root, name)

                        # Yield without .yaml
                        yield os.path.splitext(path)[0]
        else:
            raise ValueError("No variable set path to list from.")

    @property
    def render_pairs(self):
        """
        Yield pairs of (template file, destination file)
        """
        for root, _, files in os.walk(self.templates_path,
                                            followlinks=True):

            # Substitute the template dir for home dir
            dest_root = self.templates_path_re.sub(self.dest_path, root)

            # Iterate through templates
            for name in files:
                if not self.should_ignore(name):
                    template = os.path.join(root, name)
                    dest = os.path.join(dest_root, name)
                    yield (template, dest)

    def render(self):
        """
        Yield tuples of (template file, destination file, what to write).
        If there is a file render error, log it.
        """
        for template, dest in self.render_pairs:
            try:
                # Jinja needs a path from root
                src = self.templates_path_re.sub('', template)
                yield (template, dest, self.env.get_template(src).render())
            except UndefinedError as e:
                logger.error(RenderError(template, e))
            except TemplateSyntaxError as e:
                logger.error(RenderError(
                    template, '{} on line {}'.format(e.message, e.lineno)))
            except UnicodeDecodeError as e:
                logger.error(RenderError(
                    template, 'This file is probably not text; {}'.format(e)))
            except TemplateNotFound as e:
                logger.error(NotFoundError(template, e))
            # For all other errors in rendering
            except Exception as e:
                tb = traceback.extract_tb(sys.exc_info()[-1])[-1]
                logger.error(RenderError(
                    template, '{} at {}:{}: "{}"'.format(
                        e, tb[0], tb[1], tb[3])))

    def render_and_write(self):
        """
        Render the templates and write them to their destination.
        """
        for template, dest, result in self.render():
            # Delete any existing file first
            try:
                os.remove(dest)
            except OSError:
                pass

            with make_dirs_and_open(dest) as f:
                f.write(result)
                copystat(template, dest)
                logger.info("Successfully rendered \"%s\"" % dest)

    def diff(self):
        """
        Yield diffs between each template's render and current file.
        """
        for template, dest, result in self.render():
            try:
                with codecs.open(dest, 'r', 'utf-8') as f:
                    yield unified_diff(
                        result.splitlines(True),
                        f.readlines(),
                        fromfile=dest,
                        tofile='%s (rendered)' % dest)
            except IOError:
                yield [
                    "=== No destination file \"%s\" for comparison.\n"
                    % dest]

    def watch(self):
        """
        Start the file watcher.
        """
        # Because of read-only closures
        scope = Scope()
        scope.timer = None

        def make_handler(file_to_watch=None):
            def rerender():
                logger.info("\nRe-rendering...")
                self.refresh()

                # If there is no resulting difference, skip
                if not sum(sum(len(d) for d in diff) for diff in self.diff()):
                    logger.info("\nNo difference detected - skipping")
                    return

                self.render_and_write()

                # Execute watch command
                if self.watch_command:
                    logger.info("\nExecuting watch command: %s" %
                                self.watch_command)
                    call(self.watch_command, shell=True)

            def schedule_rerender(event):
                # If we have a specific file, check for it
                if file_to_watch:
                    # If the file is gone, skip
                    if not os.path.exists(file_to_watch) or \
                            not os.path.exists(event.src_path):
                        return
                    # If we don't care about the file, skip
                    if not os.path.samefile(file_to_watch, event.src_path):
                        return

                # If it's a directory, skip
                if event.is_directory:
                    return

                # If we should ignore the file, skip
                if self.should_ignore(event.src_path):
                    return

                logger.info("Change detected: \"%s\" (%s)" %
                            (event.src_path, event.event_type))

                # Debounce to prevent thrashing
                if scope.timer:
                    scope.timer.cancel()
                    scope.timer = None

                scope.timer = Timer(WATCH_TIMEOUT, rerender)
                scope.timer.start()

            return AllEventsHandler(schedule_rerender)

        dir_handler = make_handler()

        for path in self.watch_paths:
            if os.path.isdir(path):
                self.observer.schedule(
                    dir_handler,
                    os.path.realpath(path), # Watch out for symlinks...
                    recursive=True)
            else:
                # Watch the parent directory for the file pattern
                self.observer.schedule(
                    make_handler(path),
                    os.path.realpath(os.path.dirname(path)),
                    recursive=False)

        self.observer.start()

    def stop_watch(self):
        """
        Stop the file watcher.
        """
        self.observer.stop()

    def join_watch(self):
        """
        Block until the file watcher exits.
        """
        self.observer.join()


def parse_args():
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument('-l',
                        help="""
                        list variable sets.
                        """,
                        dest='list_var_sets',
                        action='store_true',
                        default=False)

    parser.add_argument('-t',
                        help="""
                        template directory.
                        Default: %s
                        """ % ZENBU_TEMPLATES,
                        dest='template_dir',
                        type=str,
                        default=ZENBU_TEMPLATES)

    parser.add_argument('-d',
                        help="""
                        destination directory.
                        Default: %s
                        """ % HOME,
                        dest='dest_dir',
                        type=str,
                        default=HOME)

    parser.add_argument('-s',
                        help="""
                        variable set directory.
                        Default: %s
                        """ % ZENBU_VAR_SETS,
                        dest='var_set_dir',
                        type=str,
                        default=ZENBU_VAR_SETS)

    parser.add_argument('-f',
                        help="""
                        filters file.
                        Default: %s
                        """ % ZENBU_FILTERS,
                        dest='filters_file',
                        type=str,
                        default=ZENBU_FILTERS)

    parser.add_argument('-i',
                        help="""
                        ignores file.
                        Default: %s
                        """ % ZENBU_IGNORES,
                        dest='ignores_file',
                        type=str,
                        default=ZENBU_IGNORES)

    parser.add_argument('-e',
                        help="""
                        whether or not to use environment variables.
                        Default: don't use environment variables
                        """,
                        dest='env_vars',
                        action='store_true',
                        default=False)

    parser.add_argument('-w',
                        help="""
                        start file watcher.
                        """,
                        dest='watch',
                        action='store_true',
                        default=False)

    parser.add_argument('--watch-command',
                        help="""
                        what to execute when a change occurs.
                        Default: Nothing
                        """,
                        type=str,
                        default=None).completer = compgen_completer

    parser.add_argument('--watch-dirs',
                        help="""
                        override what directories to watch, colon-separated.
                        Default: Nothing
                        """,
                        type=str,
                        default=None)

    parser.add_argument('--diff',
                        help="""
                        show diff between template renderings and current
                        destination files
                        """,
                        action='store_true',
                        default=False)

    parser.add_argument('--dry',
                        help="""
                        do a dry run
                        """,
                        action='store_true',
                        default=False)

    parser.add_argument('variable_files',
                        help="additional variable files",
                        nargs='*',
                        type=str).completer = variable_set_completer

    argcomplete.autocomplete(parser, always_complete_options=False)
    return parser.parse_args()

def main():
    args = parse_args()

    # Set up logging
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ColoredFormatter("%(log_color)s%(message)s"))
    logger.addHandler(ch)

    # Defaults on files
    if args.list_var_sets:
        args.variable_files = []
    elif os.path.isfile(ZENBU_DEFAULTS):
        args.variable_files.insert(0, ZENBU_DEFAULTS)
    else:
        logger.warn("Default variables file %s not found. Skipping..."
                    % ZENBU_DEFAULTS)

    if not os.path.isdir(args.var_set_dir):
        logger.warn("Variable sets directory %s not found. Skipping..."
                    % args.var_set_dir)
        args.var_set_dir = None

    if not os.path.isfile(args.filters_file):
        logger.warn("Filters file %s not found. Skipping..."
                    % args.filters_file)
        args.filters_file = None

    if not os.path.isfile(args.ignores_file):
        logger.warn("Ignores file %s not found. Skipping..."
                    % args.ignores_file)
        args.ignores_file = None

    try:
        zenbu = Zenbu(
            args.template_dir,
            args.dest_dir,
            args.var_set_dir,
            args.env_vars,
            args.variable_files,
            args.filters_file,
            args.ignores_file,
            args.watch_command,
            set(args.watch_dirs.split(':')) if args.watch_dirs else None)
    except (NotFoundError, ParseError) as e:
        logger.critical(e)
        sys.exit(1)

    # -l
    if args.list_var_sets:
        try:
            for var_set in zenbu.var_sets:
                print(var_set)
        except ValueError as e:
            logger.critical(e)
            sys.exit(1)

    # --diff
    elif args.diff:
        pipepager(
            ''.join(
                ''.join(
                    diff_colorify(line) for line in diff
                ) for diff in zenbu.diff()
            ),
            cmd='less -R',
        )

    # --dry
    elif args.dry:
        logger.warning("Commencing dry run...")
        for _, dest, _ in zenbu.render():
            logger.info("Successfully dry rendered \"%s\"" % dest)

    # -w
    elif args.watch:
        logger.info("Starting watch...")
        zenbu.watch()
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            zenbu.stop_watch()
        zenbu.join_watch()

    # Default mode: render and write
    else:
        zenbu.render_and_write()

if __name__ == '__main__':
    main()
