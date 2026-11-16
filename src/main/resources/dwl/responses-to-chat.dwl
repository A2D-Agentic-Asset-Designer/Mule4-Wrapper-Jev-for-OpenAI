%dw 2.0
output application/json
// OpenAI Responses request -> Chat Completions request (vars.req), so both APIs share the Jev pipeline.
var r = payload
fun txt(c) =
  if (c is String) c
  else if (c is Array) ((c filter ((p) -> p is Object and p.text != null)) map ((p) -> p.text as String)) joinBy "\n"
  else if (c == null) ""
  else write(c, "application/json", { indent: false })
fun kind(it) = it."type" default (if (it.role != null) "message" else "unknown")
// Consecutive function calls (and a text reply before them) become one assistant message with tool_calls.
fun addCall(acc, call) = do {
  var n = sizeOf(acc)
  var lastM = if (n > 0) acc[n - 1] else null
  ---
  if (lastM != null and lastM.role == "assistant")
    (if (n > 1) acc[0 to n - 2] else []) ++ [(lastM - "tool_calls") ++ { tool_calls: (lastM.tool_calls default []) << call }]
  else acc << { role: "assistant", content: null, tool_calls: [call] }
}
var items = if (r."input" is String) [{ role: "user", content: r."input" }] else (r."input" default [])
var sys = if (!isEmpty(r.instructions default "")) [{ role: "system", content: r.instructions as String }] else []
var msgs = (items reduce ((it, acc = []) ->
  kind(it) match {
    case "message" -> acc << { role: if (it.role == "developer") "system" else it.role, content: txt(it.content) }
    case "function_call" -> addCall(acc, { id: it.call_id, "type": "function", function: { name: it.name, arguments: it.arguments default "{}" } })
    case "function_call_output" -> acc << { role: "tool", tool_call_id: it.call_id, content: txt(it."output") }
    case "custom_tool_call" -> addCall(acc, { id: it.call_id, "type": "function", function: { name: it.name, arguments: write({ "input": (it."input" default "") as String }, "application/json", { indent: false }) } })
    case "custom_tool_call_output" -> acc << { role: "tool", tool_call_id: it.call_id, content: txt(it."output") }
    else -> acc
  })) default []
// Function tools pass through. Custom tools (free-text input; the v1 broker sends its linked A2A agents this way)
// become function tools with one string argument "input"; chat-to-responses.dwl turns the call back into a custom_tool_call.
var tools = ((r.tools default []) filter ((t) -> t."type" == "function" or t."type" == "custom")) map ((t) ->
  if (t."type" == "custom") {
    "type": "function",
    function: {
      name: t.name,
      (description: t.description) if (t.description != null),
      parameters: { "type": "object", properties: { "input": { "type": "string", description: "The request for this tool, in plain natural language" } }, required: ["input"] }
    }
  } else {
    "type": "function",
    function: { name: t.name, (description: t.description) if (t.description != null), parameters: t.parameters default { "type": "object", properties: {} } }
  })
var tc = r.tool_choice
var toolChoice = if (tc is String) tc else if (tc is Object and (tc."type" == "function" or tc."type" == "custom")) { "type": "function", function: { name: tc.name } } else null
var f = r.text.format default null
var rf = if (f == null) null
  else if (f."type" == "json_schema") { "type": "json_schema", json_schema: { name: f.name default "output", schema: f.schema, strict: f.strict default false } }
  else if (f."type" == "json_object") { "type": "json_object" }
  else null
---
{
  model: r.model default "",
  messages: sys ++ msgs,
  (tools: tools) if (!isEmpty(tools)),
  (tool_choice: toolChoice) if (toolChoice != null and !isEmpty(tools)),
  (response_format: rf) if (rf != null),
  (max_tokens: r.max_output_tokens) if (r.max_output_tokens != null),
  (temperature: r.temperature) if (r.temperature != null),
  (top_p: r.top_p) if (r.top_p != null),
  stream: false
}
