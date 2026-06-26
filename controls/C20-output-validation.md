### Control 20 - Agent-to-Human Output Validation {#sec-c20}

**Layer:** Layer 3 - Observability and Forensics Controls
**Placement rationale:** C20 sits in Layer 3 alongside C13 (semantic observability) and C19 (model behaviour monitoring) because it is an observation-and-response control that operates on the agent's output stream rather than on its tool calls or its memory reads. C13 captures the agent's intent telemetry on a per-run basis. C19 watches the statistical distribution of behaviour over time. C20 inspects the content of every final response immediately before delivery and routes it through a configured action matrix. All three controls operate on the output stream but at different levels: C13 is per-run intent, C19 is aggregate drift, C20 is per-response content classification. Placing C20 in Layer 2 would misrepresent it as a per-call decision gate on the same axis as C05 and C09; placing it in Layer 1 would imply that output classification is an identity property. Layer 3 is the right home: output validation is observation of the response stream with a governance response path attached, exactly the shape Layer 3 already carries.

#### Why

Without this control, an agent that passes every existing GATE check can still deliver a regulated-content response to a user with no record that the response was classified, no opportunity for human review, and no redaction of fields the response should never have contained. The agent's identity is valid (C01). The agent's tool calls were policy-compliant (C05). The invariants held (C09). The model is not drifting (C19). The replay reproduces (C10). And the agent told a customer that a specific medication is safe to take, or that a specific contract term is enforceable, or returned a record that included an unredacted social security number alongside the answer the customer asked for. The failure mode is at the output boundary, and GATE v1.3 has no control there.

This happens through several routes. An agent answers a benign question by retrieving information that happens to fall into a regulated category (medical advice, legal advice, financial advice, HR decisions, immigration guidance) without the calling system being aware that the answer crosses a regulatory line. An agent producing a structured response includes a field that contains personal data the consumer was not entitled to see, because the upstream tool returned more than the agent's prompt expected and the agent included it verbatim in the output. An agent with general-purpose capabilities answers a question outside its intended scope with apparent confidence, and the calling user has no signal that the answer is low-confidence relative to the agent's calibrated distribution.

Prompt-based constraints fail here for two reasons. First, the agent is asked at generation time to "not say anything regulated" but the meaning of "regulated" is jurisdiction-specific and context-specific; a prompt cannot encode the full action matrix. Second, even when the prompt is well-crafted, the agent's output is the very thing the prompt is meant to constrain - there is no independent check that the constraint was honoured. Conventional content filters (toxicity scoring, basic PII redaction) catch a subset of failures but operate on a different signal: they look at words, not at the regulatory category of the response or at the agent's calibrated confidence in the answer.

The transparency obligations now in force in regulated jurisdictions raise the bar further. EU AI Act Articles 13 and 14 require that providers of high-risk AI systems supply users with information about the system's capabilities, limitations, and accuracy, and ensure effective human oversight over its operation (European Union, 2024). Article 50 requires that certain categories of AI system - chatbots, emotion-recognition systems, and biometric categorisation systems - inform the natural person they are interacting with that they are interacting with AI, and that AI-generated synthetic content is detectable as such (European Union, 2024). None of these obligations is met by an unclassified, unreviewed, unredacted output stream.

This control reduces risk by enforcing classification of every final agent response immediately before delivery, attaching obligations (redact, hold for review, route to a human) based on a signed action matrix, and producing an evidence event per response that records what was classified, what obligations applied, and what the delivered output was.

#### What

A pre-delivery classification and obligation service that sits between the agent runtime and any downstream consumer of the agent's final response, evaluates the response against a signed output classification bundle, and emits a classification event per response.

The control consists of three mechanisms:

A classification engine that runs on every final agent response immediately before delivery. The engine consumes the response content and a signed output classification bundle. The bundle defines: the set of sensitivity tiers in use at this organisation (a normative enumeration, not a free list), the set of regulated content categories the organisation tracks (medical, legal, financial, HR, immigration, jurisdiction-specific child safety, others as configured), the confidence threshold below which a response is held for review, the action matrix that maps the cross-product of sensitivity tier, regulated category, and autonomy tier to a set of obligations.

