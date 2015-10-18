# whizkers
Pystache + YAML based config templater.

# Dependencies
- pystache
- PyYAML
- termcolor

# Usage
```
usage: whizkers [-h] [-l] [-t TEMPLATE_DIR] [-d DEST_DIR] [-i IGNORES_FILE]
                [variable_files [variable_files ...]]

A pystache + YAML based config templater. Searches for a yaml file with a
variable mapping in ~/.config/whizkers/variables.yaml, a yaml file with an
ignore sequence in (by default) ~/.config/whizkers/ignores.yaml, and uses the
templates in (by default) ~/.config/whizkers/templates/ to render into your
home directory (by default). Additional variable files can be applied by
supplying them as arguments, in order of application. They can either be paths
or, if located in ~/.config/whizkers/variable_sets/, extension-less filenames.

positional arguments:
  variable_files   additional variable files

optional arguments:
  -h, --help       show this help message and exit
  -l               list variable sets.
  -t TEMPLATE_DIR  template directory. Default:
                   /home/echan/.config/whizkers/templates
  -d DEST_DIR      destination directory. Default: /home/echan
  -i IGNORES_FILE  ignores file. Default:
                   /home/echan/.config/whizkers/ignores.yaml
```

# Thanks to
- https://gist.github.com/coleifer/33484bff21c34644dae1
- https://github.com/defunkt/pystache
- http://pyyaml.org/
