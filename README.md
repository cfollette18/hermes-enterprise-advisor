# Enterprise Advisor — Hermes profile

Maintained by [cfollette18](https://github.com/cfollette18). A dedicated enterprise AI planning advisor using the native Nous Research Hermes CLI.

## Install and chat

```bash
hermes profile install github.com/cfollette18/hermes-enterprise-advisor
hermes profile use enterprise-advisor
hermes setup
hermes chat
```

Configure your own MiniMax credential during setup or in the profile's `.env`, using `.env.EXAMPLE` as a guide. MiniMax-M3 is the configured model; inference uses the cloud API even though Hermes runs locally. Existing local installations already configured with credentials can immediately run `hermes chat`.

No web app or wrapper harness is required. The standard `hermes profile use enterprise-advisor` selection persists across commands.

## Knowledge and capabilities

The complete [production AI framework](https://github.com/cfollette18/production-ai-framework) is embedded in `agent.system_prompt` as 46 stable, identified, hashed records from three talks and the repository's implementation guidance. This includes coordination patterns, versioned state, handoff contracts, circuit breakers, Saga compensation, lexical retrieval with BM25 (k1 and b parameters), agentic search evaluation, and a transcript validation report. One advisory skill is included and preloaded in the same prompt. No model-callable tools or MCP servers are enabled. Persistent memory injection is disabled; normal Hermes conversation/session behavior applies.

The advisor drafts and reviews architectures, project contracts, evaluation plans, data lifecycle designs, release criteria, and incident procedures. It cites knowledge IDs and identifies unsupported requests. Technical knowledge-only behavior and citation correctness are model instructions, not deterministic semantic guarantees. Native Hermes uses conversational output; citation semantics are not automatically verified. Operators can change configuration, so the profile is not an immutable security sandbox.

The pack contains implementation guidance inspired by the talks, not exhaustive transcripts or a vendor-specific deployment manual. Source provenance and limitations are included in the pack. Public distribution includes no transcript text, credentials, sessions, or customer data.

## Refresh from the knowledge repository

To install the snapshot from a checked-out profile repository, with the profile already created, run:

```bash
~/.hermes/hermes-agent/venv/bin/python refresh_profile.py
```

This validates the packaged snapshot and prompt, then refreshes the local profile while preserving model settings, credentials, and sessions. The complete runtime prompt is atomically replaced last. Start a new chat to load changes. Set `ADVISOR_PROFILE_ROOT` or `ADVISOR_HERMES_REPO` for nonstandard locations. The script requires PyYAML (already installed in the local Hermes environment); standalone contributor environments can install requirements.txt.

Maintainers adding knowledge should clone both repositories side by side, review source changes, regenerate and validate the framework exports, and commit the framework first. Then run from this repository:

```bash
~/.hermes/hermes-agent/venv/bin/python refresh_profile.py --package
~/.hermes/hermes-agent/venv/bin/python validate_bundle.py
~/.hermes/hermes-agent/venv/bin/python -m unittest discover -s tests
~/.hermes/hermes-agent/venv/bin/python refresh_profile.py
```

`--package` requires a clean framework checkout, checks its export against the committed file, and updates this repository's pack, prompt, and commit lock together. Set `ADVISOR_KNOWLEDGE_ROOT` for a different framework location. It uses the distribution's config, never the user's private config. Commit these generated distribution changes when publishing the update.

## Autonomous updates and MCP

MCP is an optional future access layer, not an updater or a replacement for Git. A small read-only server could expose framework search, get-by-ID, relationships, and revision metadata. Both that server and this profile should consume the same validated bundle. Keep snapshots pinned for a conversation so a knowledge change cannot silently change its authority halfway through.

For unattended snapshot updates, use an external scheduled job: fetch a reviewed release of this repository, require passing CI, run `validate_bundle.py`, then run `refresh_profile.py`. Retain the previous distribution revision for rollback by reinstalling that version. The package builder checks integrity and commit consistency; it does not determine whether a commit was reviewed. Release selection and approval policy belong to the scheduler/operator. No background job or MCP server is installed by these scripts.

Hermes' native profile updater preserves config.yaml by default. Since this advisor embeds knowledge in that file, copying a new knowledge-pack.json alone leaves old knowledge active. Run the refresh script after acquiring an updated distribution. It preserves local model settings; forcing replacement of the entire config does not provide that same preservation. Existing chats retain their prior context; open a new chat after refresh.

## Verification

The native `hermes chat` path is smoke-tested for knowledge coverage and unsupported requests. Runtime tool resolution is checked separately against the installed Hermes version. CI verifies record hashes, the commit lock format, exact prompt binding to policy/skill/knowledge, and capability settings; regression tests cover stale prompts, enabled tools, tampering, and preservation of local settings. These checks do not prove citation semantics or source truth. AI-generated recommendations still require appropriate review before implementation.

## Relationship to the framework

The framework repository is agent-independent: any agent can read its entry point, attach its text pack, or import its JSON records. This repository is the Hermes-specific adapter. It includes a ready-to-use knowledge snapshot so recipients do not need to clone the framework just to chat. Provider credentials remain user-supplied.

The packaged `knowledge-pack.json` uses the same schema and IDs as the upstream export. `framework-lock.json` identifies the upstream revision and content hash. The complete policy, advisory skill, and reference records are embedded in config.yaml for native CLI startup. Refreshing knowledge requires a new chat to take effect.
