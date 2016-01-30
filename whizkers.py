#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

"""
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
"""

import collections
import logging
import os
import codecs
import yaml
import re
import argcomplete
from sys import exit, stdout
from subprocess import call, check_output
from threading import Timer
from time import sleep
from difflib import unified_diff
from pydoc import pipepager # Dangerously undocumented...
from argparse import ArgumentParser, RawDescriptionHelpFormatter
from termcolor import colored
from colorlog import ColoredFormatter
from pystache.renderer import Renderer
from pystache.common import MissingTags
from pystache.context import KeyNotFoundError
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Constants
HOME = os.getenv('HOME')
CONFIG_DIR = os.getenv(
    'XDG_CONFIG_HOME',
    os.path.join(HOME, '.config'))
WHIZKERS_ROOT = os.path.join(
    CONFIG_DIR, 'whizkers')
WHIZKERS_DEFAULTS = os.path.join(
    WHIZKERS_ROOT, 'defaults.yaml')
WHIZKERS_VAR_SETS = os.path.join(
    WHIZKERS_ROOT, 'variable_sets')
WHIZKERS_IGNORES = os.path.join(
    WHIZKERS_ROOT, 'ignores.yaml')
WHIZKERS_TEMPLATES = os.path.join(
    WHIZKERS_ROOT, 'templates')
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
        var_sets = Whizker(
            DUMMY,
            DUMMY,
            WHIZKERS_VAR_SETS,
            ignores=WHIZKERS_IGNORES,
        ).var_sets
    except FileNotFoundError as e:
        # Try again with no ignores file
        try:
            var_sets = Whizker(
                DUMMY,
                DUMMY,
                WHIZKERS_VAR_SETS,
            ).var_sets
        except FileNotFoundError as e:
            argcomplete.warn(e)
    except FileParseError as e:
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


class FileNotFoundError(PathException):
    def __str__(self):
        msg = "Was not found: \"%s\"" % self.path
        if self.message:
            msg += "\n    (%s)" % self.message
        return msg


class FileParseError(PathException):
    def __str__(self):
        msg = "Could not parse: \"%s\"" % self.path
        if self.message:
            msg += "\n    (%s)" % self.message
        return msg


class FileRenderError(PathException):
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


