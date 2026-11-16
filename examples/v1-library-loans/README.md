# Jev Library Loans (v1)

A library member asks for a book. The broker searches the catalog and places a hold when the book is out. Its LLM is the **Jev OpenAI wrapper** (the Mule app in this repo), so Jev decides each tool call and `openai/gpt-4o-mini` writes the text.

- Style: Agent Network 1.0 (`schemaVersion: 1.0.0`), broker card A2A 0.3.0
- Broker: `jev_lib1_library-broker`
- MCP server: Library Catalog MCP (`search_books`, `place_hold`)
- Agents: Library Membership Agent, Book Recommendation Agent (both A2A 0.3.0)
- LLM: `jev_lib1_jev`, an OpenAI-type provider whose URL is the wrapper (`${jevWrapper.url}`)

The MCP server and the agents are public A2D mocks, so the network needs no other system. No credentials are stored in this project.

## Before you deploy

1. The Jev wrapper must be running (see the [main README](../../README.md)). Note its public URL and its caller key (`wrapper.apiKey`).
2. You need an Agent Fabric gateway in your environment, plus `anypoint-cli-v4` with the `agent-network` plugin, logged in to your org.
3. In `exchange.json`, set `groupId` to **your organization id**. The CLI does not fill in a placeholder, and the build fails on one.

## Variables (`exchange.json`)

| Variable | Secret | What to set |
| --- | --- | --- |
| `ingressgw.url` | no | Public URL of your gateway, e.g. `https://<gateway>.<id>.usa-e2.cloudhub.io` |
| `jevWrapper.url` | no | Wrapper base URL ending in `/v1/` (the default is the demo deployment) |
| `jev.apiKey` | **yes** | The wrapper's `wrapper.apiKey`. Pass it at deploy time; never write it in a file |
| `catalogMcp.url`, `membershipAgent.url`, `recommendationAgent.url` | no | A2D mock URLs (already the defaults) |

## Deploy

```bash
cd examples
anypoint-cli-v4 agent-network project build --path v1-library-loans

anypoint-cli-v4 agent-network project deploy --path v1-library-loans -g <gateway-name> \
  --property "ingressgw.url:https://<gateway-public-url>" \
  --property "jevWrapper.url:https://<wrapper-public-url>/v1/" \
  --property "catalogMcp.url:https://www.a2d-ai.com/api/platform/9b2edd04-bf9a-4b09-8b7f-c31d5802585a/" \
  --property "membershipAgent.url:https://www.a2d-ai.com/api/platform/9c75f4b5-449f-4fb3-a0e7-d229cb97cd3c/a2a" \
  --property "recommendationAgent.url:https://www.a2d-ai.com/api/platform/5e0bb263-9aef-4f38-826e-f7072f2a7764/a2a" \
  --property "jev.apiKey:$JEV_WRAPPER_KEY"
```

The CLI asks for every variable you don't pass, so pass all of them. Keep the key in an environment variable so it doesn't land in your shell history.

With Octoloom: open the folder, click **Deploy** in Projects & Deploy, pick the gateway, and type the wrapper key when asked for `jev.apiKey`.

The broker is then served at `https://<gateway-public-url>/jev_lib1_library-broker/`.

## Try it

Send an A2A 0.3.0 `message/send`. Send the JSON-RPC `id` as a **string**, because the v1 runtime resets the connection on large numeric ids:

```bash
curl -s https://<gateway-public-url>/jev_lib1_library-broker/ -H 'content-type: application/json' -d '{
  "jsonrpc": "2.0", "id": "1", "method": "message/send",
  "params": { "message": { "role": "user", "messageId": "m1", "kind": "message",
    "parts": [ { "kind": "text", "text": "I am member M-501. Is Dune available? If not, please place a hold for me." } ] } } }'
```

Example prompts (the results come from the mocks, tested on 2026-11-16 with wrapper 1.1.0):

- **I am member M-666. Please check my membership and place a hold on Dune for me.**
  - Jev's calls: `search_books`, then the **Library Membership agent**, then answer.
  - Expected result: M-666 is blocked (unpaid fines of 18.50 EUR), so no hold is placed.
- **I am member M-501. Is Dune available? If not, please place a hold for me.**
  - Jev's calls: `search_books`, then the Library Membership agent, then `place_hold`.
  - Expected result: Dune (BK-1001) is out. The hold is HLD-7781, queue position 2, pickup at the Main branch.
- **I loved Dune. Can you recommend similar books?**
  - Jev's calls: the **Book Recommendation agent**.
  - Expected result: Hyperion (BK-4004) and Foundation (BK-4005), both available.
- **I am member M-501. Is The Hobbit available? Please place a hold if it is not.**
  - Jev's calls: `search_books`.
  - Expected result: The Hobbit (BK-2002) is available, so no hold is placed.

Each reply from the wrapper has a header like `x-jev-decision: tool:<name>;confidence=0.98`, and the wrapper logs list every decision, so you can see that Jev picked the tool.

## How the v1 broker offers its agents

The v1 broker sends each linked A2A agent as an OpenAI **custom tool** (`"type": "custom"`, free-text input, no parameters). Its MCP tools are sent as function tools. Up to wrapper 1.0.1, only function tools were passed on to Jev, so Jev never saw the agents:

- M-666 got a hold even though the Membership mock says that member is blocked.
- "Books like Dune" got a follow-up question instead of the recommendation agent's answer.

Since 1.1.0, the wrapper shows Jev a custom tool as a function with one string argument `input`, and returns the call to the broker as a `custom_tool_call`. The broker then sends that text to the agent. No change to the broker, its instructions or the A2D mocks was needed.

The broker is probabilistic, so the wording and the order of calls can change between runs. The ids and numbers come from the mocks and stay the same.
