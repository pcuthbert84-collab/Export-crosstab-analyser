# DBSJP subject transition mapping — review register

Updated 13 November 2026. Contains no student identifiers or student grades.

## Decisions confirmed 13 November 2026 (Version 2.8)

| Transition | Decision | Evidence from DCPro | Conversion policy |
|---|---|---|---|
| Y6 Computing → Y7 ICT | **Approved subject transition** | Crosstab (86): Y7 ICT DP1 present for 159; Y6 Computing DP3 present for 152 | Conversion approval remains independent; 60 comparisons classified with existing rules, 92 await conversion |
| Y6 → Y7 Geography | **Explicitly unmapped** | No Year 6 Geography prior-assessment column in Y7 export | No conversion implied |
| Y6 → Y7 History | **Explicitly unmapped** | No Year 6 History prior-assessment column in Y7 export | No conversion implied |
| Y6 → Y7 Technology | **Explicitly unmapped** | No Year 6 Technology prior-assessment column in Y7 export | No conversion implied |
| Y6 → Y7 Drama | Pending review | Y7 Drama DP1 has 159 grades; no Drama DP3 field in Y7 export; no Drama field in Y6 file (87) | No conversion implied |
| Y9 → Y10 Science | Pending review | Crosstab (83): Y9 Science DP3 in 123 rows; Y10 Combined Science DP1 in 99, Biology/Chemistry/Physics DP1 in 17 each | Descriptor → double GCSE / separate GCSE require their own approval |

No-mapping decisions stop the dashboard proposing a replacement previous-year subject; they do not erase any already valid direct subject-baseline grade. Student identifiers and results are not included in this document.

## Approved subject mappings (source grade conversions are NOT approved by these decisions)

| Transition | Target | Source subject(s) | Method | Where the prior grade is found | Status |
|---|---|---|---|---|---|
| Year 6 → Year 7 | English | Reading, Writing | Mean of available approved-equivalent source grades | Year 7 student's export, in prior-year assessment columns | Approved by assessment lead in conversation |
| Year 10 → Year 11 | English | English Language | Single source | Year 11 student's export, prior-year examination assessment column | Approved by assessment lead in conversation |
| Year 6 → Year 7 | ICT | Computing | Single source | Year 7 student's export, prior-year assessment column | Approved by assessment lead in conversation |

The app preserves an existing valid baseline and uses student ID + enrolled year to locate prior assessment grades, not current outcomes from a different cohort. Year 7 averaging currently permits one available valid source when the other is absent; discuss whether both should be mandatory.

## Pending — subject leaders and assessment lead to review

All subject names below were found in the uploaded DCPro exports. Presence of a column does not mean that it contains a valid previous-year grade for every student.

| Priority | From → To | Current subject | Potential prior subject heading(s) | Existing gap (assessment records) | Decision needed |
|---|---|---|---|---:|---|
| High | Y9→Y10 | Science | Science, Science - Combined, Science - Biology / Chemistry / Physics | 131 | Check prior-year grade availability and whether single or composite baseline is valid |
| High | Y6→Y7 | Geography | Geography or an approved Humanities aggregate | 159 | Confirm Primary subject grade(s) |
| High | Y6→Y7 | History | History or an approved Humanities aggregate | 159 | Confirm Primary subject grade(s) |
| High | Y6→Y7 | ICT | Computing or ICT | 159 | Confirm curriculum continuity and actual baseline column |
| High | Y6→Y7 | Technology | Technology or Design Technology | 159 | Confirm curriculum continuity and actual baseline column |
| High | Y6→Y7 | Drama | Drama | 159 | Check whether separately assessed in Primary; otherwise unmapped |
| High | Y9→Y10 | Business | Business or another related course | 99 | Check whether this is a new GCSE option (do not force baseline) |
| Medium | Y9→Y10 | Psychology | Psychology or none | 47 | Likely new option; confirm whether progress should remain unavailable |
| Medium | Y9→Y10 | Design Technology | Technology / Design Technology | 28 | Confirm prior subject and scale |
| Medium | Y9→Y10 | BTEC IT | ICT / Computing / Computer Science | 25 | Confirm course comparability and grading rules |
| Medium | Y9→Y10 | Computer Science | Computing / ICT / Computer Science | 23 | Confirm course comparability |
| Medium | Y10→Y11 | Triple Science | Science / constituent sciences | 22 | Define qualification-equivalent composite, if justified |

Potential sources are proposals only. Never use a current-year grade as last year's baseline. Grade conversions, especially Primary / KS3 descriptors vs numeric GCSE grades, require a separate approved conversion table.

## Actual source-column observations

- **Year 7 export: Crosstab (86)** contains `Computing`, `Drama`, `Geography`, `History`, `ICT`, `Science`, and `Technology` subject headings.
- **Year 10 export: Crosstab (83)** contains `Science`, `Science - Biology`, `Science - Chemistry`, `Science - Combined`, `Science - Physics`, `Technology`, `Design Technology`, `ICT`, `Business`, `Psychology`, and `Computer Science` subject headings.
- **Year 11 export: Crosstab (80)** contains `Science - Biology`, `Science - Chemistry`, `Science - Combined`, `Science - Physics`, `Triple Science`, and other examination subjects.

Source-column presence and previous-year grade availability must be checked for each mapping. The listed counts are from the progress-coverage report, not inferred approval counts.

## Implementation notes

- Approvals reside in `approved_subject_transitions.json` with `source_scope: same_cohort_prior_assessment`.
- Unapproved transitions are not added as active rules.
- Approved subject mappings are preselected in the optional same-cohort mapping panel; users can disable them for their session.
- Approved mapping doesn't guarantee classified progress: unsupported grade conversions remain excluded and must be shown in the progress-coverage audit.
- Real student data must not be uploaded to the free Community Cloud prototype.
