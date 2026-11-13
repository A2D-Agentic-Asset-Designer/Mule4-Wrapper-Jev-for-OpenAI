%dw 2.0
output text/plain
// stream: true — the finished reply as OpenAI chat.completion.chunk server-sent events.
var r = payload
var c = r.choices[0]
var m = c.message
var tc = m.tool_calls default []
var base = { id: r.id, object: "chat.completion.chunk", created: r.created, model: r.model }
var d1 = { role: "assistant", content: if (sizeOf(tc) > 0) (m.content default null) else (m.content default "") } ++ (if (sizeOf(tc) > 0) { tool_calls: tc map ((t, i) -> { index: i } ++ t) } else {})
var c1 = base ++ { choices: [{ index: 0, delta: d1, finish_reason: null }] }
var c2 = base ++ { choices: [{ index: 0, delta: {}, finish_reason: c.finish_reason }] }
var c3 = base ++ { choices: [], usage: r.usage }
fun ev(x) = "data: " ++ write(x, "application/json", { indent: false }) ++ "\n\n"
---
ev(c1) ++ ev(c2) ++ (if (vars.req.stream_options.include_usage default false) ev(c3) else "") ++ "data: [DONE]\n\n"
