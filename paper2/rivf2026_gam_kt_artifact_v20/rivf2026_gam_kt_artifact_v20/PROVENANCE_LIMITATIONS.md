# Provenance limitations for the v18 metadata layer

This metadata layer was produced without rerunning either the simulator or the
Junyi confirmation experiment. It does not retune a model, reopen a test set,
change a graph, or alter any frozen numerical result.

## Evidence levels

The added records distinguish three levels of evidence.

1. **Recomputable from released bytes.** Examples include SHA-256 values,
   simulator input row counts, candidate-table values, and exact equality of the
   released GAM-KT and gate-selected-null per-user metric rows.
2. **Historical execution evidence.** The executed Junyi notebook, its outputs,
   its hard assertions, and the frozen manifest consistently report zero overlap
   and the 979-to-976 edge cycle removal. These facts were recorded by the
   historical run but cannot be reconstructed independently from the smaller
   released artifact.
3. **Not recoverable.** The exact gate-lock instant, exact historical dependency
   versions, raw Junyi input hashes, old and confirmation-development membership
   fingerprints, and identities of the three removed edges were not frozen in
   the released v18 inputs. The certificates mark these fields as unavailable
   rather than inventing values.

## Junyi privacy and data boundary

No raw learner identifier or raw Junyi interaction log was added. The split
certificate contains only aggregate counts and a SHA-256 fingerprint computed
from the already salted confirmation-test identifiers. Because equivalent
fingerprints for the earlier train/development/test sets and confirmation
development were not released, that fingerprint cannot independently prove the
historical zero-overlap assertion.

The raw Junyi exercise table is also absent. Consequently,
`certificates/graph_cycle_removal.json` can cross-check the method and reported
counts but cannot name or hash the removed edges or rebuild the corrected graph.

The recovered executed Junyi notebook preserves the historical run settings
`ACCEPT_JUNYI_NONCOMMERCIAL_TERMS=True` and `AUTO_DOWNLOAD=True`. Its included
builder instead defaults both values to `False`. Consequently, any statement
that the *executed notebook file itself* retains the safe default is inaccurate;
the safe default belongs to the builder. This bounded metadata pass does not
modify either source. A later packaging pass should prevent a reviewer from
inadvertently reusing the historical opt-in state and must never accept dataset
terms on the reviewer's behalf.

## Identity-check boundary

The gate-selected Junyi configuration is algebraically all-pathways-off:
signal weight is zero and graph-dependent adaptation is disabled. Released
per-user metrics are exactly identical for all 1,000 users, including identical
missingness for the 32 users without a defined AUC.

The v13 build audited the recovered frozen event-level prediction table before
packaging. `certificates/junyi_identity.json` records its compressed-file hash,
matching canonical event digests, zero full-row mismatches, and a maximum
absolute prediction difference of zero across 127,923 paired events. The table
itself is not redistributed, so reviewers cannot independently rerun this
event-level comparison from artifact v20 alone. The result remains an
implementation-identity check after null selection, not evidence that a nonzero
graph effect is zero and not a general equivalence claim.

## Gate chronology boundary

The recovered notebook metadata shows the development-selection cell executed
successfully before the confirmation-test cell. It does not provide an external
preregistration or a separate immutable timestamp for the in-cell lock
assignment. The most precise defensible status is therefore:
`exact_lock_time_status = not independently recoverable`.

## Environment boundary

The dependency names in `requirements.txt` are unpinned. The Junyi notebook
reports a Colab execution and the manifest reports CPU sequential updates, but
the exact Colab image, Python version, and package versions were not captured.
The simulator manifest contains no historical runtime description.

`environment/verification_environment.json` records only the later local
environment used to inspect frozen bytes and execute the standard-library claim
verifier. It must not be cited as the original experimental environment.

## Checksum coverage

The completed v18 package enrolls its paper, configs, certificates, environment
record, claim maps, source snapshots, and frozen outputs in `SHA256SUMS.txt`.
The checksum list authenticates the distributed state; it cannot retroactively
establish an unavailable historical Git commit or preregistration timestamp.


