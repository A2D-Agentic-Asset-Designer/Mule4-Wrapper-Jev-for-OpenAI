%dw 2.0
output application/json
// Only standard OpenAI chat.completion fields (OpenRouter adds cost, reasoning, provider...).
var r = payload
---
{
  id: r.id default ("chatcmpl-" ++ uuid()),
  object: "chat.completion",
  created: r.created default now() as Number {unit: "seconds"},
  model: vars.req.model default r.model,
  choices: (r.choices default []) map ((c, i) -> do {
    var tc = c.message.tool_calls default []
    ---
    {
      index: c.index default i,
      message: {
        role: "assistant",
        content: if (sizeOf(tc) > 0) (c.message.content default null) else (c.message.content default ""),
        (tool_calls: tc map ((t, j) -> { id: t.id default ("call_" ++ uuid()), "type": "function", function: { name: t.function.name, arguments: t.function.arguments default "{}" } })) if (sizeOf(tc) > 0)
      },
      finish_reason: if (sizeOf(tc) > 0) "tool_calls" else (c.finish_reason default "stop")
    }
  }),
  usage: {
    prompt_tokens: r.usage.prompt_tokens default 0,
    completion_tokens: r.usage.completion_tokens default 0,
    total_tokens: r.usage.total_tokens default 0
  }
}
