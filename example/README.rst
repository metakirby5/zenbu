Example
-------

This is an example of a ~/.config/zenbu directory. Stick the contents
of this directory in ~/.config/zenbu and try out the following, observing
what happens to ``~/rendered_Xresources`` each time.

- ``zenbu`` will render with ``defaults.yaml``
- ``zenbu homura`` will render with ``defaults.yaml``, but using the
  colors from ``variable_sets/homura.yaml``
- ``zenbu no_pixel_fonts homura`` will render... you guessed it,
  same as before but with the fonts from
  ``variable_sets/no_pixel_fonts.yaml``
- Notice the last line in ``~/rendered_Xresources``: it's using a filter to
  turn a hex color into an RGB tuple!
- ``zenbu -w --watch-command 'xrdb -merge ~/rendered_Xresources' homura``
  will start a file watcher, so that when any template or variable file
  change would affect rendering, everything is rerendered and
  ``xrdb -merge ~/rendered_Xresources`` is run.
