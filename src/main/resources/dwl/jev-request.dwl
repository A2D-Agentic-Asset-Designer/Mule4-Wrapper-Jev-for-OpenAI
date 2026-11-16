%dw 2.0
output application/json
import * from dw::core::Strings
var req = vars.req
// Builds {model, state, questions}; the TypeSafe Connector sends state and questions (the model comes from the connection).
var maxChars = p('jev.maxChars') as Number
var maxMsgs = p('jev.maxMessages') as Number
fun cut(s) = do {
  var t = if (s is String) s else if (s == null) "" else write(s, "application/json", {indent: false})
  ---
  if (sizeOf(t) > maxChars) t[0 to maxChars - 1] ++ "…" else t
}
fun text(c) = if (c is Array) ((c filter ($."type" == "text")) map $.text) joinBy "\n" else cut(c)
var msgs = req.messages default []
var last = if (sizeOf(msgs) > maxMsgs) msgs[sizeOf(msgs) - maxMsgs to -1] else msgs
var tools = (req.tools default []) filter ($."type" == "function")
var respond = "respond_to_user"
---
{
  model: p('jev.model'),
  state: {
    conversation: last map ((m) -> {
      role: m.role,
      (content: cut(text(m.content))) if (m.content != null),
      (called_tools: (m.tool_calls default []) map ({ tool: $.function.name, arguments: cut($.function.arguments) })) if (m.tool_calls != null),
      (result_of_tool_call: m.tool_call_id) if (m.tool_call_id != null)
    }),
    available_tools: tools map ((t) -> {
      name: t.function.name,
      description: cut(t.function.description default ""),
      parameters: keysOf(t.function.parameters.properties default {}) map ($ as String)
    })
  },
  questions: {
    next_action: {
      "type": "choice",
      instructions: "You are deciding the next step of an assistant in this conversation. Pick the one tool the assistant should call next to make progress on the user's latest request, using the tool results already in the conversation. Pick " ++ respond ++ " when no further tool call is needed: the information is already there, the user must be asked for missing details, or no tool fits.",
      criteria: {
        (tools map ((t) -> { (t.function.name): cut(t.function.description default t.function.name) })),
        ((respond): "No tool now: answer the user (or ask the user for missing details).") if (req.tool_choice != "required")
      }
    }
  }
}
