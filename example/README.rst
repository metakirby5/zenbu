Example
=======

This is an example of a ~/.config/whizkers directory. Stick this
directory in ~/.config/whizkers and try out the following:

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

Have fun!
