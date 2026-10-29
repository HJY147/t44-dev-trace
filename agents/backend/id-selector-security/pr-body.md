Fix the confirmed frozen-contract classification error for numeric SQL selector expressions. Exact source: 90b734f65ce6ee9f5c217e885bc7ea4857e32b48; base frozen356f29983c904e949245aedfad464efc1bf7b63d.

The sole production change adds numeric OR/AND equality to the existing selector attack pattern. Authentication priority, normal integer validation, body text handling, SQL, transactions, pools and current measured356f SUT stay unchanged.

Exact encoded owner_id attack: old source returns422 (preserved failing regression), candidate returns400 SECURITY_INPUT_REJECTED with committed rejection audit and zero task SELECTs. Ordinary malformed owner remains422, valid owner remains200, missing credentials remain401. New regression plus existing selector/quoted-text/auth neighbors:6 passed,118 deselected; original backend Ruff passed. SQLite/TestClient only, not independent acceptance/MySQL or performance evidence.

New exact-source full CI and Docker build required; old results are not transplanted. No private QA read or tester contact. AI implementation, no student manual-fix claim.

Agent-Role: backend
Prompt-Ref: ROLE-backend-ID-SELECTOR-SECURITY-v1
Refs: #3
