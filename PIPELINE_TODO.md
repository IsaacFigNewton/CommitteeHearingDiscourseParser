# Pipeline Refactoring: Move Mask Generation to ClassifierPipeline

## Overview
Move all mask generation logic from `Masker._apply_masking` to a new `_get_masks` method in `ClassifierPipeline`. This refactoring will:
- Centralize mask generation logic in the pipeline orchestrator
- Make `Masker` a simpler, more focused component that only applies masks
- Change the mask indexing scheme from sequential row indices to utterance UIDs

## Current Architecture

### Current Flow
1. **ClassifierPipeline.predict_hearing_sections()** (lines 236-253):
   - Calls `MaskedSoftmaxHelper.allowed_sections_for_hearing()` to generate class mask
   - Passes `class_mask` tuple `(allowed_sections, parse_successful)` via `set_params(masker__class_mask=...)`
   - `allowed_sections` is a list indexed by row position (0 to n-1)

2. **Masker._get_masked_probs()** (lines 114-138):
   - Receives class_mask tuple from set_params
   - Calls `_apply_masking(probs, allowed_sections)`
   - Returns masked probabilities and parse_successful flag

3. **Masker._apply_masking()** (lines 140-193):
   - Takes `probs` array (n_samples × n_classes) and `allowed_sections` list
   - Iterates over rows: `for row_idx, allowed in enumerate(allowed_sections)`
   - Masks probabilities by zeroing out disallowed classes
   - Renormalizes the remaining probabilities

### Problem with Current Approach
- Mask is indexed by **row position** (0, 1, 2, ...)
- This assumes the row order in the DataFrame matches the utterance order
- Fragile coupling between mask generation and data ordering

## Target Architecture

### New Flow
1. **ClassifierPipeline._get_masks()** (NEW METHOD):
   - Generate mask array of shape `(num_utterances_in_hearing, num_classes)`
   - Index rows by utterance UID, not sequential position
   - Return `np.ndarray` with dtype `bool` or `float`

2. **ClassifierPipeline.predict_hearing_sections()**:
   - Call `class_mask = self._get_masks(hearing, hearing_df, parse_trees)`
   - Pass mask via `self.model.set_params(masker__class_mask=class_mask)`
   - No longer pass allowed_sections tuple; pass raw ndarray

3. **Masker**:
   - Receive `class_mask: np.ndarray` of shape `(num_utterances, num_classes)`
   - Receive `uids: np.ndarray` via set_params to map rows to mask indices
   - Apply mask using UID-based indexing: `mask_row = class_mask[uid]`
   - Remove the `_apply_masking` logic that converts allowed_sections to masks

## Detailed Implementation Steps

### Step 1: Create `ClassifierPipeline._get_masks()`

**Location**: [ClassifierPipeline.py](src/ClassifierPipeline.py)

**Add new method after `_fill_missing()` (after line 156)**:

