"""The guard in data_provider/__init__.py must neutralize vnstock's
import-time agent-file writes. Verified live: unguarded import writes 7 files
into the user's home directory."""

import vnai

import data_provider  # noqa: F401 - importing it installs the guard


def test_guard_neutralizes_vnai_agent_setup():
    for name in ("setup_agent_environment", "async_setup_agent_environment"):
        fn = getattr(vnai, name)
        assert getattr(fn, "_dsa_vn_noop", False), (
            f"vnai.{name} is not the no-op guard — importing vnstock will write "
            "AI-agent instruction files into the user's home directory"
        )


def test_guard_functions_are_harmless_when_called():
    assert vnai.setup_agent_environment("/tmp/should-not-be-written") is True
    assert vnai.async_setup_agent_environment("/tmp/should-not-be-written") is None
