# Images

Extracted from the frozen v1.4 Doc during Phase 2 migration (Pandoc media
extraction), renamed descriptively, and resized at reference time to page-fit
widths in the chapters (the docx carried oversized display dimensions).

| File | Source in v1.4 paper | Native px | Displayed |
|---|---|---|---|
| `hero.png` | Title page hero | 1000 x 525 | 70% width (cover) |
| `figure-threat-model.png` | Threat Model (TM) | 1386 x 854 | 95% width |
| `figure-ra-1.png` | Reference Architecture, Trust Pipeline (RA.1) | 869 x 1110 | 60% width |
| `figure-ra-2.png` | Reference Architecture, Logical Architecture (RA.2) | 1208 x 1225 | 70% width |
| `figure-c17-1.png` | Control 17 discovery flow (17.1) | 884 x 1137 | 58% width |
| `figure-c19-1.png` | Control 19 drift monitoring (19.1) | 627 x 1359 | 42% width |
| `figure-cloud-a-minimal-reference.png` | Appendix Cloud Quickstart, minimal reference (A.1) | 800 x 1038 | 58% width |
| `figure-cloud-c-aws.png` | Appendix Cloud Quickstart, AWS (C.1) | 877 x 1489 | 48% width |
| `figure-cloud-d-azure.png` | Appendix Cloud Quickstart, Azure (D.1) | 882 x 1489 | 48% width |
| `figure-cloud-e-gcp.png` | Appendix Cloud Quickstart, GCP (E.1) | 875 x 1513 | 48% width |

## Not present

`github-avatar.png` (native 460 x 460) sits in the docx header. Pandoc does not
import headers, so it was not extracted. The formal title-page treatment
(hero + avatar placement, brand palette) is Phase 4.
