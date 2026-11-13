%dw 2.0
output application/json
---
{ error: { message: vars.errMessage default (error.description default "Internal error"), "type": vars.errType default "server_error", code: vars.errCode default null } }
