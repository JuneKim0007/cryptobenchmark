"""The catalogue read tools: thin wrappers over lib/cryptobench/cryptobench/catalogue/views.py and lib/cryptobench/cryptobench/catalogue/glossary.py; text out, never a file."""
from __future__ import annotations

import json

from cryptobench.catalogue.glossary import what_is
from cryptobench.catalogue.views import get_group, list_groups, view_for
from ...stop.halt import Coded
from .tool import READ, Context, Outcome, Tool, args_schema

TEXT = {"type": "string"}


def _read(fn):
    def run(args: dict, _ctx: Context) -> Outcome:
        try:
            return Outcome(True, json.dumps(fn(**args), sort_keys=True, default=str))
        except Coded as e:
            return Outcome(False, str(e))
    return run


VIEW_FOR = Tool("view_for", "one catalogue entry, as one provider build sees it when provider is given",
                args_schema({"identifier": TEXT, "provider": TEXT}, ("identifier",)), READ, _read(view_for))
WHAT_IS = Tool("what_is", "a glossary term or section by its dotted path; with value, that value's one meaning",
               args_schema({"path": TEXT, "value": TEXT}, ("path",)), READ, _read(what_is))
LIST_GROUPS = Tool("list_groups", "every catalogue group: id, description, exemplars", args_schema({}), READ,
                   _read(list_groups))
GET_GROUP = Tool("get_group", "one page of a group's member ids after `after`, and how many remain",
                 args_schema({"group": TEXT, "items": {"type": "integer"}, "after": TEXT}, ("group",)), READ, _read(get_group))
CATALOGUE_READS = (VIEW_FOR, WHAT_IS, LIST_GROUPS, GET_GROUP)