A confidence scoring component that produces a structured confidence score on the response in the [0, 1] range. The score is derived from the model's logprobs where available and from a calibrated proxy where not. The score is a property of the response as a whole; per-claim confidence scoring is out of scope for this control and is left to future versions. The confidence score is included in the classification event and is the input to the hold-for-review obligation.

An obligation router that consumes the classification output and applies the obligations defined by the action matrix. Three obligation types are defined: `redact_fields` (specific fields in a structured response are zeroed or replaced with the standard redaction marker), `hitl_review` (the response is held until a HITL approval record arrives), `hold_for_review` (the response is held until a confidence-threshold review record arrives). Obligations compose: a single response can require both redaction and HITL review.

Invariants the control guarantees:

- Every final agent response produces exactly one `gate.output.classification` event in the ledger before delivery. There is no delivery path that bypasses classification.
- The output classification bundle is signed (C03) and its hash is recorded in the classification event so a classification decision can be replayed (C10).
- Classification events are immutable evidence (C11 ledger) and correlate to the run ID and trace ID of the originating agent run.
- Where a regulated category and high-privilege tier combination triggers a `hitl_review` obligation, the delivery is gated on the HITL Decision Record arriving and resolving to `approve`. The fail-closed default is hold, not deliver.

#### Distinction from C13 and C19

The boundary with C13 and C19 is the architectural property of this control that prevents three controls from collapsing into one. It is stated here normatively.

C13 captures intent telemetry on a per-run basis: which tools the agent considered, which it chose, what category of decision it made, what the structured intent shape was. C13 events are produced during the run, before the final response is composed. C13 is the per-run intent signal.

C19 observes the distribution of behaviour over time and emits drift decisions and response actions on a defined cadence. C19 operates on aggregated telemetry across many runs; a single response does not move a C19 distribution by a detectable amount. C19 is the aggregate drift signal.

C20 inspects the content of each final response at delivery and emits one classification event per response. C20 operates on the response itself; it does not look at the agent's reasoning, its tool choices, or its trajectory through the run. C20 is the per-response content signal.

These are different signals operating at different cadences on different artifacts, and they must not be merged. A system that runs only C13 will have rich intent telemetry and will deliver regulated content without classification. A system that runs only C19 will detect that the agent has shifted into producing more regulated-category responses on average, weeks after the first such response was delivered. A system that runs only C20 will classify every response correctly and learn nothing about the agent's intent or its drift. All three controls are required for high-privilege tier; any one alone is insufficient.

The three controls share an evidence destination (C11 ledger) and a common correlation key (`run_id`, `trace_id`) but have independent decision logic, separate bundles, and distinct ledger event types: `gate.observability.semantic_event` (C13), `gate.assurance.drift_decision` and `gate.assurance.response_action` (C19), and `gate.output.classification` (C20).

#### How

**Control-plane flow.** The classification engine runs as the last hop before the agent runtime returns its final response to the calling system. It receives the response content, the run context (run_id, trace_id, tenant_id, environment, autonomy_tier), and a reference to the active output classification bundle. The engine produces a classification result (sensitivity tier, regulated categories, confidence score) and an obligation list, then emits a `gate.output.classification` event into the C11 ledger. If the obligations are empty, the response is delivered. If `redact_fields` is present, the field-level redactions are applied to the response before delivery. If `hitl_review` is present, the response is held in a review queue and the calling system receives a hold acknowledgement with a review ticket identifier; delivery resumes when the HITL Decision Record arrives with `approve`. If `hold_for_review` is present (confidence-threshold review), the response is held pending a confidence-threshold review record from the designated reviewer.

**Deployment.** The classification engine runs inside the agent runtime container as a deterministic post-generation hook, or as a sidecar that the runtime calls synchronously before delivery. Both deployment shapes are valid; the choice is driven by the runtime's tolerance for additional in-process logic. The output classification bundle is loaded at agent start, signature is verified at load time (C03), and the bundle hash is held in memory for inclusion in each classification event. The HITL review queue and the confidence-threshold review queue are persistent queues with retention sufficient to cover the review SLA.

