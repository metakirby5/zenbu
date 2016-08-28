Example
-------

This is an example of a ~/.config/sanpai directory. Stick the contents
of this directory in ~/.config/sanpai and try out the following, observing
what happens to ``~/rendered_Xresources`` each time.

- ``sanpai`` will render with ``defaults.yaml``
- ``sanpai homura`` will render with ``defaults.yaml``, but using the
  colors from ``variable_sets/homura.yaml``
- ``sanpai no_pixel_fonts homura`` will render... you guessed it,
  same as before but with the fonts from
  ``variable_sets/no_pixel_fonts.yaml``
- Notice the last line in ``~/rendered_Xresources``: it's using a filter to
  turn a hex color into an RGB tuple!
- ``sanpai -w --watch-command 'xrdb -merge ~/rendered_Xresources' homura``
  will start a file watcher, so that when any template or variable file
  change would affect rendering, everything is rerendered and
  ``xrdb -merge ~/rendered_Xresources`` is run.

Additional Usage Information (courtesy of `fullsalvo`_)
-------------------------------------------------------

``sanpai`` is a file templater written in python. It uses Jinja2 and YAML as
the base for file templating. This means that when you run it, it'll use
variables you've assigned to fill in fields in other files you've created
templates for. To be exact, sanpai uses the folder
``$HOME/.config/sanpai/templates/`` as a clone of your ``$HOME`` directory.
Files within this folder are rewritten, filling in fields of the form ``{{
variable_name }}`` with what ``variable_name`` has been defined as within yaml
files. This gives you the power to rewrite configuration files on-the-fly then
reload your programs to update apperances almost instantly (or at least that's
how I use sanpai). The standard yaml file referenced is
``$HOME/.config/sanpai/defaults.yaml``. Variations you make should be stored
in ``$HOME/.config/sanpai/variable_sets/`` (which also allows you to nest
folders for better organization).

Let's have an example. Say you want to change your files to a theme in a file
``bright.yaml`` in your ``variable_sets`` directory and you have one file in
your ``templates`` directory, ``.Xresources``. In ``bright.yaml``, contents
might look something like 

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

This is the typical structure for colors used in sanpai. Accessing nested elements can be a hassle, but this is something typically handled from within the ``defaults.yaml`` file with a section for convenience, like

::

    TODO

Anyway, if ``.Xresources`` looks something like

::

    ! Colors
    URxvt.borderColor:  {{ colors.background }}
    URxvt.background:   {{ colors.background }}
    URxvt.foreground:   {{ colors.foreground }}

    ! Black
    URxvt.color0:       {{ colors.black.normal }}
    URxvt.color8:       {{ colors.black.bold }}

    ! Red
    URxvt.color1:       {{ colors.red.normal }}
    URxvt.color9:       {{ colors.red.bold }}

    ! Green
    URxvt.color2:       {{ colors.green.normal }}
    URxvt.color10:      {{ colors.green.bold }}

    ! Yellow
    URxvt.color3:       {{ colors.yellow.normal }}
    URxvt.color11:      {{ colors.yellow.bold }}

    ! Blue
    URxvt.color4:       {{ colors.blue.normal }}
    URxvt.color12:      {{ colors.blue.bold }}

    ! Magenta
    URxvt.color5:       {{ colors.magenta.normal }}
    URxvt.color13:      {{ colors.magenta.bold }}

    ! Cyan
    URxvt.color6:       {{ colors.cyan.normal }}
    URxvt.color14:      {{ colors.cyan.bold }}

    ! White
    URxvt.color7:       {{ colors.white.normal }}
    URxvt.color15:      {{ colors.white.bold }}


Then the ultimately rewritten file from a call of ``sanpai bright`` (sanpai will load from ``defaults.yaml`` unless other yamls are called as arguments by their basename) would be in ``$HOME/.Xresources`` as

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

This process only rewrites the file, however. If you want functionality with reloading like metakirby5 and fullsalvo have, you need to use scripting, like a script in `wz-utils`_ , ``rhisk``. This was designed for ``whizkers``, so you'll need to substitute with ``sanpai`` as necessary.

This example is only the tip of the iceberg of what sanpai can be used for. If you want to understand all its power, start messing around with it yourself! Have fun!

.. _fullsalvo: https://github.com/fullsalvo
.. _wz-utils: https://github.com/fullsalvo/wz-utils
