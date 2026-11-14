%dw 2.0
output text/plain
// stream: true on /v1/responses — the finished Responses object as the Responses API's server-sent events.
var resp = payload
var start = (resp -- ["status", "output", "usage"]) ++ { status: "in_progress", "output": [], usage: null }
fun itemEvents(it, i) =
  if (it."type" == "message") do {
    var part = it.content[0]
    ---
    [
      { "type": "response.output_item.added", output_index: i, item: (it -- ["status", "content"]) ++ { status: "in_progress", content: [] } },
      { "type": "response.content_part.added", item_id: it.id, output_index: i, content_index: 0, part: { "type": "output_text", text: "", annotations: [] } },
      { "type": "response.output_text.delta", item_id: it.id, output_index: i, content_index: 0, delta: part.text, logprobs: [] },
      { "type": "response.output_text.done", item_id: it.id, output_index: i, content_index: 0, text: part.text, logprobs: [] },
      { "type": "response.content_part.done", item_id: it.id, output_index: i, content_index: 0, part: part },
      { "type": "response.output_item.done", output_index: i, item: it }
    ]
  } else [
    { "type": "response.output_item.added", output_index: i, item: (it -- ["status", "arguments"]) ++ { status: "in_progress", arguments: "" } },
    { "type": "response.function_call_arguments.delta", item_id: it.id, output_index: i, delta: it.arguments },
    { "type": "response.function_call_arguments.done", item_id: it.id, output_index: i, arguments: it.arguments },
    { "type": "response.output_item.done", output_index: i, item: it }
  ]
var events = [
  { "type": "response.created", response: start },
  { "type": "response.in_progress", response: start }
] ++ flatten((resp."output" default []) map ((it, i) -> itemEvents(it, i))) ++ [{ "type": "response.completed", response: resp }]
---
(events map ((e, n) -> "event: " ++ e."type" ++ "\ndata: " ++ write(e ++ { sequence_number: n }, "application/json", { indent: false }) ++ "\n\n")) joinBy ""
