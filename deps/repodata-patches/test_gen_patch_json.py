from gen_patch_json import REMOVALS
from gen_patch_json import _gen_patch_instructions


def test_gen_patch_instructions():
    index = {
        "a": {"depends": ["c", "d"], "features": "d"},
        "b": {"nane": "blah"},
        "c": {},
    }

    new_index = {
        "a": {"depends": ["c", "d", "e"], "features": None},
        "b": {"nane": "blah"},
        "c": {"addthis": "yes"},
    }

    inst = _gen_patch_instructions(index, new_index, "packages")
    assert inst["patch_instructions_version"] == 1
    assert "revoke" in inst
    assert "remove" in inst
    assert "packages" in inst

    assert inst["packages"] == {
        "a": {"depends": ["c", "d", "e"], "features": None},
        "c": {"addthis": "yes"},
    }

    assert set(REMOVALS["osx-64"]) <= set(inst["remove"])