class Whizker:
    """
    A template manager.
    """
    def __init__(self,
                 templates_path,
                 dest_path,
                 var_set_path=None,
                 use_env_vars=False,
                 variables=[],
                 ignores=None,
                 watch_command=None):

        self.init_params = locals()             # Save locals for later
        self.watch_paths = set()                # List of paths to watch

        self.renderer = Renderer(
            missing_tags=MissingTags.strict,    # Alert on missing vars
            escape=lambda x: x,                 # Don't escape
        )

        self.observer = Observer()
        self.watch_command = watch_command

        # Check paths
        if os.path.exists(templates_path):
            self.templates_path = templates_path
            self.watch_paths.add(templates_path)
        else:
            raise FileNotFoundError(templates_path, "templates path")

        if os.path.exists(dest_path):
            self.dest_path = dest_path
        else:
            raise FileNotFoundError(dest_path, "destination path")

        if not var_set_path or os.path.exists(var_set_path):
            self.var_set_path = var_set_path
        else:
            raise FileNotFoundError(var_set_path, "variable set path")

        # Initial setup
        self.refresh_variables()

    def refresh_variables(self):
        self.variables = {}             # {variable: value}
        self.ignores = set()            # Set of regexes
        self.variables_rendered = False # Whether or not variables have been
                                        # shallowly rendered

        if self.init_params['use_env_vars']:
            self.variables.update(dict(os.environ))
        for name in self.init_params['variables']:
            self.add_variables(name)
        if self.init_params['ignores']:
            self.add_ignores(self.init_params['ignores'])

    def add_variables(self, name):
        # If it might be just a name...
        if self.var_set_path and not os.path.exists(name):
            name = os.path.join(self.var_set_path, '%s.yaml' % name)

        try:
            with codecs.open(name, 'r', 'utf-8') as f:
                to_merge = yaml.load(f.read())
        except IOError:
            raise FileNotFoundError(name, "variables file")
        except yaml.parser.ParserError as e:
            raise FileParseError(name, e)
        else:
            self.watch_paths.add(name)
            if isinstance(to_merge, dict):
                logger.info("Using \"%s\"..." % name)
                deep_update_dict(self.variables, to_merge)
            else:
                raise FileParseError(name, "not in mapping format")

    def render_variables(self):
        """
        Shallowly resolves variables within variables, then evals
        content in {`...`}
        """
        rendered_variables = {}
        for k, v in iter(self.variables.items()):
            if isinstance(v, str):
                try:
                    v = self.renderer.render(v, self.variables)
                except KeyNotFoundError as e:
                    logger.error(VariableRenderError(k, e))

                # Eval {`...`}
                for expr in re.findall(r'{`.*?`}', v):
                    try:
                        v = v.replace(expr, str(eval(expr[2:-2])))
                    except Exception as e:
                        logger.error(VariableRenderError(k, e))

                rendered_variables[k] = v
        self.variables.update(rendered_variables)
        self.variables_rendered = True

    def add_ignores(self, name):
        try:
            with codecs.open(name, 'r', 'utf-8') as f:
                to_merge = yaml.load(f.read())
        except IOError:
            raise FileNotFoundError(name, "ignores file")
        except yaml.parser.ParserError as e:
            raise FileParseError(e, name)
        else:
            self.watch_paths.add(name)
            if isinstance(to_merge, list):
                self.ignores |= set(re.compile(i) for i in to_merge)
            else:
                raise FileParseError(name, "not in scalar format")

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
            for root, subdirs, files in os.walk(self.var_set_path,
                                                followlinks=True):

                # Don't print the var set dir
                short_root = re.sub(r'^%s/?' % self.var_set_path, '', root)

                for name in files:
                    if not self.should_ignore(name):
                        path = os.path.join(short_root, name)

                        # Yield without .yaml
                        yield re.sub(r'\.%s$' % TEMPLATE_EXT, '', path)
        else:
            raise ValueError("No variable set path to list from.")

    @property
    def render_pairs(self):
        """
        Yield pairs of (template file, destination file)
        """
        for root, subdirs, files in os.walk(self.templates_path,
                                            followlinks=True):

            # Substitute the template dir for home dir
            dest_root = re.sub(r'^%s' % self.templates_path,
                               self.dest_path, root)

            # Iterate through templates
            for name in files:
                if not self.should_ignore(name):
                    template = os.path.join(root, name)
                    dest = os.path.join(dest_root, name)
                    yield (template, dest)

    def render(self):
        """
        Yield tuples of (destination file, mode, what to write).
        If there is a file render error, log it.
        """
        if not self.variables_rendered:
            self.render_variables()
        for template, dest in self.render_pairs:
            try:
                with codecs.open(template, 'r', 'utf-8') as f:
                    yield (dest, os.stat(template).st_mode,
                           self.renderer.render(f.read(), self.variables))
            except KeyNotFoundError as e:
                logger.error(FileRenderError(template, e))
            except IOError as e:
                logger.error(FileNotFoundError(template, e))

    def render_and_write(self):
        for dest, mode, result in self.render():
            # Delete any existing file first
            try:
                os.remove(dest)
            except OSError:
                pass

            with make_dirs_and_open(dest) as f:
                f.write(result)
                os.chmod(dest, mode)
                logger.info("Successfully rendered \"%s\"" % dest)

    def diff(self):
        for dest, mode, result in self.render():
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
                self.refresh_variables()

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
                        """ % WHIZKERS_TEMPLATES,
                        dest='template_dir',
                        type=str,
                        default=WHIZKERS_TEMPLATES)

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
                        """ % WHIZKERS_VAR_SETS,
                        dest='var_set_dir',
                        type=str,
                        default=WHIZKERS_VAR_SETS)

    parser.add_argument('-i',
                        help="""
                        ignores file.
                        Default: %s
                        """ % WHIZKERS_IGNORES,
                        dest='ignores_file',
                        type=str,
                        default=WHIZKERS_IGNORES)

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
    ch = logging.StreamHandler(stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ColoredFormatter("%(log_color)s%(message)s"))
    logger.addHandler(ch)

    # Defaults on files
    if args.list_var_sets:
        args.variable_files = []
    elif os.path.isfile(WHIZKERS_DEFAULTS):
        args.variable_files.insert(0, WHIZKERS_DEFAULTS)
    else:
        logger.warn("Default variables file %s not found. Skipping..."
                    % WHIZKERS_DEFAULTS)

    if not os.path.isfile(args.ignores_file):
        logger.warn("Ignores file %s not found. Skipping..."
                    % args.ignores_file)
        args.ignores_file = None

    try:
        whizker = Whizker(
            args.template_dir,
            args.dest_dir,
            args.var_set_dir,
            args.env_vars,
            args.variable_files,
            args.ignores_file,
            args.watch_command
        )
    except (FileNotFoundError, FileParseError) as e:
        logger.critical(e)
        exit(1)

    if args.list_var_sets:
        try:
            for var_set in whizker.var_sets:
                print(var_set)
        except ValueError as e:
            logger.critical(e)
            exit(1)

    elif args.diff:
        pipepager(
            ''.join(
                ''.join(
                    diff_colorify(line) for line in diff
                ) for diff in whizker.diff()
            ),
            cmd='less -R',
        )

    elif args.dry:
        logger.warning("Commencing dry run...")
        for dest, mode, result in whizker.render():
            logger.info("Successfully dry rendered \"%s\"" % dest)

    elif args.watch:
        logger.info("Starting watch...")
        whizker.watch()
        try:
            while True:
                sleep(1)
        except KeyboardInterrupt:
            whizker.stop_watch()
        whizker.join_watch()

    else:
        whizker.render_and_write()

if __name__ == '__main__':
    main()
