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
