<!-- Written by Claude, guided by Chris. -->

# `spacepak_ilahp`, in Home Assistant core's layout

This folder is the integration as it would sit in a
[home-assistant/core](https://github.com/home-assistant/core) checkout:

- `homeassistant/components/spacepak_ilahp/`: the integration, requiring the
  published `spacepak-modbus` library
- `tests/components/spacepak_ilahp/`: its tests, written against core's test
  helpers (`tests.common`, `tests.components.diagnostics`)

Copy both into a core checkout at the same paths to run the tests there, or as
the starting point for a core pull request. It is the source the custom
integration in `custom_components/` is generated from.

Before proposing it to core, someone would still need to:

- publish `spacepak-modbus` to PyPI and pin the version in `manifest.json`
- add themselves as a code owner in `manifest.json`
- write the user documentation (home-assistant.io) and brand images
- work through the remaining `todo` rules in `quality_scale.yaml`
- run core's own tooling: `python -m script.hassfest`, `script.translations`,
  and `pytest tests/components/spacepak_ilahp`

Home Assistant's [AI policy](https://developers.home-assistant.io/docs/ai_policy)
applies. This code was written with AI assistance, so whoever submits it needs
to review and understand every line and be able to explain it themselves.
