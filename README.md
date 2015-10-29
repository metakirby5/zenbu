# whizkers
Pystache + YAML based config templater.

# Dependencies
- pystache
- PyYAML
- termcolor
- colorlog

# Usage
```
usage: whizkers [-h] [-l] [-t TEMPLATE_DIR] [-d DEST_DIR] [-s VAR_SET_DIR]
                [-i IGNORES_FILE] [-e] [--diff]
                [variable_files [variable_files ...]]

A pystache + YAML based config templater. Searches for an optional yaml file
with a variable mapping in ~/.config/whizkers/variables.yaml, an optional yaml
file with an ignore scalar in (by default) ~/.config/whizkers/ignores.yaml,
and uses the templates in (by default) ~/.config/whizkers/templates/ to render
into your home directory (by default). Additional variable files can be
applied by supplying them as arguments, in order of application. They can
either be paths or, if located in (by default)
~/.config/whizkers/variable_sets/, extension-less filenames. Environment
variable support is available; simply put the name of the variable in mustache
brackets. Finally, diffs between the current destination files and template
renderings are available via command-line flag.

positional arguments:
  variable_files   additional variable files

optional arguments:
  -h, --help       show this help message and exit
  -l               list variable sets.
  -t TEMPLATE_DIR  template directory. Default:
                   /home/echan/.config/whizkers/templates
  -d DEST_DIR      destination directory. Default: /home/echan
  -s VAR_SET_DIR   variable set directory. Default:
                   /home/echan/.config/whizkers/variable_sets
  -i IGNORES_FILE  ignores file. Default:
                   /home/echan/.config/whizkers/ignores.yaml
  -e               whether or not to use environment variables. Default: don't
                   use environment variables
  --diff           show diff between template renderings and current
                   destination files
```

# Thanks to
- https://gist.github.com/coleifer/33484bff21c34644dae1
- https://github.com/defunkt/pystache
- http://pyyaml.org/