**Action matrix.** The action matrix is configuration-driven, not hardcoded. It is expressed as a YAML structure inside the output classification bundle. Each entry specifies a combination of sensitivity tier (one value), regulated categories (zero or more values), autonomy tier (sandbox, bounded, high_privilege), and confidence band (a closed interval over [0, 1]). For each matching combination the entry lists the obligations to apply. Multiple entries can match a single response, in which case the obligation lists are merged. The bundle MUST contain a default entry that matches any unmatched combination at high_privilege tier; the default is `hold_for_review` to enforce fail-closed behaviour. The bundle is versioned, signed, and ships under the same change-control bar as the policy bundle.

**Streaming output.** Streaming output to the user is disabled at high_privilege tier for any agent whose action matrix can produce a `hitl_review` or `hold_for_review` obligation. The response is buffered until the classification event is emitted and the obligations are applied. Streaming to internal logging and to trace destinations is unaffected. This constraint applies in v1.4 pending the streaming-aware classification path scoped to v1.5; the disablement is not a permanent architectural property of C20.

**Safe rollout.** Begin in flag-only mode for thirty days. During this period, classification events are emitted and the action matrix is evaluated, but no obligation is applied to the response. This establishes the false-positive rate per regulated category and the baseline distribution of confidence scores. After flag-only, promote `redact_fields` obligations first (lowest blast radius - the response still goes out, but with redactions applied). Promote `hold_for_review` next (delivery is delayed but not blocked indefinitely). Promote `hitl_review` last and only after the HITL review SLA is demonstrated to be reliable; an unreliable HITL queue with `hitl_review` enforced produces a denial-of-service against the agent's users.

**Testing.** Synthetic input injection in CI. For each regulated category in the action matrix, maintain a test corpus of responses that should classify into the category and a counter-corpus that should not. Run both through the engine on every bundle change and confirm the classification matches expectations. For confidence scoring, maintain a calibration test that confirms the score distribution on a held-out set is consistent with the score the engine was calibrated against. For the action matrix, maintain a coverage test that confirms every reachable cross-product of inputs produces a non-empty obligation list (no silent passes).

**Integration with C13.** C13 events and C20 events share `run_id` and `trace_id` and can be correlated for forensics and replay. An auditor reconstructing a single agent interaction reads the C13 events to see the intent and the trajectory and reads the C20 event to see the classification of the final response.

**Integration with C19.** The C19 baseline can include the distribution of C20 classification outcomes (sensitivity tier distribution, regulated category distribution, confidence score distribution, obligation distribution) as additional dimensions. A drift in the rate at which the agent produces regulated-category responses is itself a C19 signal. The C19 baseline schema is extensible to consume C20 outcomes; the integration is recommended at high_privilege tier.

**Integration with C09.** Where the output classification bundle specifies `hold_for_review` and the response is never approved, the response is permanently held. This is not an invariant halt; it is a delivery suspension. The distinction matters: an invariant halt is a hard stop on the agent's authority to act; a delivery suspension is a hold on a specific response that may or may not be released. C09 is not invoked by C20 obligations.

**Integration with HITL.** C20 uses the existing HITL Decision Record contract for `hitl_review` obligations. The HITL Decision Record is single-approver in v1.4 (see "Known scope boundaries" below); a multi-approver HITL extension is forthcoming in v1.5.

#### Evidence

