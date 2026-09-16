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

The complete [production AI framework](https://github.com/cfollette18/production-ai-framework) is embedded in `agent.system_prompt` as 16 identified, hashed sections. One advisory skill is included and preloaded in the same prompt. No model-callable tools or MCP servers are enabled. Persistent memory injection is disabled; normal Hermes conversation/session behavior applies.

The advisor drafts and reviews architectures, project contracts, evaluation plans, data lifecycle designs, release criteria, and incident procedures. It cites knowledge IDs and identifies unsupported requests. Technical knowledge-only behavior and citation correctness are model instructions, not deterministic semantic guarantees. Native Hermes does not run the former web harness's JSON validator. Operators can change configuration, so the profile is not an immutable security sandbox.

The pack contains implementation guidance inspired by the talk, not an exhaustive transcript or vendor-specific deployment manual. Source provenance and limitations are included in the pack. Public distribution includes no transcript text, credentials, sessions, or customer data.

## Refresh from the knowledge repository

Clone both repositories side by side. With the profile already created, run:

```bash
~/.hermes/hermes-agent/venv/bin/python refresh_profile.py
```

Set `ADVISOR_KNOWLEDGE_ROOT` or `ADVISOR_HERMES_REPO` for different locations. This refreshes the local profile's policy, knowledge, skill, and capability configuration while preserving model settings and credentials. Start a new chat to load changes. Copy the refreshed sanitized config and knowledge pack into this distribution before publishing an update.

## Verification

The native `hermes chat` path was tested for role, knowledge coverage, and handling unsupported cloud-price questions. Runtime tool resolution is checked separately. The installation retains source hashes for reproducibility. AI-generated recommendations still require appropriate review before implementation.
