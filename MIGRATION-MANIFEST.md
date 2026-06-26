# MIGRATION-MANIFEST - gate-framework-paper Phase 2

## Source

Frozen v1.4 Google Doc, exported to .docx by Andrew.

- File: `GATE-v1.4-frozen.docx`
- Google Doc ID: `1Y5hIsor2TIDTVv0WpjxtjobTYA4iDk8_LPNjHjWruQU`
- Doc title: "GATE v1.4 paper - PRE-PIVOT FROZEN REFERENCE 2026-06-26"
- Size: 2428085 bytes
- sha256: `11038a96215aedb26a421ba89e512a3e6749e6a75d90a49d892886496b8f5233`
- Acquired (UTC): 2026-06-26T16:53:41Z


## Pandoc conversion (Part B)

- Command: `pandoc GATE-v1.4-frozen.docx -o v1.4-converted.md --extract-media=... --wrap=none --markdown-headings=atx --reference-links=false` (run via Quarto's bundled Pandoc 3.8.3)
- Exit code: 0
- Output: 4317 lines
- Media files extracted: 10 (expected 11). The 11th, the GitHub avatar, was not
  extracted: it sits in the docx header, which Pandoc does not import. The hero
  (image3, 1000x525) was extracted but, like the avatar, is not referenced in the
  body; it is placed manually on the cover. All 9 figures extracted and mapped.

## Media mapping (Part B.3)

| Pandoc file | Repo name | Native px | Figure |
|---|---|---|---|
| image3 | hero.png | 1000x525 | Hero / cover |
| image8 | figure-threat-model.png | 1386x854 | TM (threat model) |
| image2 | figure-ra-1.png | 869x1110 | RA.1 trust pipeline |
| image7 | figure-ra-2.png | 1208x1225 | RA.2 logical arch |
| image4 | figure-c17-1.png | 884x1137 | 17.1 C17 discovery |
| image5 | figure-c19-1.png | 627x1359 | 19.1 C19 drift |
| image11 | figure-cloud-a-minimal-reference.png | 800x1038 | A.1 minimal ref |
| image1 | figure-cloud-c-aws.png | 877x1489 | C.1 AWS |
| image10 | figure-cloud-d-azure.png | 882x1489 | D.1 Azure |
| image6 | figure-cloud-e-gcp.png | 875x1513 | E.1 GCP |
| (absent) | github-avatar.png | 460x460 | in docx header, not imported |

## Control include refactoring (Part D)

- C20: rendered from `controls/C20-output-validation.md` via `chapters/_includes/C20.qmd`, nested in `13-control-catalog-layer-3.qmd`. Source-of-truth include pattern established.
- C01-C19: inlined from frozen-Doc migration. Paper-form on-disk specs do not exist (only T1520 gate-knowledge KB articles, a different format). Surfaced in `DRIFT-FINDINGS.md`.

## Build verification (Part E)

- quarto render: PDF + HTML both EXIT 0.
- Cross-reference warnings: 0 (no `?@` markers in HTML, no undefined-reference warnings in PDF log).
- PDF: 151 pages, 0 blank pages (KOMA `open=any` + empty-heading removal).
- Em-dash (U+2014): 0. American "defense": 0. Three Path-2 capitalization regressions: 3 fixed.

### PDF spot-check (Part E.3) - 5 pages, all PASS

- Cover (p7): hero image present and centered; title, subtitle, version, copyright, license, attribution, disclaimer all render.
- Control entry (p66, Control 05): Why/What/How/Evidence structure intact, bullet lists correct.
- Controls at a Glance (p31): adoption-path section renders.
- Conformance (p103): Conformance Check entries with Requirement/Evidence intact.
- Standard Mappings (p112): orientation text faithful to frozen Doc; full per-control alignment tables are Phase 3 (pu06), correctly absent.

## Source digest chain (Part F.1)

- Source files hashed: 43 (index.qmd, chapters/, controls/, assets/, references.bib, harvard.csl, _quarto.yml)
- Chain sha256 (sha256 over the sorted per-file digest list): `e23dabc816b36399c22a15055f5bedddaf8c6ce9eb3605c78e810c7925970605`

## Snapshot

- Name: `gate-framework-paper-phase-2-migration-2026-06-26T1905`
- Trigger: Phase 2 of v1.4 framework paper pipeline pivot. Content migration from frozen v1.4 Doc. Control chapters refactored to render from on-disk specs (source-of-truth discipline) where format-compatible specs exist (C20). C20 added via include of corrected T1520 spec. Drift findings captured for separate triage.
