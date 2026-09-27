# System of record and live connections

Why: integrations are reachable only as platform capabilities, never from a
script (the sandbox holds no accounting credentials) [104]. Knowing on day one
which sources are live and which are export-only decides how every later skill
gets its inputs. Bench shut down on 27 December 2024 and customers lost access
at once [62][85], so the owner must also hold their own exported copies.

## Contents
1. What to record
2. Read-only connection probe
3. When nothing is connected
4. What this skill never does

## 1. What to record (in `intake.json.system_of_record` and per source)

- Ledger name (QuickBooks Online, Xero, a spreadsheet, none).
- `connection`: `live` (a capability answered a read probe), `export_only`, or
  `not_checked`.
- `owner_holds_export_copy`: yes or no. If no, add an open item: "Owner to
  export and keep a copy of the ledger and documents" (owner: the owner).
- Where documents live (drive folder, receipt app, email).

## 2. Read-only connection probe

For each system the owner names (ledger, bank feed, Stripe, PayPal, Google
Drive, Google Sheets):

1. `find_capability(query="<system> read transactions")` (or "list accounts",
   "list files"). Note whether a result exists and whether it shows as connected.
2. `describe_capability(id=<result id>)`. Confirm the effect is a read. If the
   tool's name or schema suggests it writes (create, update, post, categorise,
   match, send), do not call it.
3. `run_capability(id=<result id>, input={...}, validate_only=true)`. This is a
   safe probe; it does not fetch data.
4. On a sign-in card: stop that probe and tell the user which system to connect
   and why ("read-only access to <system> so I can pull the April bank lines").
   Carry on with the other systems.
5. Record the outcome per source: `live`, `export_only`, or `sign-in needed`.

Do not hard-code capability ids; resolve them with `find_capability` each time.
Which accounting integrations exist in a given workspace is not known in
advance. If none is found, record `export_only` and work from exports.

## 3. When nothing is connected

Ask for exports instead (CSV preferred). For a PDF statement, ask the owner to
also supply the opening balance, closing balance and period so the export can be
tied to it. Do not read figures off a PDF by guessing at its layout.

## 4. What this skill never does

- Never calls a write, post, categorise, match or send tool. Intake is read-only.
- Never asks the user for passwords, one-time codes or API keys in chat.
- A connection that could write is still used read-only here; later skills
  gate each write separately.
