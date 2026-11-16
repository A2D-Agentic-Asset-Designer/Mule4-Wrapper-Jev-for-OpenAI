# Jev Restaurant Booking (v2)

A guest asks for a table. The broker finds and books one, checks the menu for allergies or diets, and adds the guest's loyalty perks. Its LLM is the **Jev OpenAI wrapper** (the Mule app in this repo), so Jev decides each tool and agent call and `openai/gpt-4o-mini` writes the text.

- Style: Agent Network 2.0 (`agentNetwork: 2.0.0`), AgentScript broker (`brokers/booking-broker.agent`), A2A 1.0
- Broker: `jev_rb2_booking_broker`: one orchestrator step (`book`) with four actions
- MCP server: Restaurant Tables MCP (`find_table`, `book_table`)
- Agents: Menu Allergy Agent, Restaurant Loyalty Agent (both A2A 1.0)
- LLM: `jev_rb2_jev` on connection `jev_rb2_llm_connection`, whose URL is the wrapper (`${jevWrapper.url}`)

The MCP server and the agents are public A2D mocks, so the network needs no other system. No credentials are stored in this project.

## Before you deploy

1. The Jev wrapper must be running, at version **1.0.1 or later** (see the [main README](../../README.md)). v2 brokers call `POST /v1/responses` and check it at startup. On an older wrapper the broker keeps restarting. Note the wrapper's public URL and its caller key (`wrapper.apiKey`).
2. You need an Agent Fabric gateway in your environment, plus `anypoint-cli-v4` with the `agent-network` plugin, logged in to your org.
3. In `exchange.json`, replace `<enter-your-org-id>` in `groupId` with **your organization id**. The CLI does not fill in a placeholder.
4. Connection keys must be unique in an environment. When you deploy a second copy, rename the `jev_rb2_` prefix, or the deploy fails with a 409.

## Variables (`exchange.json`)

| Variable | Secret | What to set |
| --- | --- | --- |
| `jevWrapper.url` | no | Wrapper base URL ending in `/v1`. The default is the placeholder `https://<your-cloudhub-wrapper-deployment-url>/v1`: replace it or pass your URL at deploy time |
| `jev.apiKey` | **yes** | The wrapper's `wrapper.apiKey`. Pass it at deploy time; never write it in a file |
| `tablesMcp.url`, `menuAgent.url`, `loyaltyAgent.url` | no | A2D mock URLs (already the defaults) |

## Deploy

```bash
cd examples
anypoint-cli-v4 agent-network project build --path v2-restaurant-booking

anypoint-cli-v4 agent-network project deploy --path v2-restaurant-booking -g <gateway-name> \
  --property "jevWrapper.url:https://<your-cloudhub-wrapper-deployment-url>/v1" \
  --property "tablesMcp.url:https://www.a2d-ai.com/api/platform/8552e021-0a18-4ca8-979d-729ef0e71273/" \
  --property "menuAgent.url:https://www.a2d-ai.com/api/platform/dfb5bd9b-cf76-4847-99bf-00273c063af7/a2a" \
  --property "loyaltyAgent.url:https://www.a2d-ai.com/api/platform/2597660f-31fc-4ef7-b08c-91c7c372d2a4/a2a" \
  --property "jev.apiKey:$JEV_WRAPPER_KEY"
```

If you rebuild after changing `exchange.json`, delete `target/` first so the deploy doesn't use the old build. The first start of a v2 broker can take several minutes.

With Octoloom: open the folder, click **Deploy** in Projects & Deploy, pick the gateway, and type the wrapper key when asked for `jev.apiKey`.

The broker is then served at `https://<gateway-public-url>/jev_rb2_booking_broker/`.

## Try it

Send an A2A 1.0 `SendMessage` with the header `A2A-Version: 1.0`:

```bash
curl -s https://<gateway-public-url>/jev_rb2_booking_broker/ -H 'content-type: application/json' -H 'A2A-Version: 1.0' -d '{
  "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
  "params": { "message": { "role": "ROLE_USER", "messageId": "m1",
    "parts": [ { "text": "Table for 4 on 2026-11-20 at 19:30 for Maria Rossi. One guest has a nut allergy." } ] } } }'
```

Example prompts (the results come from the mocks, tested on 2026-11-14, again on 2026-11-16 with wrapper 1.2.0):

- **Table for 4 on 2026-11-20 at 19:30 for Maria Rossi. One guest has a nut allergy.**
  - Expected result:
    - `find_table`: T-12 by the window. `book_table` creates RSV-5521.
    - Menu agent: nut-free dishes are grilled salmon, risotto ai funghi and lemon sorbet; avoid the pesto pasta and the praline cake.
    - Loyalty agent: Gold member with 1,240 points, so a free welcome drink and 10% off the bill.
- **Table for 2 on 2026-11-21 at 20:00 for John Smith. We eat gluten-free.**
  - Expected result: RSV-5521. Gluten-free dishes are grilled salmon, steak frites (fries from a separate fryer) and panna cotta. Gold perks as above.
- **Book a table for 10 people on 2026-11-22 at 19:00 for Anna Meier.**
  - Expected result: `find_table` refuses parties over 8. The broker tries another time (21:30), then asks you to change the request (`TASK_STATE_INPUT_REQUIRED`). Nothing is booked.

In the wrapper logs, each step shows Jev's decision, for example:

```
decision {"action":"tool","tool":"find_table-client__find_table","confidence":1}
decision {"action":"tool","tool":"menu_agent-client","confidence":0.6}
decision {"action":"tool","tool":"book_table-client__book_table","confidence":0.9}
decision {"action":"tool","tool":"loyalty_agent-client","confidence":0.99}
decision {"action":"respond","choice":"respond_to_user","confidence":1}
```

When Jev's confidence is below `jev.minConfidence` (0.5), the wrapper lets the chat model decide alone (`"action":"auto"`).

The broker is probabilistic, so the wording and the order of calls can change between runs. The ids and numbers come from the mocks and stay the same.