- `gate.output.classification` event per final response: `schema_version`, `event_type`, `time`, `run_id`, `trace_id`, `tenant_id`, `environment`, `output_hash` (sha256 over canonical serialisation of the response), `classification` (object: `sensitivity_tier`, `regulated_categories` array, `confidence_score`, `requires_human_review` boolean), `obligations` (array of obligation strings: `redact_fields`, `hitl_review`, `hold_for_review`), `bundle_hash`, `ledger_event_id`.
- HITL Decision Record per response that triggered `hitl_review` (existing schema, see C09 and the contracts repository).
- Hold-for-review approval record per response that triggered `hold_for_review` (re-uses the HITL Decision Record schema with a `review_type` discriminator).
- Output coverage metric: `% of final agent responses with a corresponding gate.output.classification event`. Target 100% at bounded and high_privilege tier.
- Regulated category review SLA metric: median and 95th percentile time from `hitl_review` obligation emission to HITL Decision Record arrival, per regulated category, computed weekly.
- Obligation distribution: count of responses per obligation type per agent per week, used to track operational load on the review queues.
- Bundle integrity report: signed output classification bundle hash matches the hash recorded in classification events.

#### Failure modes

- Bypass via streaming output. The agent runtime streams tokens to the user as they are generated, and the classification engine runs only on the final response. Tokens reach the user before classification can hold them. Mitigation: at high_privilege tier and for any agent whose action matrix can produce a `hitl_review` or `hold_for_review` obligation, streaming output to the user is disabled and the response is buffered until the classification event is emitted and the obligations are applied. Streaming to internal logging is unaffected.
- Action matrix coverage gaps. The matrix has a default entry but the default is `pass`, not `hold_for_review`. Combinations not enumerated in the matrix slip through. Mitigation: the bundle's default entry at high_privilege tier MUST be `hold_for_review` per the schema; a CI check on the bundle rejects bundles whose default is `pass`.
- Confidence score misuse. Operators treat the confidence score as a per-claim accuracy score rather than as a calibrated proxy for the response as a whole, and tune thresholds against a metric the score does not represent. Mitigation: the bundle documents the score's semantics in a free-text field; the conformance check asks whether the operator has documented their interpretation of the score.
- Review queue saturation. A poorly tuned action matrix puts a large fraction of responses into `hitl_review`. The queue grows without bound, response latency degrades, and users experience the system as broken. Mitigation: the action matrix is rolled out per regulated category and per autonomy tier with explicit volume forecasts; a tracked metric on queue depth raises an alert before saturation.
- Redaction over-application. The `redact_fields` obligation is applied broadly and useful fields are zeroed in normal responses. Mitigation: the action matrix specifies `redact_fields` per regulated category; redaction is applied only to the named fields, not to the whole response. A negative test confirms unaffected fields are unchanged.
- Confusion with C13 or C19. Operators reading a runbook for an output-related incident look first at C13 traces (intent) or C19 dashboards (drift), miss the C20 classification event, and misdiagnose the cause. Mitigation: documentation and the event type distinction make the C13 / C19 / C20 boundary explicit; runbooks for output-related incidents start at the C20 event for the affected run_id.
- Bundle versioning drift between runtime and ledger. The runtime is loaded with bundle version N; classification events claim bundle version N; an auditor reads the ledger and looks up the bundle and gets version N+1 (the version currently in the bundle store). Mitigation: the classification event records `bundle_hash`, not `bundle_version`; the auditor verifies by hash, not by version label.
- Classifier false-negative on sensitive content. The classifier itself misses content that should classify into a regulated category. This is distinct from action-matrix coverage gaps (the matrix has no entry for the combination) and from confidence signal degradation (the score is uninformative). This is the classifier being wrong even when the matrix is right and the score is calibrated. Mitigation: routine evaluation of classifier accuracy against a held-out test set per regulated category, with results stored as evidence; alert on accuracy degradation against the test set baseline; the test set itself is signed and versioned alongside the bundle.
- Synchronous classifier latency. The engine runs on every final response before delivery. If the engine is slow (it calls another model, it runs a heavy rule set, it hits a network round trip), every response carries that latency. At p99 the result is user-facing timeout and a perceived outage. Mitigation: an explicit classifier latency SLO in the bundle; p50 and p99 latency metrics in the evidence set, computed continuously and tracked per regulated category; alert on degradation against the SLO; a documented degraded-mode behaviour for the case where the SLO cannot be met (recommended degraded mode: emit the classification event with the obligations as configured and decline delivery rather than degrade silently).
- Confidence signal unavailable. The model provider stops returning logprobs; the calibrated proxy degrades; confidence scores drift toward an uninformative midpoint. Mitigation: the bundle's confidence threshold is calibrated against the current score distribution; a drift detector (per C19) on the score distribution itself raises an alert when the distribution shifts.
- Single-approver HITL bottleneck. A regulated category that should require dual approval is gated on a single approver because v1.4 HITL is single-approver. Mitigation: documented forward-looking scope boundary noting that dual-approver HITL arrives in v1.5; operators that require dual approval today use the break-glass record path (Workstream 2 contract) as a manual workaround until v1.5.

