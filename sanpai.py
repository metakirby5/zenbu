#!/usr/bin/env python
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

"""
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

For help on designing templates, refer to
http://jinja.pocoo.org/docs/dev/templates/
"""

import collections
import logging
import os
import sys
import codecs
import yaml
import re
import argcomplete
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
SANPAI_ROOT = os.path.join(
    CONFIG_DIR, 'sanpai')
SANPAI_DEFAULTS = os.path.join(
    SANPAI_ROOT, 'defaults.yaml')
SANPAI_VAR_SETS = os.path.join(
    SANPAI_ROOT, 'variable_sets')
SANPAI_FILTERS = os.path.join(
    SANPAI_ROOT, 'filters.py')
SANPAI_IGNORES = os.path.join(
    SANPAI_ROOT, 'ignores.yaml')
SANPAI_TEMPLATES = os.path.join(
    SANPAI_ROOT, 'templates')
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
        var_sets = Sanpai(
            DUMMY,
            DUMMY,
            SANPAI_VAR_SETS,
            ignores=SANPAI_IGNORES,
        ).var_sets
    except NotFoundError as e:
        # Try again with no ignores file
        try:
            var_sets = Sanpai(
                DUMMY,
                DUMMY,
                SANPAI_VAR_SETS,
            ).var_sets
        except NotFoundError as e:
            argcomplete.warn(e)
    except ParseError as e:
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
        return colored(line.encode('utf-8'), attrs=['bold'])
    elif re.match(r'^\+', line):
        return colored(line.encode('utf-8'), 'green')
    elif re.match(r'^-', line):
        return colored(line.encode('utf-8'), 'red')
    elif re.match(r'^\?', line):
        return colored(line.encode('utf-8'), 'yellow')
    else:
        return line.encode('utf-8')

