# AIDER_DISPATCH_SURFACE_001

This is the active manual dispatch surface for Aider support-runner tasks.

Aider receives declared work.
Aider does not choose work.

Aider does not choose:
- repo path
- lane
- files
- gates
- acceptance

The task packet declares all of that before Aider begins.

## Folders

incoming/
  Human-approved task packets not yet run.

working/
  Active task packet copy and live notes while Aider is operating.

completed/
  Result packets for tasks Aider claims completed.

failed/
  Result packets for tasks Aider could not complete or that returned FALSE.

## Required Aider Loop

1. Read packet first.
2. Echo boundary fields.
3. Run reproduction before patching.
4. Patch only files in scope.
5. Run post-edit gate.
6. Run declared regressions.
7. Write result packet.
8. Stop for human acceptance.

## Aider Stop Conditions

Aider must stop if:
- packet is missing
- scope is unclear
- required file is missing and not listed under NEW_FILES_ALLOWED
- reproduction cannot run
- another file is needed
- task asks Aider to decide authority
- task asks Aider to mutate canon, AP, runtime law, visual authority, spatial authority, affect authority, or lore authority
- task asks Aider to operate outside declared target path
- task asks Aider to run as daemon or watcher

FINAL_STAMP: AIDER_DISPATCH_SURFACE_ACTIVE
