# f-pdf-text: proving a PDF extraction

Trap: a PDF extraction that silently drops a line produces a false
"ledger-only" item and a false difference downstream.

- `statement.txt` is the text a PDF tool returns for the April statement of
  scenario a. `extract_statement.py --text statement.txt --date-format "%d %b"
  --year 2026 --closing 23392.50` must print PROVEN with 6 lines; the sign of
  each movement comes from the running balance, not from the column position.
- `statement-missing-line.txt` has the Adobe line removed. The running balance
  jumps from 21,700.00 to 24,005.00 while the line shows 2,400.00, so the script
  must exit 2 naming page 1 and the line. The correct response is to stop and ask
  for the bank's CSV export, never to "fill in" the missing line.
