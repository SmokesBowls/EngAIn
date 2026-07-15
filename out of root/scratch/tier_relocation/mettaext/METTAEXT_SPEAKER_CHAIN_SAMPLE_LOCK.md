# METTAEXT SPEAKER CHAIN SAMPLE LOCK

Purpose: document the current Mettaext speaker-chain sample result for MrLore review without changing Pass 1, Pass 2, Pass 3, canon, runtime, or tool code.

## Authority / Scope

This is a review lock only.

It does not change canon.
It does not write runtime truth.
It does not patch pipeline behavior.
It does not create tools.
It records the sample result and the tier-path command form MrLore can use for review.

## New Paths

Raw chapter source:

```text
tier1/mrlore/raw/chapters/
```

Mettaext package:

```text
tier3/mettaext/
```

Passroom modules:

```text
tier3.mettaext.passroom.*
```

Scratch test output:

```text
scratch/mettaext_speaker_test/
```

## Test Command Form

Run from the EngAIn repo root:

```bash
cd /home/mytruelove/Desktop/burdens_of_a_forgotten_past/EngAIn
```

Pass 1 explicit dialogue extraction:

```bash
python3 -m tier3.mettaext.passroom.pass1_explicit \
  --input tier1/mrlore/raw/chapters/<chapter-file>.txt \
  --output scratch/mettaext_speaker_test/pass1_explicit.json
```

Pass 2 enhanced speaker inference:

```bash
python3 -m tier3.mettaext.passroom.pass2_enhanced \
  --input scratch/mettaext_speaker_test/pass1_explicit.json \
  --output scratch/mettaext_speaker_test/pass2_enhanced.json
```

Pass 3 merge:

```bash
python3 -m tier3.mettaext.passroom.pass3_merge \
  --pass1 scratch/mettaext_speaker_test/pass1_explicit.json \
  --pass2 scratch/mettaext_speaker_test/pass2_enhanced.json \
  --output scratch/mettaext_speaker_test/pass3_merge.json
```

Use the real module path form:

```text
python3 -m tier3.mettaext.passroom.<pass_module>
```

Do not use the old root module form:

```text
python3 -m mettaext.passroom.<pass_module>
```

## Locked Sample Results

```text
TOTAL_DIALOGUE=84
TOTAL_UNKNOWN=7
UNKNOWN_RATE=0.0833
PRONOUN_SPEAKERS=6
```

## Interpretation

Unknown speaker is now a review queue, not a mass pipeline failure.

Pronoun speaker is a resolution candidate, not a final named actor.

Inferred speaker is evidence, not canon.

MrLore reviews unresolved ambiguity.

## Final Booleans

```text
METTAEXT_SPEAKER_CHAIN_SAMPLE_LOCK_WRITTEN=TRUE
MRLORE_NEW_PATHS_DOCUMENTED=TRUE
MRLORE_CAN_TEST_WITH_TIER_PATHS=TRUE
MRLORE_CANON_NOT_CHANGED=TRUE
```