def deep_update_dict(d, u):
    for k, v in iter(u.items()):
        if isinstance(d, collections.Mapping):
            if isinstance(v, collections.Mapping):
                r = deep_update_dict(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        else:
            d = {k: u[k]}
    return d

def deep_iter_empty(l):
    return hasattr(l, '__iter__') and all(map(deep_iter_empty, l))


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
            msg += "\n    (%s)" % self.message
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


class Sanpai:
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
                 ignores=None,
                 watch_command=None):

        variables = variables or []             # PyLint W0102
        self.init_params = locals()             # Save locals for later
        self.watch_paths = set()                # List of paths to watch

        # Check paths
        if os.path.exists(templates_path):
            self.templates_path = templates_path
            self.watch_paths.add(templates_path)
            self.templates_path_re = re.compile(
                '^{}/?'.format(templates_path))
        else:
            raise NotFoundError(templates_path, "templates path")

        if os.path.exists(dest_path):
            self.dest_path = dest_path
        else:
            raise NotFoundError(dest_path, "destination path")

        if not var_set_path or os.path.exists(var_set_path):
            self.var_set_path = var_set_path
            self.var_set_path_re = re.compile(
                '^{}/?'.format(var_set_path or ''))
        else:
            raise NotFoundError(var_set_path, "variable set path")

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

        # Filters
        if filters_path:
            if os.path.exists(filters_path):
                sys.path.append(os.path.dirname(filters_path))
                self.filters_module = os.path.splitext(
                    os.path.basename(filters_path))[0]
            else:
                raise NotFoundError(var_set_path, "variable set path")
        else:
            self.filters_module = None

        # Initial setup
        self.refresh()

    def refresh(self):
        # Get ignores
        self.ignores = set()
        if self.init_params['ignores']:
            self.add_ignores(self.init_params['ignores'])

        # Get variables
        self.env.globals = self.defaults['globals'].copy()
        if self.init_params['use_env_vars']:
            self.env.globals.update(dict(os.environ))
        for name in self.init_params['variables']:
            self.add_variables(name)

        # Get filters
        self.env.filters = self.defaults['filters'].copy()
        if self.filters_module:
            try:
                deep_update_dict(
                    self.env.filters,
                    vars(import_module(self.filters_module)))
            except ImportError:
                pass

    def add_variables(self, name):
        # If it might be just a name...
        if self.var_set_path and not os.path.exists(name):
            name = os.path.join(self.var_set_path, '{}.{}'.format(
                name, TEMPLATE_EXT))

        try:
            with codecs.open(name, 'r', 'utf-8') as f:
                to_merge = yaml.load(f.read())
        except IOError:
            raise NotFoundError(name, "variables file")
        except yaml.parser.ParserError as e:
            raise ParseError(name, e)
        else:
            self.watch_paths.add(name)
            if isinstance(to_merge, dict):
                logger.info("Using \"%s\"..." % name)
                deep_update_dict(self.env.globals, to_merge)
            else:
                raise ParseError(name, "not in mapping format")

    def add_ignores(self, name):
        try:
            with codecs.open(name, 'r', 'utf-8') as f:
                to_merge = yaml.load(f.read())
        except IOError:
            raise NotFoundError(name, "ignores file")
        except yaml.parser.ParserError as e:
            raise ParseError(e, name)
        else:
            self.watch_paths.add(name)
            if isinstance(to_merge, list):
                self.ignores |= set(re.compile(i) for i in to_merge)
            else:
                raise ParseError(name, "not in scalar format")

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
            except (TemplateSyntaxError, UndefinedError) as e:
                logger.error(RenderError(template, e))
            except TemplateNotFound as e:
                logger.error(NotFoundError(template, e))

    def render_and_write(self):
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
        # Because of read-only closures
        scope = Scope()
        scope.timer = None

        def make_handler(file_to_watch=None):
            def rerender():
                logger.info("\nRe-rendering...")
                self.refresh()

                # If there is no resulting difference, skip
                if deep_iter_empty(self.diff()):
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

                logger.info("\nChange detected: \"%s\" (%s)" %
                            (event.src_path, event.event_type))

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
        self.observer.stop()

    def join_watch(self):
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
                        """ % SANPAI_TEMPLATES,
                        dest='template_dir',
                        type=str,
                        default=SANPAI_TEMPLATES)

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
                        """ % SANPAI_VAR_SETS,
                        dest='var_set_dir',
                        type=str,
                        default=SANPAI_VAR_SETS)

    parser.add_argument('-f',
                        help="""
                        filters file.
                        Default: %s
                        """ % SANPAI_FILTERS,
                        dest='filters',
                        type=str,
                        default=SANPAI_FILTERS)

    parser.add_argument('-i',
                        help="""
                        ignores file.
                        Default: %s
                        """ % SANPAI_IGNORES,
                        dest='ignores_file',
                        type=str,
                        default=SANPAI_IGNORES)

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
    elif os.path.isfile(SANPAI_DEFAULTS):
        args.variable_files.insert(0, SANPAI_DEFAULTS)
    else:
        logger.warn("Default variables file %s not found. Skipping..."
                    % SANPAI_DEFAULTS)

    if not os.path.isfile(args.ignores_file):
        logger.warn("Ignores file %s not found. Skipping..."
                    % args.ignores_file)
        args.ignores_file = None

    try:
        sanpai = Sanpai(
            args.template_dir,
            args.dest_dir,
            args.var_set_dir,
            args.env_vars,
            args.variable_files,
            args.filters,
            args.ignores_file,
            args.watch_command
        )
    except (NotFoundError, ParseError) as e:
        logger.critical(e)
        sys.exit(1)

    if args.list_var_sets:
        try:
            for var_set in sanpai.var_sets:
                print(var_set)
        except ValueError as e:
            logger.critical(e)
            sys.exit(1)

    elif args.diff:
        pipepager(
            ''.join(
                ''.join(
                    diff_colorify(line) for line in diff
                ) for diff in sanpai.diff()
            ),
            cmd='less -R',
        )

    elif args.dry:
        logger.warning("Commencing dry run...")
        for _, dest, _ in sanpai.render():
            logger.info("Successfully dry rendered \"%s\"" % dest)

    elif args.watch:
        logger.info("Starting watch...")
        sanpai.watch()
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            sanpai.stop_watch()
        sanpai.join_watch()

    else:
        sanpai.render_and_write()

if __name__ == '__main__':
    main()