```python
def _get_masks(
    self,
    hearing: TaggedHearing,
    hearing_df: pd.DataFrame,
    parse_trees: Optional[List] = None,
) -> np.ndarray:
    """Generate class mask array for a hearing.

    Args:
        hearing: TaggedHearing object
        hearing_df: DataFrame with utterance features, must include 'uid' column
        parse_trees: Optional pre-generated parse trees

    Returns:
        np.ndarray of shape (num_utterances, num_classes) where:
        - Rows are indexed by utterance UID
        - Each row is a boolean or float mask for that utterance
        - mask[uid, class_idx] = 1.0 if class is allowed, 0.0 otherwise
    """
    # Get classifier classes
    classifier = self.model.named_steps['classifier']
    classes_ = classifier.classes_
    num_classes = len(classes_)

    # Extract metadata for masking
    speaker_positions = hearing_df['speaker.position.value'].values
    can_file_motions = hearing_df['can_file_motions'].values
    is_presenters = hearing_df['is_presenter'].values
    uids = hearing_df['uid'].values

    # Get allowed sections per utterance from MaskedSoftmaxHelper
    allowed_sections, parse_successful = MaskedSoftmaxHelper.allowed_sections_for_hearing(
        hearing=hearing,
        parser=self.parser,
        speaker_positions=speaker_positions,
        can_file_motions=can_file_motions,
        is_presenters=is_presenters,
        max_parses=self.max_parses,
        parse_trees=parse_trees,
    )

    # Find max UID to determine array size
    max_uid = max(uids) if len(uids) > 0 else 0
    num_utterances = max_uid + 1

    # Initialize mask array (indexed by UID)
    class_mask = np.ones((num_utterances, num_classes), dtype=np.float32)

    # Convert allowed_sections to mask array
    class_keys = [MaskedSoftmaxHelper._section_key(c) for c in classes_]

    for row_idx, (uid, allowed) in enumerate(zip(uids, allowed_sections)):
        allowed_keys = {
            MaskedSoftmaxHelper._section_key(s)
            for s in allowed
            if s is not None
        }

        # Empty/unknown mask means "do not constrain this utterance"
        if not allowed_keys:
            continue

        # Build boolean mask for this utterance
        keep = np.array([key in allowed_keys for key in class_keys], dtype=bool)

        # If grammar produced labels not in trained classes, don't constrain
        if not keep.any():
            continue

        # Set mask: 1.0 for allowed classes, 0.0 for disallowed
        class_mask[uid, :] = keep.astype(np.float32)

    return class_mask
```

**Notes**:
- This method consolidates mask generation logic currently in `Masker._apply_masking`
- Returns a mask array indexed by UID, not row position
- The mask shape is `(max_uid + 1, num_classes)` to support UID-based indexing
- Rows for UIDs not present in the hearing will remain all 1.0 (no constraint)

---

### Step 2: Update `ClassifierPipeline.predict_hearing_sections()`