#### NIST AI RMF alignment

C20 maps to **GOVERN**, **MEASURE**, and **MANAGE**. GOVERN: the control implements GV-3 (workforce diversity, equity, inclusion, and accessibility processes are prioritized in the mapping, measurement, and management of AI risks) by routing regulated content to humans whose role is to evaluate the response in context. MEASURE: the control implements MS-2.10 (output quality is monitored over time) by emitting a structured classification event per response, MS-2.11 (fairness and bias of AI system outputs is examined and documented) where the regulated category set includes bias-relevant categories, and MS-3 (mechanisms for tracking identified AI risks over time are in place). MANAGE: the control implements MG-3 (AI risks and benefits from third-party resources are regularly monitored, and risk controls are applied and documented) by enforcing redaction and review obligations on responses that touch third-party data. Rationale (short): Per-response content classification with documented obligations and human-in-the-loop review for regulated categories.

#### ISO/IEC 42001 alignment

C20 maps to **A.6.2.6 (AI system intended use)**, **A.7.4 (data quality)** to the extent that response quality is bound to the quality of the response generation step, **A.8.3 (information for interested parties)** by ensuring the response delivered to the user is the response that was classified and approved, **A.9 (performance monitoring of AI systems)**, and **clause 8.1 (operational planning and control)** for the operational planning of the review queues and the action matrix maintenance. Typical evidence produced: signed output classification bundle per ABOM version, classification events per response, HITL Decision Records for reviewed responses, action matrix change history.

#### OWASP AISVS alignment

C20 maps directly to AISVS C4.1 (Output gating before delivery) and AISVS C4.2 (Output content classification). C4.1 requires that output be gated before delivery to the user; C20 is the GATE-side enforcement surface for this requirement, with the classification engine running on every final response and the obligation router applying redact, hold, or review obligations from a signed action matrix. C4.2 requires that output content be classified into the operator's regulated category taxonomy with a confidence signal attached; C20's `gate.output.classification` event carries the `sensitivity_tier`, `regulated_categories`, and `confidence_score` fields that satisfy this requirement directly. Check20 verifies coverage (every final response produces a classification event), bundle hash integrity, obligation distribution stability, and the fail-closed default at high_privilege tier. See `owasp-aisvs.yaml` for the full per-requirement mapping; full coverage on C4.1 and C4.2.

#### MITRE ATLAS alignment

C20 maps to four ATLAS techniques in the External Harms and Exfiltration categories. **AML.T0048 (External Harms):** C20 gates output content before delivery, complementing C05's tool-call authorisation. The output classification engine catches the case where an action did not require a tool call but the response itself carries regulated content. Coverage: full. **AML.T0049 (Exfiltration via ML Inference API):** C20 gates output content; C07 limits exfiltration volume on the tool-call side. The two controls operate at different exfiltration paths. Coverage: full. **AML.T0024 (Exfiltration via ML Inference API):** identical operationally to T0049 in the current ATLAS taxonomy. **AML.T0067 (LLM Trusted Output Components Manipulation):** C20 gates the trusted output surface; the Check20 fail-closed guardrail at high_privilege tier catches the specific case where the action matrix yields no obligations on a response that should be held. Coverage: full. See `mitre-atlas.yaml` for the per-technique detail and the relationship to the C16 adversarial robustness harness coverage list.

