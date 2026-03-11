# PlugMem demo pipeline flow (DeepSeek)

```mermaid
flowchart TD
  A[demo_ingest.py] --> B[PlugMem.build_default(db_path)]
  B --> C[_load_local_env: .secrets.env -> os.environ]
  B --> D[_load_config: plugmem/config/default.yaml]
  B --> E[build_llm_from_env -> DeepSeekLLM]

  B --> F[SQLiteStore.initialize]
  B --> G[MemoryGraphStore]
  B --> H[LLMDeduplicator]
  B --> I[EpisodicStandardizer]
  B --> J[SemanticExtractor]
  B --> K[Segmenter]
  B --> L[ProceduralExtractor]
  B --> M[MemoryRetriever]
  B --> N[MemoryReasoner]

  A --> O[PlugMem.ingest(raw_trace, instruction, task_type)]
  O --> P[standardizer.standardize -> Episode/EpisodeStep]
  P --> Q[LLM generate_json: infer state/subgoal/reward]

  O --> R[for step: semantic_extractor.extract]
  R --> S[LLM generate_json: propositions+concepts]
  R --> T[deduplicator.deduplicate_propositions]
  T --> U[LLM judge_duplicate]
  T --> V[write_dedup_audit]

  O --> W[segmenter.segment(episode) -> segments]
  O --> X[for segment: procedural_extractor.extract]
  X --> Y[LLM generate_json: intent+workflow]
  X --> Z[deduplicator.deduplicate_prescription]

  O --> AA[sqlite_store.write_episode/propositions/prescriptions]
  O --> AB[graph_store.add_*]

  A --> AC[prints DB counts + samples]

  subgraph DeepSeek
    DS[DeepSeekLLM] --> DC[OpenAI SDK -> chat.completions.create]
  end
  Q --> DS
  S --> DS
  U --> DS
  Y --> DS
```

## Notes

- `demo_ingest.py` defaults to real DeepSeek; if init fails (missing key, network), it falls back to `FakeLLM`.
- Retrieval path is available via `PlugMem.retrieve(query)`:
  - `MemoryRetriever.retrieve(...)` -> `MemoryReasoner.build_context(...)`