**Location**: [ClassifierPipeline.py:190-259](src/ClassifierPipeline.py#L190-L259)

**Changes**:

1. **Remove lines 225-244** (parse tree generation and MaskedSoftmaxHelper call)
2. **Replace with**:

```python
# Generate parse trees for masking
parse_trees = []
if self.do_grammar_masking:
    try:
        parse_trees = list(
            self.parser.get_all_parses_as_nltk_trees(hearing, max_parses=self.max_parses)
            or []
        )
    except Exception:
        parse_trees = []

# Generate class mask array indexed by UID
class_mask = None
if self.do_grammar_masking:
    class_mask = self._get_masks(
        hearing=hearing,
        hearing_df=filled_df,
        parse_trees=parse_trees,
    )
```

3. **Update set_params call (lines 246-253)**:

```python
# Extract UIDs for UID-based mask indexing
uids = filled_df['uid'].values

# Set masking parameters on the masker stage
self.model.set_params(
    masker__classes_=classes_,
    masker__uids=uids,
)
if self.do_grammar_masking and class_mask is not None:
    self.model.set_params(
        masker__class_mask=class_mask,
    )
```

**Complete updated method**:

```python
def predict_hearing_sections(
    self,
    hearing: TaggedHearing,
    hearing_df: pd.DataFrame,
    smooth: bool = True,
) -> List[SectionEnum]:
    """Predict section labels for a single hearing.

    Args:
        hearing: Tagged hearing to predict sections for
        hearing_df: DataFrame with pre-extracted features for this hearing only,
                   sorted by uid. Should contain feature columns and metadata columns:
                   'speaker.position.value', 'can_file_motions', 'is_presenter', 'uid'.
        smooth: Whether to apply label smoothing

    Returns:
        List of predicted SectionEnum labels, one per utterance
    """
    if hearing_df.empty:
        raise ValueError(f'Empty hearing_df provided for hid={hearing.hid}, bid={hearing.bid}')
    filled_df = self._fill_missing(hearing_df)

    # Extract features for the pipeline
    X = filled_df[self.feature_cols]

    # Get classifier classes and set them on the masker
    classifier = self.model.named_steps['classifier']
    classes_ = classifier.classes_

    # Generate parse trees for masking
    parse_trees = []
    if self.do_grammar_masking:
        try:
            parse_trees = list(
                self.parser.get_all_parses_as_nltk_trees(hearing, max_parses=self.max_parses)
                or []
            )
        except Exception:
            parse_trees = []

    # Generate class mask array indexed by UID
    class_mask = None
    if self.do_grammar_masking:
        class_mask = self._get_masks(
            hearing=hearing,
            hearing_df=filled_df,
            parse_trees=parse_trees,
        )

    # Extract UIDs for UID-based mask indexing
    uids = filled_df['uid'].values

    # Set masking parameters on the masker stage
    self.model.set_params(
        masker__classes_=classes_,
        masker__uids=uids,
    )
    if self.do_grammar_masking and class_mask is not None:
        self.model.set_params(
            masker__class_mask=class_mask,
        )

    # Predict using the full pipeline (features -> classifier -> masker)
    labels, parse_success = self.model.predict(X)
    labels = list(labels)

    return self.smooth_label_list(labels) if smooth else labels
```

---

### Step 3: Simplify `Masker` to Apply Pre-Generated Masks

**Location**: [Masker.py](src/classifier/Masker.py)

**Changes**:

1. **Update `__init__` parameters (lines 46-69)**:

```python
def __init__(
    self,
    classes_: Optional[np.ndarray] = None,
    uids: Optional[np.ndarray] = None,
    class_mask: Optional[np.ndarray] = None,
) -> None:
    """Initialize the masker.

    Args:
        classes_: Array of class labels (set automatically by pipeline)
        uids: Array of utterance IDs for each row in prediction batch
        class_mask: Pre-generated mask array of shape (num_utterances, num_classes)
                   indexed by UID. mask[uid, class_idx] indicates if class is allowed.
    """
    self.classes_ = classes_
    self.uids = uids
    self.class_mask = class_mask
```

2. **Update `_get_masked_probs()` (lines 114-138)**:

Replace entire method:

```python
def _get_masked_probs(self, X: np.ndarray) -> Tuple[np.ndarray, bool]:
    """Apply masking to probability matrix.

    Args:
        X: Probability matrix of shape (n_samples, n_classes)

    Returns:
        Tuple of (masked_probs, parse_success) where:
        - masked_probs: Masked and renormalized probability matrix
        - parse_success: Always False (parse success tracked in pipeline)
    """
    # X is expected to be probability matrix from classifier
    probs = X

    # If no masking context, return unmasked probabilities
    if self.class_mask is None or self.uids is None:
        return probs, False

    # Apply UID-indexed masking
    masked_probs = self._apply_uid_indexed_masking(probs)
    return masked_probs, False
```

3. **Replace `_apply_masking()` with `_apply_uid_indexed_masking()` (lines 140-193)**:

```python
def _apply_uid_indexed_masking(self, probs: np.ndarray) -> np.ndarray:
    """Apply UID-indexed masking to probabilities.

    Args:
        probs: Probability matrix of shape (n_samples, n_classes)

    Returns:
        Masked and renormalized probability matrix
    """
    if self.class_mask is None or self.uids is None:
        return probs

    if len(self.uids) != probs.shape[0]:
        raise ValueError(
            f"uids length ({len(self.uids)}) must match "
            f"number of rows in probs ({probs.shape[0]})."
        )

    masked = probs.copy()

    for row_idx, uid in enumerate(self.uids):
        # Validate UID is in bounds
        if uid < 0 or uid >= self.class_mask.shape[0]:
            # UID out of bounds - don't constrain this row
            continue

        # Get mask for this utterance
        mask = self.class_mask[uid, :]

        # If all zeros, don't constrain (edge case)
        if mask.sum() == 0:
            continue

        # Apply mask
        masked[row_idx, :] *= mask

        # Renormalize
        denom = masked[row_idx].sum()
        if denom > 0:
            masked[row_idx] /= denom
        else:
            # Degenerate case: uniform over allowed classes
            keep = mask > 0
            if keep.any():
                masked[row_idx, keep] = 1.0 / keep.sum()

    return masked
```

4. **Remove or deprecate the old `_apply_masking` method entirely**

---

### Step 4: Update Imports

**Location**: [Masker.py:1-10](src/classifier/Masker.py#L1-L10)

**Remove**:
```python
from src.dataclasses.Hearing import TaggedHearing
from src.grammar.Parser import Parser
from src.classifier.MaskedSoftmaxHelper import MaskedSoftmaxHelper
```

These are no longer needed in `Masker` since mask generation moved to `ClassifierPipeline`.

---

### Step 5: Testing Strategy

**Create test file**: `tests/test_uid_indexed_masking.py`

```python
import numpy as np
import pandas as pd
from src.ClassifierPipeline import ClassifierPipeline
from src.classifier.Masker import Masker

def test_get_masks_shape():
    """Test that _get_masks returns correct shape indexed by UID"""
    # Setup: create a hearing with UIDs [0, 2, 5]
    # Expected: mask shape is (6, num_classes) to accommodate max UID of 5
    pass

def test_get_masks_uid_indexing():
    """Test that mask rows correspond to utterance UIDs, not positions"""
    # Setup: hearing with UIDs [0, 5, 10]
    # Verify: mask[0], mask[5], mask[10] have constraints
    # Verify: mask[1], mask[2], etc. are all-ones (unconstrained)
    pass

def test_masker_applies_uid_indexed_mask():
    """Test that Masker correctly applies UID-indexed masks"""
    # Setup: probs array with 3 rows
    # UIDs: [0, 5, 10]
    # mask[0] = [1, 0, 1, 0]
    # mask[5] = [0, 1, 0, 1]
    # mask[10] = [1, 1, 0, 0]
    # Verify: row 0 uses mask[0], row 1 uses mask[5], row 2 uses mask[10]
    pass

def test_uid_out_of_bounds():
    """Test that out-of-bounds UIDs don't crash, just skip masking"""
    # Setup: mask with shape (5, 4), UIDs [0, 100]
    # Verify: row 0 gets masked, row 1 (UID 100) stays unmasked
    pass

def test_backward_compatibility():
    """Test that refactored code produces same results as original"""
    # Load a real hearing from test data
    # Run old and new pipelines
    # Compare predictions
    pass
```

**Run tests**:
```bash
pytest tests/test_uid_indexed_masking.py -v
```

---

### Step 6: Integration Testing

**Test with real hearings**:

1. **Notebook**: `notebooks/test_refactored_pipeline.ipynb`

```python
# Load a trained model
pipeline = ClassifierPipeline.load('models/my_model.pkl')

# Load test hearings
hearings = load_test_hearings()

# Compare old vs new predictions
for hearing in hearings:
    hearing_df = pipeline._build_utterances_dataframe([hearing])

    # New approach
    predictions_new = pipeline.predict_hearing_sections(hearing, hearing_df)

    # Verify no crashes, reasonable outputs
    assert len(predictions_new) == len(hearing.utterances)
    print(f"Hearing {hearing.hid}: {len(predictions_new)} predictions")
```

2. **Check for regressions**:
   - Run evaluation on held-out test set
   - Compare metrics (accuracy, F1) before and after refactoring
   - Expect identical or near-identical results

---

## Benefits of This Refactoring

### 1. **Clearer Separation of Concerns**
   - `ClassifierPipeline`: Orchestrates masking logic, owns hearing/parser context
   - `Masker`: Pure transformation component, applies pre-generated masks
   - `MaskedSoftmaxHelper`: Pure utility functions, no state

### 2. **More Robust Indexing**
   - Mask indexed by UID, not row position
   - Resilient to DataFrame reordering or filtering
   - Explicit about which utterance gets which mask

### 3. **Easier to Test**
   - `_get_masks()` can be tested independently with mock hearings
   - `Masker` logic is simpler: just array indexing and masking
   - No need to mock complex hearing/parser objects in Masker tests

### 4. **Better Extensibility**
   - Easy to add alternative mask generation strategies
   - Can swap out MaskedSoftmaxHelper for different approaches
   - Masker becomes a generic "apply mask array" component

### 5. **Reduced Coupling**
   - Masker no longer imports Hearing, Parser, MaskedSoftmaxHelper
   - Easier to use Masker in other contexts (e.g., non-hearing classifiers)

---

## Migration Checklist

- [ ] Implement `ClassifierPipeline._get_masks()`
- [ ] Update `ClassifierPipeline.predict_hearing_sections()` to call `_get_masks()`
- [ ] Update `ClassifierPipeline.predict_hearing_sections()` to pass `uids` via set_params
- [ ] Update `Masker.__init__()` to accept `uids` and `class_mask` ndarray
- [ ] Replace `Masker._apply_masking()` with `Masker._apply_uid_indexed_masking()`
- [ ] Update `Masker._get_masked_probs()` to use new masking method
- [ ] Remove unused imports from Masker (Hearing, Parser, MaskedSoftmaxHelper)
- [ ] Write unit tests for `_get_masks()` UID indexing
- [ ] Write unit tests for `Masker._apply_uid_indexed_masking()`
- [ ] Run integration tests on real hearings
- [ ] Compare predictions before/after refactoring
- [ ] Update documentation and docstrings
- [ ] Create PR and review changes

---

## Potential Gotchas

### 1. **UID Gaps**
   - If hearing has UIDs [0, 5, 100], mask array will be shape `(101, num_classes)`
   - Sparse UID space ’ large mask arrays
   - **Mitigation**: Document this behavior, consider UID remapping if memory is an issue

### 2. **UID Indexing Assumptions**
   - Code assumes UIDs are non-negative integers
   - **Mitigation**: Add validation in `_get_masks()` and `Masker`

### 3. **Parse Success Flag**
   - Currently `parse_successful` is part of the class_mask tuple
   - After refactoring, this information is lost in the ndarray
   - **Mitigation**: Return parse_success separately or embed it as a pipeline attribute

### 4. **Backward Compatibility**
   - Old pickled models expect the old Masker interface
   - **Mitigation**: Version the pipeline, add migration script or deprecation warning

---

## Timeline Estimate

- **Step 1-2** (ClassifierPipeline changes): 2-3 hours
- **Step 3** (Masker refactoring): 2 hours
- **Step 4** (Import cleanup): 15 minutes
- **Step 5** (Unit tests): 2-3 hours
- **Step 6** (Integration tests): 1-2 hours
- **Code review and iteration**: 1-2 hours

**Total**: ~10-13 hours

---

## Open Questions

1. **Should we remap UIDs to dense indices [0, 1, 2, ...] to save memory?**
   - Pro: Smaller mask arrays
   - Con: Need to maintain UID ’ index mapping

2. **Should we return parse_success from _get_masks()?**
   - Current: Embedded in tuple with allowed_sections
   - After: Lost in ndarray conversion
   - Option: Return `(class_mask, parse_success)` tuple from `_get_masks()`

3. **How to handle missing UIDs in hearing_df?**
   - Current: Assumes hearing_df has all utterances
   - Refactored: Could support partial predictions
   - Need validation or explicit error

4. **Should Masker validate UID bounds?**
   - Current plan: Skip out-of-bounds UIDs silently
   - Alternative: Raise error on invalid UIDs
   - Depends on desired robustness vs fail-fast philosophy