#### NIST SSDF alignment

C20 falls outside the NIST SSDF intersection scope. SSDF (NIST SP 800-218 v1.1) is software-development-lifecycle scope: prepare the organisation, protect the software, produce well-secured software, respond to vulnerabilities. C20 is an agent-runtime output-validation control. The two surfaces do not intersect: SSDF does not prescribe per-response output classification, and C20 does not address the SDLC discipline SSDF expects. C20 is listed in `nist-ssdf.yaml` only by exclusion (not in the gate_controls list of any SSDF practice). This is a deliberate boundary, not a gap: operators pair GATE with an SDLC discipline upstream of agent deployment per the scope note in the SSDF mapping file. The GATE controls that do intersect SSDF are C03 (at PS.2.1 for runtime-retrieved-content provenance, and at PW.4.1 alongside C18 for chain-to-registered-source), C18 (at PW.4.1 alongside C03), and C05 (at PW.9.1 for the fail-closed Tool Gateway default).

#### EU AI Act alignment

C20 supports compliance with the EU AI Act in three specific articles. The control does not by itself make a system Act-compliant; compliance is a property of the system as a whole and includes obligations that GATE does not cover (conformity assessment, registration, technical documentation under Annex IV). Where the Act's obligations relate to output behaviour, C20 is the GATE-side mechanism.

**Article 13 (Transparency and provision of information to deployers).** Article 13 requires that high-risk AI systems be designed and developed in a way that ensures their operation is sufficiently transparent to enable deployers to interpret the system's output and use it appropriately (European Union, 2024). The classification event produced by C20 is the per-response transparency artifact: it records the sensitivity tier of the response, the regulated categories that apply, the confidence score, and the obligations that attached. A deployer reading the ledger has the per-response evidence needed to evaluate whether the system is operating within the intended limits documented in the system's instructions for use.

**Article 14 (Human oversight).** Article 14 requires that high-risk AI systems be designed and developed in a way that ensures they can be effectively overseen by natural persons during the period in which they are in use, including measures that enable persons to intervene in the operation of the system or interrupt it through a "stop" button or similar procedure (European Union, 2024). The `hitl_review` and `hold_for_review` obligations are the GATE mechanism by which Article 14 oversight is exercised at the response level. The conformance check below verifies that the oversight mechanism is configured, that the review SLA is documented, and that the queue is monitored.

**Article 50 (Transparency obligations for providers and deployers of certain AI systems).** Article 50 requires, among other obligations, that providers of AI systems intended to interact directly with natural persons inform them that they are interacting with an AI system unless this is obvious from the context, and that providers of AI systems generating synthetic content mark that content in a machine-readable format and detectable as artificially generated (European Union, 2024). The classification event records that a response was AI-generated and the response can carry a machine-readable marker derived from the event. The classification event also records the model identity from the ABOM, satisfying the provenance side of Article 50.

These mappings are operational, not legal. Counsel determines whether a specific system is in scope for any specific article. The C20 conformance evidence supports that determination; it does not make it.

#### Conformance check (self-assessment pattern)

