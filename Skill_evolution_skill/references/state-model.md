# State Model

## 1. EvolutionTransaction

建议字段：

- transaction_id
- created_at
- trigger_type
- host_framework
- source_skill_id
- source_skill_version
- related_trace_ids[]
- status
- decision_summary
- recommended_action

`status` 建议值：
- detected
- normalized
- attributed
- candidate_generated
- validated
- review_required
- finalized
- rejected

## 2. EvolutionReport

建议字段：

- report_id
- transaction_id
- trigger_type
- skill_name
- task_summary
- input_summary
- observed_failure
- user_feedback
- environment_notes
- evidence[]

## 3. SkillCandidate

建议字段：

- candidate_id
- candidate_type            # patch | replacement | composition
- parent_skill_id
- parent_skill_version
- derived_from_report_id
- rationale
- proposed_changes_summary
- candidate_location
- validation_status
- promotion_status

`promotion_status` 建议值：
- draft
- experimental
- stable
- deprecated
- archived

## 4. ValidationResult

建议字段：

- validation_id
- candidate_id
- checks_run[]
- passed
- failed_checks[]
- warnings[]
- smoke_test_summary
- compared_against_parent

## 5. Lineage Links

建议关系：

- patch_of
- replacement_of
- composed_from
- deprecated_by
- triggered_by_trace
