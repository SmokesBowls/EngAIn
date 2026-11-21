EngAIn — Chapter extraction

Effect: Runs the December 2025 Mettaext pipeline on one chapter, chosen through
the Tier 1 catalog. If that chapter (same text) already has a receipt.json,
nothing runs: it prints the existing receipt and changes nothing. Otherwise it
writes candidate output and receipt.json to
tier3/mettaext/stageroom/output/narrative_to_game/catalog/<book>/<chapter>/<sha12>/
(new files show up in git as untracked). Doesn't touch the vault, 8765 or 8080.


Stageroom — test a real regeneration without touching the repo
Working directory:

cd ~/Desktop/burdens_of_a_forgotten_past/EngAIn
//

PYTHONPATH=. python3 -m tier1.engainos.tools.run_chapter_extraction --catalog-id "book_16_fragmented_beginning/086_sanctuary_to_storm.md" --stageroom /tmp/stageroom_test
//

Effect: Runs the full pipeline into /tmp/stageroom_test instead of the repo.
Compare against the committed folder with:
diff -r /tmp/stageroom_test/output/narrative_to_game/catalog tier3/mettaext/stageroom/output/narrative_to_game/catalog/
(diff will report receipt.json and run.log as different, plus every chapter
you didn't regenerate as "Only in"; the output files themselves should match)
Changes: nothing in the repo.
///

EngAIn — Git: bring main up to a branch, then push
Working directory:

cd ~/Desktop/burdens_of_a_forgotten_past/EngAIn

git switch main
git merge --ff-only <branch-name>
git push
///
Effect: Moves main forward to the branch's commits. If the histories have
split, it stops with an error instead of creating a merge commit.
Changes: main only. git push publishes it to GitHub.

///
Addition: A way to test regeneration without modifying EngAIn
Claude added this command:

cd ~/Desktop/burdens_of_a_forgotten_past/EngAIn

PYTHONPATH=. python3 -m tier1.engainos.tools.run_chapter_extraction \
  --catalog-id "book_16_fragmented_beginning/086_sanctuary_to_storm.md" \
  --stageroom /tmp/stageroom_test
///

Instead of writing into the repository's Stageroom, the command directs the output to /tmp/stageroom_test.

That gives you a separate location to inspect experimental output before deciding whether it belongs in Git.
///

The comparison command:

diff -r \
  /tmp/stageroom_test/output/narrative_to_game/catalog \
  tier3/mettaext/stageroom/output/narrative_to_game/catalog
///

compares the temporary output against the repository's existing results. It will also report unrelated folders and expected receipt differences, so it isn't a clean pass/fail test by itself.
///

