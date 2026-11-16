# Tutorial: build the Jev example networks with Octoloom

This tutorial shows how to build the two example agent networks in [`examples/`](../../examples) step by step in **Octoloom for Agent Fabric** (the VS Code extension). Both networks use the Jev OpenAI wrapper as their LLM. At the end you deploy each network and chat with it.

| Chapter | Network | Style | What you learn |
| --- | --- | --- | --- |
| [1. Library Loans](01-v1-library-loans.md) | `v1-library-loans` | Probabilistic Network (Agent Network 1.0, A2A 0.3.0) | An LLM broker that picks MCP tools and A2A agents from its instructions |
| [2. Restaurant Booking](02-v2-restaurant-booking.md) | `v2-restaurant-booking` | Deterministic Network (Agent Network 2.0, AgentScript, A2A 1.0) | A broker whose steps are an AgentScript flow (trigger, orchestrator, reply) |

Each chapter builds the same project you find in `examples/`. You can compare your result with that folder at any time, or open the finished example directly and skip the building.

## Before you start

You need:

1. **The Jev wrapper running**, version 1.0.1 or later (v2 brokers need `/v1/responses`). See the [main README](../../README.md) to build and deploy it. Note two things:
   - its public URL, for example `https://<wrapper-app>.<id>.usa-e2.cloudhub.io`
   - its caller key `wrapper.apiKey` (a secret: keep it in an environment variable, never in a file)
2. **VS Code with Octoloom for Agent Fabric** installed.
3. **`anypoint-cli-v4`** with the `agent-network` plugin, logged in to your Anypoint organization. Octoloom runs it for you on build and deploy.
4. **An Agent Fabric gateway** in your environment. You need its name and its public URL.
5. **Your organization id.** Each project's `exchange.json` uses it as `groupId`. The examples have the placeholder `<enter-your-org-id>`, and the build fails until you replace it.

The MCP servers and the agents in both networks are public **A2D mocks**. They need no account and return fixed test data, so the results in this tutorial are the same for you.

## How the pieces fit

```
you (Octoloom chat)
   │  A2A
   ▼
Agent Fabric gateway ──► broker (v1 LLM broker or v2 AgentScript broker)
                            │  OpenAI API (/v1/chat/completions or /v1/responses)
                            ├──► Jev OpenAI wrapper ──► Jev decides the tool, gpt-4o-mini writes the text
                            ├──► MCP server (A2D mock)
                            └──► A2A agents (A2D mocks)
```

The broker sees the wrapper as an ordinary **OpenAI** LLM provider. Jev decides which tool or agent comes next, so every wrapper response has an `x-jev-decision` header and the wrapper logs list each decision.

## About the screenshots

The screenshots were made with Octoloom's screenshot harness, in the dark theme. Your gateway name, URLs and organization will be different. The gateway in the pictures is called `my-gateway`. The chat replies are real answers from the deployed examples (wrapper 1.2.0, tested 2026-11-16).

A small round **i** button sits at the bottom right of every Octoloom view. It opens the **Explain** panel for whatever you are looking at. Use it whenever a field is unclear.

## Troubleshooting

| What you see | Why | What to do |
| --- | --- | --- |
| Build fails on `groupId` | `exchange.json` still has `<enter-your-org-id>` | Put your organization id there |
| Every chat reply fails with 401 "No API key" | The broker sends no or a wrong `jev.apiKey`, or the wrapper lost its secure properties | Deploy again with the right key. When you update the wrapper with `runtime-mgr ... modify`, pass both `--secureProperty` values again |
| v2 broker keeps restarting | The wrapper is older than 1.0.1, so it has no `/v1/responses` | Update the wrapper |
| Deploy fails with 409 | Connection keys must be unique in an environment | Rename the `jev_lib1_` / `jev_rb2_` prefix before deploying a second copy |
| Deploy fails with 429 | Several deploys ran at the same time | Deploy one network at a time |
| v1 chat: connection reset | The v1 runtime resets on large numeric JSON-RPC ids | Send the `id` as a string (Octoloom already does) |
| v2 deploy uses old values | An old `target/` build is still there | Delete `target/` and build again |
| The reply wording differs from this tutorial | The brokers are probabilistic | The ids and numbers come from the mocks and stay the same |

## Regenerating the screenshots

[`tools/make-specs.py`](tools/make-specs.py) writes the screenshot specs from the example files. Run it from an Octoloom checkout:

```bash
python3 <this-repo>/docs/tutorial/tools/make-specs.py <this-repo> /tmp/jevtut/specs
OUT=/tmp/jevtut/shots node .claude/skills/octoloom-screenshot/shot.mjs /tmp/jevtut/specs/*.json
```
