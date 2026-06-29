"""hive_codegen — generate PyHive's typed core layer from Hive's OpenAPI spec.

The tool produces the *generated layer* (``pyhive/src/types/_generated/``):

- ``enums.py``   — every spec enum as a PyHive-style ``str``/``IntEnum``.
- ``models.py``  — a Pydantic base class per real entity schema.
- ``manifest.json`` — a machine record of schemas, fields, enums and endpoints
  used as the drift-detection contract between releases.

The curated ergonomic layer (``pyhive/src/types/<resource>.py``) subclasses the
generated bases and adds the ``hive_client`` injection, lazy relations and
convenience methods. Generation never touches the curated layer.
"""

from .config import Config, load_config

__all__ = ["Config", "load_config"]
