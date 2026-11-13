# Mule 4 Wrapper: Jev for OpenAI

A small Mule 4 application that looks like an **OpenAI Chat Completions** endpoint, so anything that speaks OpenAI can use it. This includes MuleSoft Agent Fabric brokers (v1 LLM brokers and v2 AgentScript brokers).

The wrapper sends each request through two steps:

1. **Jev decides the action.** Typesafe's decision model `~typesafe/jev-latest` runs on OpenRouter (`POST /api/alpha/decisions`). It gets the recent conversation and the tools on offer, then picks one of them or `respond_to_user`. It returns a choice with a confidence score.
2. **A chat model writes the reply.** The fallback model (default `openai/gpt-4o-mini`, also via OpenRouter) writes the answer or the tool arguments:
   - Jev picked a tool: the tool call is forced (`tool_choice: {type: function, name}`).
   - Jev picked `respond_to_user`: the model must answer in text (`tool_choice: none`).
   - Jev is unsure (confidence below `jev.minConfidence`), fails, or there are no tools: the model decides alone (`auto` or the caller's `tool_choice`).

Every response has a `x-jev-decision` header, for example `tool:get_order_status;confidence=1`, `respond;confidence=0.97`, `auto` or `passthrough`.

```
client (OpenAI SDK, Agent Fabric broker)
   │  POST /v1/chat/completions
   ▼
Mule wrapper ──► OpenRouter /api/alpha/decisions   (Jev: which tool / respond?)
   │
   └──────────► OpenRouter /api/v1/chat/completions (fallback model: text / tool args)
   ▼
OpenAI-shaped chat.completion (or SSE stream)
```

## Endpoints

| Method | Path | What it does |
| --- | --- | --- |
| POST | `/v1/chat/completions` | OpenAI Chat Completions: messages, tools, tool_choice and stream are supported |
| GET | `/v1/models` | Lists the fallback model and `jev` |
| GET | `/health` | `{"status":"UP"}` |
| any | anything else | 404 with an OpenAI-style error |

Errors use the OpenAI shape `{"error":{"message","type","code"}}`.

## Configuration

`src/main/resources/config.yaml` holds the defaults. **It holds no secrets.** Override any value with a property at deploy time.

| Property | Default | Meaning |
| --- | --- | --- |
| `openrouter.apiKey` | (empty) | **Secure property.** Your OpenRouter API key |
| `wrapper.apiKey` | (empty) | **Secure property.** When set, callers must send `Authorization: Bearer <wrapper.apiKey>`. Empty means no check |
| `jev.enabled` | `true` | Turn the Jev step off to make the wrapper a plain proxy |
| `jev.model` | `~typesafe/jev-latest` | Jev model id |
| `jev.minConfidence` | `0.5` | Below this, the fallback model decides alone |
| `jev.maxMessages` / `jev.maxChars` | `12` / `2000` | How much of the conversation is sent to Jev |
| `fallback.model` | `openai/gpt-4o-mini` | Model that writes the reply. A request `model` that contains `/` (an OpenRouter id) overrides it |
| `http.port` | `8081` | Listener port |

## Build and run locally

You need Java 17 and Maven, plus a Mule 4.9 runtime (standalone, or the one bundled with Anypoint Code Builder).

```bash
mvn -DskipTests package
cp target/jev-openai-wrapper-1.0.0-mule-application.jar $MULE_HOME/apps/
$MULE_HOME/bin/mule -M-Dopenrouter.apiKey="$OPENROUTER_API_KEY" -M-Dhttp.port=8091
```

Try it:

```bash
curl -s localhost:8091/v1/chat/completions -H 'content-type: application/json' -d '{
  "model": "gpt-4o-mini",
  "messages": [{"role":"user","content":"Where is my order 1042?"}],
  "tools": [{"type":"function","function":{"name":"get_order_status","description":"Status of an order",
             "parameters":{"type":"object","properties":{"order_id":{"type":"string"}},"required":["order_id"]}}}]
}' -D - | grep -iE 'x-jev-decision|tool_calls'
```

## Deploy to CloudHub 2.0

Publish to Exchange with your org id as the group id, then deploy with the key as a **secure property**:

```bash
mvn -DgroupId=<org-id> -DskipTests deploy          # needs Exchange credentials in ~/.m2/settings.xml (server id anypoint-exchange-v3)

anypoint-cli-v4 runtime-mgr application deploy jev-openai-wrapper cloudhub-us-east-2 4.9.24:10e-java17 jev-openai-wrapper \
  --groupId <org-id> --assetVersion 1.0.0 --javaVersion 17 \
  --secureProperty "openrouter.apiKey=$OPENROUTER_API_KEY" \
  --secureProperty "wrapper.apiKey=$WRAPPER_API_KEY"
```

Your OpenAI base URL is then `https://<app-public-url>/v1/`.

## Use it as the LLM of an Agent Fabric broker

**v1 broker** (`agent-network.yaml`):

```yaml
connections:
  jev-openai-connection:
    kind: llm
    spec:
      url: https://<app-public-url>/v1/
      configuration:
        apiKey: ${jev.apiKey}      # the wrapper.apiKey, or any text when the check is off
```

**v2 broker** (`agent-network.yaml` context):

```yaml
context:
  connections:
    jev_openai_connection:
      kind: llm
      url: https://<app-public-url>/v1/
      authentication:
        kind: apiKey
        apiKey: ${jev.apiKey}
```

## Limits

- `stream: true` is supported, but the reply arrives as one chunk after the model has finished (no token streaming).
- Jev only picks **one** next action, so each turn has at most one tool call (`parallel_tool_calls: false`).
- Each call costs one Jev decision (about $0.00002) plus the fallback model's tokens.
- Only the Chat Completions API is served. `/v1/responses`, embeddings and images are not.

## Security

Never commit keys. `.gitignore` excludes `*.key`, `.env`, `.envrc` and `local.properties`. Pass keys only as secure properties.
