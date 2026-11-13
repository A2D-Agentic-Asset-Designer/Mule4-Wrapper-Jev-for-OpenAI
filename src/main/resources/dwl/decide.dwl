%dw 2.0
output application/json
// What the fallback model is told to do, from Jev's answer (or its failure).
var a = vars.jev.answers.next_action default null
var minC = p('jev.minConfidence') as Number
var conf = (a.confidence default 0) as Number
---
if (vars.jevError != null) { action: "auto", reason: "jev error: " ++ vars.jevError }
else if (a == null or a.choice == null) { action: "auto", reason: "no jev answer" }
else if (conf < minC) { action: "auto", reason: "low confidence " ++ (conf as String), choice: a.choice, confidence: conf }
else if (a.choice == "respond_to_user") { action: "respond", choice: a.choice, confidence: conf }
else { action: "tool", tool: a.choice, choice: a.choice, confidence: conf }
