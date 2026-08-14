"""Package init doubles as the vnstock agent-write guard.

Importing vnstock runs `setup_agent(async_mode=True)` at module scope
(vnstock/__init__.py), which writes vendor "AI agent instruction" files into the
user's home directory — ~/.cursorrules, ~/.windsurfrules, ~/.clinerules,
~/.clauderc, ~/.github/copilot-instructions.md, ~/.gemini/config/AGENTS.md —
plus AGENTS.md in the project root, with no prompt and no opt-out flag.

Verified against a throwaway HOME: unguarded import wrote 7 files, guarded
import wrote 0, and data fetching was unaffected.

The real work happens in the bundled `vnai` package, which vnstock imports
lazily inside init_agent_environment(). Importing vnai here and replacing the
two entry points with no-ops means the lazy import resolves to ours.

This runs before data_provider.vnstock_fetcher is loaded, which is why it lives
in __init__ rather than in the fetcher module.
"""

import vnai


def _noop_setup(*_args, **_kwargs) -> bool:
    return True


def _noop_async_setup(*_args, **_kwargs) -> None:
    return None


# Marker the guard test asserts on, so removing the guard fails the suite.
_noop_setup._dsa_vn_noop = True
_noop_async_setup._dsa_vn_noop = True

vnai.setup_agent_environment = _noop_setup
vnai.async_setup_agent_environment = _noop_async_setup