```yaml
- id: C20
  name: Agent-to-Human Output Validation
  layer: 3
  depends_on:
    - C11
    - C13
  classification: PARTIAL
  questions:
    - id: C20.Q1
      text: Does every final agent response produce a gate.output.classification event in the ledger before delivery?
      evidence_required:
        - Sample gate.output.classification events from the last 30 days
        - Coverage metric showing 100% of final responses classified
    - id: C20.Q2
      text: Is the output classification bundle signed, versioned, and loaded with hash verification at agent start?
      evidence_required:
        - Bundle signature verification log
        - Sample classification event showing bundle_hash matches active bundle
    - id: C20.Q3
      text: Does the action matrix cover the cross-product of sensitivity tier, regulated categories, autonomy tier, and confidence band, with a default entry that holds for review at high_privilege tier?
      evidence_required:
        - Output classification bundle YAML
        - CI test confirming default entry behaviour at high_privilege tier
    - id: C20.Q4
      text: Are hitl_review obligations gated on a HITL Decision Record arriving and resolving to approve before delivery?
      evidence_required:
        - Sample held responses with the corresponding HITL Decision Records
        - Median and 95th percentile review SLA per regulated category
    - id: C20.Q5
      text: Is streaming output to the user disabled for agents whose action matrix can produce hitl_review or hold_for_review obligations at high_privilege tier?
      evidence_required:
        - Runtime configuration showing streaming disabled
        - Documented exception list and rationale where streaming is permitted
    - id: C20.Q6
      text: Has the control been promoted from flag-only to enforce mode, and is the obligation distribution stable enough for production operations?
      evidence_required:
        - Documented promotion criteria and date of promotion
        - Obligation distribution metrics for the last 30 days
        - Review queue depth metrics for the last 30 days
  conformance_levels:
    sandbox: optional
    bounded: required (flag-only minimum; events emitting, sensitivity_tier populated, human review gate wired for regulated categories)
    high_privilege: required (enforce mode; action matrix enforced; hold_for_review and hitl_review obligations active for configured categories)
```

Classification rationale (PARTIAL): the coverage metric (% of final responses with a classification event), the bundle hash integrity, and the obligation distribution are all queryable from the ledger and automatable. The human review workflow verification (Q4) and the streaming policy verification (Q5) require process inspection by the operator. PARTIAL is the correct disposition. The split is the same shape as Check17 (C18 Data Quality Gates) and Check18 (C19 Model Behaviour Monitoring).

#### Required changes to gate-contracts

One new event schema. All field types follow the existing JSON Schema draft used by the repository (Draft 2020-12).

