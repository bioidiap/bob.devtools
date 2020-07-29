# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import copy
import json
import os
import sys

from collections import defaultdict
from os.path import isdir
from os.path import join

import requests
import tqdm

from packaging.version import parse as parse_version

BASE_URL = "http://www.idiap.ch/software/bob/conda"
SUBDIRS = (
    "noarch",
    "linux-64",
    "osx-64",
)

REMOVALS = {"osx-64": {}, "linux-64": {}, "noarch": {}}

OPERATORS = ["==", ">=", "<=", ">", "<", "!="]


def _gen_patch_instructions(index, new_index, packages_key):
    instructions = {
        "patch_instructions_version": 1,
        packages_key: defaultdict(dict),
        "revoke": [],
        "remove": [],
    }

    # diff all items in the index and put any differences in the instructions
    for fn in index:
        assert fn in new_index

        # replace any old keys
        for key in index[fn]:
            assert key in new_index[fn], (key, index[fn], new_index[fn])
            if index[fn][key] != new_index[fn][key]:
                instructions[packages_key][fn][key] = new_index[fn][key]

        # add any new keys
        for key in new_index[fn]:
            if key not in index[fn]:
                instructions[packages_key][fn][key] = new_index[fn][key]

    return instructions


def _gen_new_index(repodata, packages_key):
    """Make any changes to the index by adjusting the values directly.

    This function returns the new index with the adjustments.
    Finally, the new and old indices are then diff'ed to produce the repo
    data patches.
    """
    index = copy.deepcopy(repodata[packages_key])

    for fn, record in index.items():
        record_name = record["name"]

        # bob.bio.base <=4.1.0 does not work with numpy >=1.18
        if record_name == "bob.bio.base":
            if parse_version(record["version"]) <= parse_version("4.1.0"):
                record["depends"].append("numpy <1.18")

    return index


def gen_new_index_and_patch_instructions(repodata):
    instructions = {}
    for i, packages_key in enumerate(["packages", "packages.conda"]):
        new_index = _gen_new_index(repodata, packages_key)
        inst = _gen_patch_instructions(repodata[packages_key], new_index, packages_key)
        if i == 0:
            instructions.update(inst)
        else:
            instructions[packages_key] = inst[packages_key]
            instructions["revoke"] = list(
                set(instructions["revoke"]) | set(inst["revoke"])
            )
            instructions["remove"] = list(
                set(instructions["remove"]) | set(inst["remove"])
            )

    return instructions


def main():
    # Step 1. Collect initial repodata for all subdirs.
    repodatas = {}
    subdirs = SUBDIRS
    for subdir in tqdm.tqdm(subdirs, desc="Downloading repodata"):
        repodata_url = "/".join((BASE_URL, subdir, "repodata_from_packages.json"))
        response = requests.get(repodata_url)
        response.raise_for_status()
        repodatas[subdir] = response.json()

    # Step 2. Create all patch instructions.
    prefix_dir = os.getenv("PREFIX", "tmp")
    for subdir in subdirs:
        prefix_subdir = join(prefix_dir, subdir)
        if not isdir(prefix_subdir):
            os.makedirs(prefix_subdir)

        # Step 2a. Generate a new index.
        # Step 2b. Generate the instructions by diff'ing the indices.
        instructions = gen_new_index_and_patch_instructions(repodatas[subdir])

        # Step 2c. Output this to $PREFIX so that we bundle the JSON files.
        patch_instructions_path = join(prefix_subdir, "patch_instructions.json")
        with open(patch_instructions_path, "w") as fh:
            json.dump(
                instructions, fh, indent=2, sort_keys=True, separators=(",", ": ")
            )


if __name__ == "__main__":
    sys.exit(main())
