# Validation: statement graph (`core/graph.py`)

`StatementGraph` projects one year from an opening balance sheet and operating drivers: the income
statement, the cash flow statement (indirect method) and the closing balance sheet. The scenario tree
(`agents/deep.py`) and the research agent's scenarios (`agents/research.py`) run on it. Status:
**not reference-checked**. Its arithmetic is checked against hand calculations, and its balance check
is shown to fail on a wiring fault, but it has not been compared with a published worked example.
Status of every engine: [validation status](status.md).

## What the balance check means

Every closing balance is rolled forward from its opening balance: cash by the cash flow statement,
receivables and payables from receivable and payable days, net PP&E by capex less depreciation, retained
earnings by net income. Nothing is plugged. Assets and liabilities plus equity are each summed from their
own lines, so `is_balanced` tests whether the cash flow statement captures every balance-sheet change.
It does not test whether the drivers are sensible. `cash_reconciled` compares closing cash from the cash
flow statement with the cash the balance sheet implies. In a projection that is the same test seen from
the other side, so a wiring fault fails both.

## Checks

Tests: `tests/test_graph.py` (hand calculations in the comments), `tests/test_advanced_agents.py`
(scenario tree and research agent).

| Check | Reference | Tolerance (measured) | Status |
| :--- | :--- | :--- | :--- |
| One-year projection: income statement, receivables and payables, CFO, closing balance sheet (assets 930 = 300 + 630) | hand calculation | rel 1e-6 (measured error 0.0 on all 15 values) | pass |
| A payables increase raises CFO; a loss year earns no tax credit and still balances | hand calculation | rel 1e-6 (measured error 0.0) | pass |
| The balance check fails on a wiring fault: CFO without the change in receivables is out by the change (−20) | hand calculation | rel 1e-6 | pass |
| An opening balance sheet that does not balance raises `ValueError` | n/a | float rounding (1e-12 of the largest input) | **fixed**: the graph added any balance-sheet gap to equity, so `is_balanced` held for any input (opening cash of 1e9 against debt of 200 and equity of 400 "balanced" with a plug of 999,999,974) |
| CFO includes the working-capital changes | n/a | n/a | **fixed**: CFO was net income plus depreciation while receivables and payables appeared on the balance sheet; the plug absorbed the difference (73.97 on the old test inputs) |
| Retained earnings roll forward | n/a | n/a | **fixed**: closing retained earnings were one year's net income; now opening plus net income |
| Scenario branches keep every baseline driver (Base branch ending cash 360.375) | hand calculation | rel 1e-6 | **fixed**: the scenario tree rebuilt each branch without receivable and payable days, so they were always 45 and 30 |
| A branch whose balance sheet does not balance is pruned | n/a | n/a | **fixed**: the pruning rule could not fire while the graph plugged equity |
| Research agent on Apple's FY2026 10-K: the scenarios open at the filing's balance sheet; Base ending cash = cash + NI + depreciation − capex + 0.05 × (payables − receivables) | the filing's reported lines (fixture) | rel 1e-12 | pass |
| Non-finite inputs, negative revenue, capex, depreciation, days or opening working capital, a tax rate outside [0, 1] | n/a | n/a | raise `ValueError` naming the input |

On the three real-filing fixtures (Apple, Microsoft and Nvidia FY2026), the opening balance sheets balance
exactly (assets − liabilities − equity = 0), and the test above holds for each. Net income in each
scenario is unchanged by the fix; ending cash now includes the working-capital term, which in the Base
branch is 0.05 × (payables − receivables): +1,921.75 for Apple (0.05 × (82,252 − 43,817), USD millions)
and −1,923.0 for Microsoft (0.05 × (42,416 − 80,876)).

## Not modelled

Debt is held at its opening value (no issuance or repayment), and there are no dividends or buybacks
(CFF = 0). Inventory, other assets and other liabilities are held at their opening values. Interest is on
opening debt. The tax charge is max(0, pre-tax income × rate). The research agent sets receivable and
payable days from the filing year and holds everything else on the balance sheet constant; its scenario
multipliers are assumptions and are listed in the dossier.

**Open:** a check against a published three-statement worked example; dividends and debt flows.
