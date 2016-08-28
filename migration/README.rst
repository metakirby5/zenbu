Migrating from whizkers
-----------------------

Most of your existing ``{{ ... }}`` tags should work fine in Jinja, but there
are a few notable exceptions:

- Shallow evaluation has been deprecated in favor of expressions. This means
  that any variables using ``{` ... `}`` will have to be replaced by an
  equivalent expression. Below is an example:
  ::
    # With the existing variable...
    n_primary_nohash: "{` {{ colors }}[{{ colors }}['primary']]['normal'].lstrip('#') `}"
    # You have to get rid of this, and change all instances of...
    {{ n_primary_nohash }}
    # To the following...
    {{ colors[colors.primary]['normal'].lstrip('#') }}
    # Or even better, make a filter so you can do...
    {{ colors[colors.primary]['normal'] | nohash }}
- Control flow syntax has changed, so you will need to update accordingly.
  Below is an example:
  ::
    # With the existing line...
    URxvt.boldFont:  {{ #term_fonts }}xft:{{ . }}{{ #use_bold }}:bold{{ /use_bold }}:pixelsize={{ pixelsize }}:antialias=true:hinting=true,{{ /term_fonts }}
    # Change it to...
    URxvt.boldfont: {% for f in term_fonts -%}
      xft:{{ f }}{{
        ':bold' if use_bold else ''
      }}:pixelsize={{ pixelsize }}:antialias=true:hinting=true,
    {%- endfor %}

I've found this procedure to be the best way to migrate:

1. Copy ``~/.config/whizkers`` to ``~/.config/sanpai``.
2. Remove all variables which use shallow evaluation.
3. Use a ``sed`` command to substitute all the variables you just removed with
   the expression equivalents.
4. Run sanpai. There will likely be errors due to control flow syntax changes.
5. Fix any control flow syntax errors.
6. Repeat from step 4 until there are no errors.

A script to automate this process is in the works.
