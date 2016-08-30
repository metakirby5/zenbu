Migrating from whizkers
-----------------------

Most of your existing ``{{ ... }}`` tags should work fine in Jinja, but there
are a few notable exceptions:

- Eval syntax has been deprecated in favor of expressions. This means
  that any variables using ``{` ... `}`` will have to be replaced by an
  equivalent expression. Below is an example:
  ::
    # With the existing variable...
    n_primary_nohash: "{` {{ colors }}[{{ colors }}['primary']]['normal'].lstrip('#') `}"
    # Replace it with...
    n_primary_nohash: "{{ colors[colors.primary]['normal'].lstrip('#') }}"
    # Or even better, make a filter so you can do...
    n_primary_nohash: "{{ colors[colors.primary]['normal'] | nohash }}"
  Note that unlike eval syntax, expressions are not inserted as strings and
  then evaluated. Instead, the type is preserved in the expression. This means
  that any numeric values that are used in an arithmetic expression must not
  be in quotes, or must be cast using a filter like ``{{ x|float / 7 }}``.
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
2. Replace all variables which use eval syntax with the equivalent expression.
   I used the following sed commands in Vim (your mileage may vary):

   - ``s/{{ \([^}]*\) }}/\1/g``
   - ``s/{` \([^`]*\) `}/{{ \1 }}/g``
   - ``s/\['\([^']*\)']/.\1/g``
   - ``s/\["\([^"]*\)"]/.\1/g``
   - ``s/#\([^ ]*\) \([^\/]*\) \/\1/{{ "\2" if \1 else "" }}``
3. Run sanpai. There will likely be errors due to control flow syntax changes.
4. Fix any control flow syntax errors.
5. Repeat from step 4 until there are no errors.
