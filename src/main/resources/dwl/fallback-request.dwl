%dw 2.0
output application/json
var req = vars.req
var d = vars.decision
var model = if ((req.model default "") contains "/") req.model else p('fallback.model')
var keep = req -- ["model", "stream", "stream_options", "tool_choice", "parallel_tool_calls"]
var hasTools = sizeOf(req.tools default []) > 0
---
keep ++ { model: model, stream: false } ++ (
  if (!hasTools) {}
  else if (d.action == "passthrough") (if (req.tool_choice != null) { tool_choice: req.tool_choice } else {})
  else if (d.action == "tool") { tool_choice: { "type": "function", function: { name: d.tool } }, parallel_tool_calls: false }
  else if (d.action == "respond") { tool_choice: "none" }
  else (if (req.tool_choice != null) { tool_choice: req.tool_choice } else {})
)
