<!-- Written by Claude, guided by Chris. -->

# Contributing

This is a reference implementation, not an actively maintained package, so
there is no promise anyone will review a pull request. Forking is the most
reliable way to make a change stick.

If you do open a pull request:

1. Make the change in `core/` (or in
   [spacepak-modbus](https://github.com/cwm12345/spacepak-modbus) for the
   register map), not in `custom_components/` directly.
2. Regenerate the custom integration with `scripts/vendor.py`, then run
   `scripts/lint` and `python -m pytest`.

Contributions are released under the same [Unlicense](LICENSE) as the rest of
the project.