`schemas/output/output_classification_event.schema.json`:
- `schema_version` (string, semver)
- `event_type` (const: `gate.output.classification`)
- `time` (string, date-time)
- `run_id` (string, uuid)
- `trace_id` (string; freeform per the existing v1.3 contracts convention, not uuid-formatted)
- `tenant_id` (string)
- `environment` (string)
- `output_hash` (string, sha256 over canonical serialisation of the response)
- `classification` (object):
  - `sensitivity_tier` (string, value drawn from the bundle's sensitivity tier enumeration)
  - `regulated_categories` (array of strings, values drawn from the bundle's regulated category enumeration)
  - `confidence_score` (number, 0-1, inclusive)
  - `requires_human_review` (boolean)
- `obligations` (array of strings, allowed values: `redact_fields`, `hitl_review`, `hold_for_review`)
- `bundle_hash` (string, sha256)
- `ledger_event_id` (string, uuid)

Ledger event type registry (`event_types.yaml`):
- Add `gate.output.classification` with retention class `output-evidence` (new retention class, defined as the same retention duration as `assurance-evidence`).
- **[ERRATA - reversed by `paper-updates/01-C20-errata.md` Erratum 2 (2026-06-23).]** The instruction above is stale. No `event_types.yaml` artifact exists in gate-contracts; the event-type registry mechanism is the `event_type` const field on each event schema (declared on `output_classification_event.schema.json` for this control). Category-style retention classes (`output-evidence`, `assurance-evidence`) are not used in the repo; the `audit_ledger_event.immutability.retention_class` enum is duration-based with four values (`sandbox_hot_30d | prod_hot_365d | prod_cold_6y_worm | regulated_cold_7y_plus`). C20 events use a per-event retention class selected from this enum by the action-matrix entry that classified the response. No new file is added in v1.4.

Extension to `schemas/abom/abom.schema.json`:
- Add optional `output_classification_bundle_hash` (sha256) field linking an ABOM version to its active output classification bundle.

Compatibility note: All v1.2.0 schema changes are backward-compatible with v1.1.1. The new event type is additive; the `abom.schema.json` extension is optional with a documented default of null.

#### Required changes to gate-policies

A new Rego file at `policies/output/c20_output_classification.rego` (NOT added to `tool_gateway_baseline.rego`). Package: `gate.output`. The file expresses three policy rules:

- `classify_response`: given the response content (or its hash), the active output classification bundle, and the autonomy tier, evaluates the classification and emits the classification object and the obligation list. The action matrix is read from the bundle; no obligation values are hardcoded in the rego.
- `requires_human_review`: given a classification, evaluates whether the response requires human review based on the action matrix and the autonomy tier. The default at high_privilege tier MUST be `true` for any classification combination not covered by an explicit pass-through entry.
- `enforce_default_high_privilege_hold`: a guardrail rule that denies any classification result at high_privilege tier whose obligation list is empty unless an explicit pass-through entry in the action matrix matched.

Tests at `policies/output/c20_output_classification_test.rego` cover:
- High-sensitivity output at high_privilege requires human review.
- Regulated category detected triggers redact obligation.
- Low-sensitivity output at bounded tier passes without review.
- Confidence below threshold triggers hold_for_review.
- The high_privilege default produces a non-empty obligation list when no explicit entry matches.

#### Required changes to gate-python

A new module at `gate/output/__init__.py` (NOT added to existing modules). Public surface:

- `build_output_classification_event(run_id, trace_id, output, classification, obligations, ledger_event_id, tenant_id, environment) -> dict`: returns a conformant `gate.output.classification` event. `output_hash` is computed from `gate_hash(output)` (canonical JSON + sha256, matching the existing hash function used elsewhere in the library).
- `evaluate_output_sensitivity(output_text, classification_bundle, autonomy_tier) -> dict`: pure function. Returns a classification dict with `sensitivity_tier`, `regulated_categories`, `confidence_score`, and `requires_human_review`.
- `apply_output_action_matrix(classification, autonomy_tier, action_matrix) -> list[str]`: returns the obligation list. The action matrix is the structured form of the bundle's matrix section, passed in as a parameter rather than hardcoded.
- `class OutputClassificationBundle(BaseModel)`: loads, signs, and verifies the bundle. Holds the action matrix in a structured form usable by `apply_output_action_matrix`.

Tests in `tests/output/test_classification.py` cover:
- `build_output_classification_event`: correct event_type, hash computed.
- `evaluate_output_sensitivity`: high-sensitivity returns `requires_human_review`.
- `apply_output_action_matrix`: regulated category triggers redact.
- High_privilege default produces non-empty obligation list when no explicit entry matches.

Validation in `gate/validation.py`:
- Add `validate_output_classification_event` following the existing `validate_*` pattern.

#### Known scope boundaries

These are explicit boundaries on what C20 covers in v1.4. Each is a candidate for v1.5 work.

- **Per-claim confidence scoring.** C20 produces one confidence score per response. A response that contains multiple distinct claims, only some of which are low-confidence, is treated as a single artifact. Per-claim scoring is a model-side capability that GATE does not own.
- **Multilingual classification.** The regulated category set is configured per organisation and per jurisdiction. The bundle does not impose a multilingual category vocabulary. Operators deploying agents across jurisdictions configure their bundle accordingly.
- **Streaming-aware classification.** v1.4 disables streaming at high_privilege tier for agents whose matrix can produce hold or review obligations. A streaming-compatible classification path (incremental classification, partial-response holds) is out of scope for v1.4 and is a candidate for v1.5.
- **Dual-approver HITL on output review.** v1.4 HITL Decision Record is single-approver. Where regulated category review requires dual approval, the break-glass record path (Workstream 2 contract) is the manual workaround. Dual-approver HITL is a v1.5 deliverable.
- **Unified exception register.** The output classification bundle does not currently reference the unified exception register (the `data.gate.exceptions` surface referenced by C09, C17, C18, C19). The unified exception lifecycle contract is a v1.5 deliverable; until then, exceptions to the action matrix are recorded in the bundle change history and tracked outside the ledger.

#### References

European Union (2024) *Regulation (EU) 2024/1689 of the European Parliament and of the Council of 13 June 2024 laying down harmonised rules on artificial intelligence (Artificial Intelligence Act)*. Official Journal of the European Union, L 2024/1689.
