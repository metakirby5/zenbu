Example
=======

This is an example of a ~/.config/whizkers directory. Stick the contents
of this directory in ~/.config/whizkers and try out the following:

-  ``whizkers`` will render with ``defaults.yaml``
-  ``whizkers homura`` will render with ``defaults.yaml``, but using the
   colors from ``variable_sets/homura.yaml``
-  ``whizkers no_pixel_fonts homura`` will render... you guessed it,
   same as before but with the fonts from
   ``variable_sets/no_pixel_fonts.yaml``
-  ``whizkers -w --watch-command 'xrdb -merge ~/rendered_Xresources' homura``
   will start a file watcher, so that when any template or variable file
   change would affect rendering, everything is rerendered and
   ``xrdb -merge ~/.rendered_Xresources`` is run.

Usage Information
=================

whizkers is a file templater written in python. It uses pystache and yaml as the base for file templating. This means that when you run it, it'll use variables you've assigned to fill in fields in other files you've created templates for. To be exact, whizkers uses the folder ``#HOME/.config/whizkers/templates/`` as a clone of your ``$HOME`` directory. Files within this folder are rewritten, filling in fields of the form ``{{ variable_name }}`` with what ``variable_name`` has been defined as within yaml files. This gives you the power to rewrite configuration files on-the-fly then reload your programs to update apperances almost instantly (or at least that's how I use whizkers). The standard yaml file referenced is ``$HOME/.config/whizkers/defaults.yaml``. Variations you make should be stored in ``$HOME/.config/whizkers/variable_sets/`` (which also allows you to nest folders for better organization).

Let's have an example. Say you want to change your files to a theme in a file ``bright.yaml`` in your ``variable_sets`` directory and you have one file in your ``templates`` directory, ``.Xresources``. In ``bright.yaml``, contents might look something like

::

    colors:
      primary:        "red"
      secondary:      "cyan"
      background:     "#F1F2E0"
      foreground:     "#695F6C"
      cursor:         "#695F6C"
      black:
        normal:       "#695F6C"
        bold:         "#A5B9C4"
      red:
        normal:       "#A75D4d"
        bold:         "#A75D4d"
      green:
        normal:       "#A4D485"
        bold:         "#A4D485"
      yellow:
        normal:       "#FDD485"
        bold:         "#FDD485"
      blue:
        normal:       "#90AABE"
        bold:         "#90AABE"
      magenta:
        normal:       "#B17FBC"
        bold:         "#B17FBC"
      cyan:
        normal:       "#6BD6E3"
        bold:         "#6BD6E3"
      white:
        normal:       "#A5B9C4"
        bold:         "#F1F2E0"

This is the typical structure for colors used in whizkers. Accessing elements with this can be tricky, but this is something typically handled from within the ``defaults.yaml`` file with a section for convenience, like

::

    bgc:        "{` {{ colors }}['background'] `}"
    fgc:        "{` {{ colors }}['foreground'] `}"
    csc:        "{` {{ colors }}['cursor'] `}"

    n_black:    "{` {{ colors }}['black']['normal'] `}"
    b_black:    "{` {{ colors }}['black']['bold'] `}"
    n_red:      "{` {{ colors }}['red']['normal'] `}"
    b_red:      "{` {{ colors }}['red']['bold'] `}"
    n_green:    "{` {{ colors }}['green']['normal'] `}"
    b_green:    "{` {{ colors }}['green']['bold'] `}"
    n_yellow:   "{` {{ colors }}['yellow']['normal'] `}"
    b_yellow:   "{` {{ colors }}['yellow']['bold'] `}"
    n_blue:     "{` {{ colors }}['blue']['normal'] `}"
    b_blue:     "{` {{ colors }}['blue']['bold'] `}"
    n_magenta:  "{` {{ colors }}['magenta']['normal'] `}"
    b_magenta:  "{` {{ colors }}['magenta']['bold'] `}"
    n_cyan:     "{` {{ colors }}['cyan']['normal'] `}"
    b_cyan:     "{` {{ colors }}['cyan']['bold'] `}"
    n_white:    "{` {{ colors }}['white']['normal'] `}"
    b_white:    "{` {{ colors }}['white']['bold'] `}"

    n_primary:  "{` {{ colors }}[{{ colors }}['primary']]['normal'] `}"
    b_primary:  "{` {{ colors }}[{{ colors }}['primary']]['bold'] `}"
    n_secondary:  "{` {{ colors }}[{{ colors }}['secondary']]['normal'] `}"
    b_secondary:  "{` {{ colors }}[{{ colors }}['secondary']]['bold'] `}"

Anyway, if ``.Xresources`` looks something like

::

    ! Colors
    *.borderColor:  {{ bgc }}
    *.background:   {{ bgc }}
    *.foreground:   {{ fgc }}
    *.cursorColor:  {{ csc }}

    ! Black
    *.color0:       {{ n_black }}
    *.color8:       {{ b_black }}

    ! Red
    *.color1:       {{ n_red }}
    *.color9:       {{ b_red }}

    ! Green
    *.color2:       {{ n_green }}
    *.color10:      {{ b_green }}

    ! Yellow
    *.color3:       {{ n_yellow }}
    *.color11:      {{ b_yellow }}

    ! Blue
    *.color4:       {{ n_blue }}
    *.color12:      {{ b_blue }}

    ! Magenta
    *.color5:       {{ n_magenta }}
    *.color13:      {{ b_magenta }}

    ! Cyan
    *.color6:       {{ n_cyan }}
    *.color14:      {{ b_cyan }}

    ! White
    *.color7:       {{ n_white }}
    *.color15:      {{ b_white }}

Then the ultimately rewritten file from a call of ``whizkers bright`` (whizkers will load from ``defaults.yaml`` unless other yamls are called as arguments by their basename) would be in ``$HOME/.Xresources`` as

::

    ! Colors
    *.borderColor:  #F1F2E0
    *.background:   #F1F2E0
    *.foreground:   #695F6C
    *.cursorColor:  #695F6C

    ! Black
    *.color0:       #695F6C
    *.color8:       #A5B9C4

    ! Red
    *.color1:       #A75D4d
    *.color9:       #A75D4d

    ! Green
    *.color2:       #A4D485
    *.color10:      #A4D485

    ! Yellow
    *.color3:       #FDD485
    *.color11:      #FDD485

    ! Blue
    *.color4:       #90AABE
    *.color12:      #90AABE

    ! Magenta
    *.color5:       #B17FBC
    *.color13:      #B17FBC

    ! Cyan
    *.color6:       #6BD6E3
    *.color14:      #6BD6E3

    ! White
    *.color7:       #A5B9C4
    *.color15:      #F1F2E0

This process only rewrites the file, however. If you want functionality with reloading like metakirby5 and I have, you need to use scripting, like a script in `wz-utils`_ , ``rhisk``.

.. _wz-utils: https://github.com/fullsalvo/wz-utils
