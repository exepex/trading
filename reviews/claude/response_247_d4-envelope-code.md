# Response 247: story D4 code, Book 2's authority envelope (code round, lane 1)

Builder: Claude, 16 Oct 2026 (IST), branch `story/d4-envelope-code`. Owner, 16 Oct (DESK_DECISIONS row 239): D4 and
D5 code starts now. Both are built, judged and switched off until a strategy qualifies. Text:
`docs/stories/D-playbook-decisions.md` D4 (judge 207 addenda 1-2; ChatGPT 130 answered in response 212). **Nothing is
switched on:** no envelope file exists, so every Book 2 trade still fails C4 ("no trade envelope").

## Files

- New:
  - `fno/playbook/envelope.py`: the action and status enums, `TradeEnvelope`, `BookTerms`,
    `AuthorityEnvelope.permits`, `resolve`;
  - `fno/playbook/envelope_files.py`: the files, their hash, `component_key`, `served_envelopes`;
  - `fno/checks/validity_envelope.py`: `EnvelopeMode`;
  - `fno/books/registered_components.py`: the active D6 components on a day.
- Changed:
  - `fno/checks/validity_modes.py`: `PlaybookMode` takes a lots rule, exact by default, so Book 1 is unchanged;
  - `fno/checks/validity_proposal.py`: one field, `rule_default`;
  - `fno/checks/wiring.py`: Book 2 maps to `EnvelopeMode`, with `validity_modes(root)`;
  - `fno/playbook/decision_record.py`: Book 2's four fields must be non-empty.
- Tests:
  - `tests/envelope/`: 31 tests;
  - one new parametrised test (4 cases) in `tests/decisions/test_records.py`;
  - `tests/checks/test_validity.py`: the old "Book 2 waits for D4" test is replaced by "Book 2 fails closed without an
    envelope";
  - `tests/checks/validity_builders.py`: `checker(modes=...)`.

## Criteria

| # | Where | Test | Evidence |
|---|---|---|---|
| 1 | `permits`, `TradeEnvelope.status` | each action under each status; an unlisted action is forbidden; combined actions take the strictest | strong (tests) |
| 2 | `_terms_problem`; C4's lots, width, structure and version checks | lot increase, width outside the set, another structure, a different rule fingerprint, at `permits` and at C4 | strong |
| 3 | `resolve` | allowed: the choice trades; shadow-only: the account takes the rule default and the choice is shadow; forbidden: no trade, attempt recorded. C4 refuses a shadow-only action as the account's trade | strong |
| 4 | `EnvelopeMode`, `RegisteredComponents` | the file hash differs from the registered component: `envelope_registered` fails (temporary registry file) | strong |
| 5 | `EnvelopeMode` | a forbidden width choice is blocked by C4 with no decider involved | strong |
| 6 | `permits` | no rule trade: following it passes, and any trade is refused ("never creates one") | strong |
| 7 | `validate_record`, `NON_EMPTY` | an empty reason, verdict, chosen action or rule default is refused for Book 2 | strong |
| 8 | `permits`, `_actions` | A and B with different envelopes: B at a width other than its own is refused; B at its own passes; A's width is not in B's set | strong |
| 9 | C4 `permitted` plus `permits` eligibility | an ineligible B is refused even when its envelope allows the choice; the hash must match D6 | strong |

Mutation checks, run and restored:
- the hash check replaced by `True` fails 1 test;
- Book 2's lots made exact fails 3;
- D3's non-empty rule removed fails 4.

## Deviations from the passed text (for the judge)

1. **The envelopes are in `playbook/envelopes/<name>-v<n>.yaml`, not beside the playbook file.** D1's loader parses
   every `*.yaml` directly in `playbook/` as a strategy (`loader.py:24, 124`), so an envelope there would be refused
   and break the playbook. A test runs the loader's own pattern on the layout. Strong evidence.
2. **There is no `action` field on the proposal.** The actions are derived from the trade's terms against the rule
   default. A claimed action could disagree with the terms; derived ones cannot. The proposal gains only
   `rule_default`. Reasoning, with the tests above.
3. **Reference terms when the AI switches version.** The version's own widest width and its lots. D2 tries widths
   from widest down (`candidates.py:59`), and the text's "B at its own width" needs a definition. Reasoning only; I
   flag it for the judge.
4. **C4 checks the envelope file against the D6 component.** That the record's `served` key equals the component is
   D6's own check when the decision is scored (`versions.py`: any differing served key unscores it).
   `served_envelopes` builds those keys for F5 from the same hashes. So criterion 9's "and the record's `served` key"
   is met by D6, not repeated in C4.
5. **`PlaybookMode` gains a lots rule** (exact by default) instead of `EnvelopeMode` copying its six checks. One
   parameter keeps a single copy (DRY), and Book 1's tests are unchanged.

## Not done here, and why

- **D3's refusal of a non-empty `owner_override`** (owner, 16 Oct: built before any Book 2 or 3 paper decision). It is
  D3's file and touches every book, so it is not in D4's scope. I can do it as its own small lane-1 change. The
  orchestrator decides.
- **S3 reading shadow actions** belongs to S3's builder (at slice E).
- **F5, the AI that chooses**, is a later story.
