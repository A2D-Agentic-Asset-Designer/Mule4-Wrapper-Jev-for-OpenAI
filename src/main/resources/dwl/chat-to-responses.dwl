%dw 2.0
output application/json
// Chat Completions reply (OpenRouter) -> OpenAI Responses object, echoing the request settings (vars.rreq).
var r = payload
var q = vars.rreq default {}
var m = r.choices[0].message default {}
var tc = m.tool_calls default []
var text = (m.content default "") as String
fun id(prefix) = prefix ++ (uuid() replace "-" with "")
var msg = { "type": "message", id: id("msg_"), status: "completed", role: "assistant", content: [{ "type": "output_text", text: text, annotations: [], logprobs: [] }] }
// Calls to a custom tool of the request (e.g. a v1 broker's A2A agent) go back as custom_tool_call with the free-text input.
var customNames = ((q.tools default []) filter ((t) -> t."type" == "custom")) map ((t) -> t.name)
fun customInput(args) = do {
  var a = if (args is String) (read(args, "application/json") default {}) else (args default {})
  ---
  if (a is Object) ((a."input" default write(a, "application/json", { indent: false })) as String) else (a as String)
}
var calls = tc map ((t) ->
  if (customNames contains t.function.name)
    { "type": "custom_tool_call", id: id("ctc_"), call_id: t.id default id("call_"), name: t.function.name, "input": customInput(t.function.arguments default "{}"), status: "completed" }
  else
    { "type": "function_call", id: id("fc_"), call_id: t.id default id("call_"), name: t.function.name, arguments: t.function.arguments default "{}", status: "completed" })
---
{
  id: id("resp_"),
  object: "response",
  created_at: r.created default (now() as Number { unit: "seconds" }),
  status: "completed",
  background: false,
  error: null,
  incomplete_details: null,
  instructions: q.instructions default null,
  max_output_tokens: q.max_output_tokens default null,
  model: q.model default r.model,
  "output": (if (!isEmpty(text) or isEmpty(calls)) [msg] else []) ++ calls,
  parallel_tool_calls: q.parallel_tool_calls default true,
  previous_response_id: q.previous_response_id default null,
  reasoning: { effort: null, summary: null },
  store: false,
  temperature: q.temperature default 1,
  text: q.text default { format: { "type": "text" } },
  tool_choice: q.tool_choice default "auto",
  tools: q.tools default [],
  top_p: q.top_p default 1,
  truncation: "disabled",
  usage: {
    input_tokens: r.usage.prompt_tokens default 0,
    input_tokens_details: { cached_tokens: 0 },
    output_tokens: r.usage.completion_tokens default 0,
    output_tokens_details: { reasoning_tokens: 0 },
    total_tokens: r.usage.total_tokens default 0
  },
  user: null,
  metadata: q.metadata default {}
}
