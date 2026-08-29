# Pipeline Refactoring: Sequence-Based Prediction

## Overview
Refactor the classifier pipeline to process utterances as sequences grouped by hearing, rather than as individual instances. This will enable the classifier to maintain temporal context within hearings while still leveraging the CYK parser's grammar constraints.

---

## Phase 1: Update `evaluate_model.ipynb` Data Preparation

### 1.1 Group and Sort Test Data by Hearing
**File:** [evaluate_model.ipynb](evaluate_model.ipynb)
**Location:** After cell creating `test_df` (around cell 18)

- [ ] Create a function to group utterances by `hearing_group` (bid + hid)
- [ ] For each hearing group:
  - [ ] Sort utterances by `uid` in ascending order
  - [ ] Extract feature matrix `X` of shape `(num_features, hearing_len)`
  - [ ] Store as a list of 2D arrays (one per hearing)
- [ ] Verify that `hearing_len` varies across hearings
- [ ] Store corresponding `y` labels grouped by hearing for later evaluation

**Implementation Details:**
```python
# Group test data by hearing
test_hearings_grouped = {}
for hearing_id in test_df['hearing_group'].unique():
    hearing_data = test_df[test_df['hearing_group'] == hearing_id].sort_values('uid')
    test_hearings_grouped[hearing_id] = {
        'X': hearing_data[feature_cols],
        'y': hearing_data['section'],
        'hearing_len': len(hearing_data)
    }
```

### 1.2 Prepare Training Data Similarly
**File:** [evaluate_model.ipynb](evaluate_model.ipynb)
**Location:** Training section (around cell 22)

- [ ] Group training data by `hearing_group`
- [ ] Sort each group by `uid`
- [ ] Maintain the grouped structure for potential future sequence-aware training
- [ ] Note: Initial implementation may still use flattened training data for compatibility

---

## Phase 2: Update `ClassifierPipeline` Interface

### 2.1 Modify `predict_hearing_sections()` Input Signature
**File:** [src/ClassifierPipeline.py](src/ClassifierPipeline.py)
**Location:** Lines 185-235

- [ ] Update method signature to accept utterance matrix instead of requiring `utterances_df`
- [ ] New signature should accept:
  - `hearing_df: pd.DataFrame` of shape `(num_features, hearing_len)`
  - `smooth: bool = True` (existing)
- [ ] Remove dependency on `hearing` and `utterances_df` parameters
- [ ] Ensure backward compatibility or create new method name (e.g., `predict_hearing_sequence()`)

**Implementation Notes:**
- Shape conventions: `(num_features, hearing_len)` matches sklearn convention where samples are along axis 0
- May need transpose operations depending on internal pipeline expectations
- Consider renaming to clarify the matrix input: `predict_hearing_sections_from_matrix()`

### 2.2 Update Feature Extraction Logic
**File:** [src/ClassifierPipeline.py](src/ClassifierPipeline.py)
**Location:** Lines 209-213 (inside `predict_hearing_sections()`)

- [ ] Remove `utterances_df` filtering logic
- [ ] Accept pre-extracted features `X_hearing` directly
- [ ] Remove or make optional the `_fill_missing()` call (assume caller handles this)
- [ ] Validate input shapes:
  - [ ] Check that `X_hearing.shape[0]` matches expected number of features
  - [ ] Check that metadata arrays match `X_hearing.shape[1]` (hearing_len)

### 2.3 Update Internal Pipeline Predict Call
**File:** [src/ClassifierPipeline.py](src/ClassifierPipeline.py)
**Location:** Lines 230-234

- [ ] Ensure `self.model.predict(X)` receives correctly shaped input
- [ ] Verify output shape is `(hearing_len,)` for labels
- [ ] Handle parse success flag correctly (currently concatenated to output)

---

## Phase 3: Update `MaskedClassifier` to Handle Sequences

### 3.1 Verify `predict_proba()` Compatibility
**File:** [src/classifier/MaskedClassifier.py](src/classifier/MaskedClassifier.py)
**Location:** Lines 124-155

- [ ] Confirm input shape handling: `X` of shape `(hearing_len, num_features_transformed)`
- [ ] Confirm output shape: `(probs, parse_flag)` where:
  - `probs` has shape `(hearing_len, num_classes)`
  - `parse_flag` is a scalar `bool`
- [ ] No changes needed if already correct


### 3.2 Modify `predict()` Method Output Shape
**File:** [src/classifier/MaskedClassifier.py](src/classifier/MaskedClassifier.py)
**Location:** Lines 107-122

**Current Behavior:**
- Returns concatenated array: `[labels (hearing_len,), parse_flags (hearing_len,)]`
- Shape: `(2 * hearing_len,)`

**Required Changes:**
- [ ] Change output format to return tuple: `(labels, parse_success_flag)`
- [ ] `labels` shape: `(hearing_len,)` - one label per utterance
- [ ] `parse_success_flag` shape: scalar `bool` - one flag per hearing
- [ ] Update `ClassifierPipeline.predict_hearing_sections()` to handle new return format

**Implementation:**
```python
def predict(self, X: Any) -> Tuple[np.ndarray, bool]:
    """Predict labels after applying grammar-constrained masking.

    Returns:
        Tuple of (labels, parse_success) where:
        - labels: np.ndarray of shape (n_utterances,)
        - parse_success: bool indicating if CYK parsing succeeded
    """
    probs, parse_successful = self.predict_proba(X)
    labels = self.classes_[np.argmax(probs, axis=1)]
    return labels, parse_successful
```

---

## Phase 4: Update Masking Logic for Sequences

### 4.1 Review `allowed_sections_for_hearing()` Interface
**File:** [src/classifier/MaskedSoftmaxHelper.py](src/classifier/MaskedSoftmaxHelper.py)
**Location:** Lines 27-86

**Current Behavior:**
- Returns `(masks, parse_successful)` where:
  - `masks`: `List[List[SectionEnum]]` of length `hearing_len`
  - `parse_successful`: `bool`

**Required Verification:**
- [ ] Confirm method already operates on full hearing sequence
- [ ] Verify `speaker_positions`, `can_file_motions`, `is_presenters` are sequences of length `hearing_len`
- [ ] No changes needed if interface already correct

### 4.2 Review `_apply_masking()` Method
**File:** [src/classifier/MaskedClassifier.py](src/classifier/MaskedClassifier.py)
**Location:** Lines 157-207

- [ ] Verify it handles `probs` matrix of shape `(hearing_len, num_classes)`
- [ ] Verify `allowed_sections` is a sequence of length `hearing_len`
- [ ] Confirm masking is applied row-by-row (per utterance)
- [ ] No changes needed if already correct

---

## Phase 5: Update Evaluation Harness in `evaluate_model.ipynb`

### 5.1 Modify Prediction Loop for Grouped Data
**File:** [evaluate_model.ipynb](evaluate_model.ipynb)
**Location:** Around cells 23-27 (evaluation section)

- [ ] Replace current per-utterance prediction with per-hearing prediction
- [ ] For each hearing in test set:
  ```python
  for hearing_id, data in test_hearings_grouped.items():
      # Get corresponding hearing object
      hearing = get_hearing_by_id(hearing_id)

      # Extract metadata for this hearing
      hearing_df = test_df[test_df['hearing_group'] == hearing_id].sort_values('uid')

      # Predict using new interface
      labels = parser_lr.predict_hearing_sections(
          hearing_df=hearing_df
          smooth=True
      )

      # Store predictions
      predictions[hearing_id] = labels
  ```

### 5.2 Re-concatenate Predictions for Evaluation
**File:** [evaluate_model.ipynb](evaluate_model.ipynb)
**Location:** Before classification_report calls (around cell 25-26)

- [ ] Flatten grouped predictions back into single array
- [ ] Ensure order matches `test_df` for correct alignment with `y_test`
- [ ] Implementation:
  ```python
  # Flatten predictions while preserving order
  pred_lr_flat = []
  pred_mlp_flat = []

  for hearing_id in test_df['hearing_group'].unique():
      pred_lr_flat.extend(predictions_lr[hearing_id])
      pred_mlp_flat.extend(predictions_mlp[hearing_id])

  pred_lr = np.array(pred_lr_flat)
  pred_mlp = np.array(pred_mlp_flat)
  ```

### 5.3 Verify Evaluation Metrics Still Work
**File:** [evaluate_model.ipynb](evaluate_model.ipynb)
**Location:** Cells 25-27

- [ ] Confirm `classification_report()` receives correct shapes
- [ ] Verify `y_test` and `pred_lr`/`pred_mlp` have same length and order
- [ ] Check confusion matrices render correctly
- [ ] Validate parse success rate calculation still works

---

## Phase 6: Update Smoothing Logic (Optional Enhancement)

### 6.1 Review Smoothing for Sequences
**File:** [src/ClassifierPipeline.py](src/ClassifierPipeline.py)
**Location:** Lines 168-183 (`smooth_label_list`)

**Current Implementation:**
- Fixes single outlier labels surrounded by identical labels
- Operates on flat list of labels

**Potential Enhancements:**
- [ ] Consider hearing boundaries when smoothing
- [ ] Don't smooth across hearing transitions (if processing multiple hearings in one batch)
- [ ] Current implementation should work fine for single-hearing sequences

---

## Phase 7: Testing and Validation

### 7.1 Unit Tests for Shape Handling
**File:** Create new test file `tests/test_pipeline_sequences.py`

- [ ] Test `ClassifierPipeline.predict_hearing_sections()` with various `hearing_len` values
- [ ] Test with minimum hearing length (e.g., 5 utterances)
- [ ] Test with maximum hearing length in dataset
- [ ] Test shape validation and error messages
- [ ] Test parse success flag propagation

### 7.2 Integration Tests
**File:** [evaluate_model.ipynb](evaluate_model.ipynb)

- [ ] Run full evaluation pipeline with both LR and MLP models
- [ ] Compare results with original implementation (should be similar or better)
- [ ] Verify parse success rates match expectations
- [ ] Check for any hearings that fail with new implementation

### 7.3 Edge Cases
- [ ] Test with single-utterance hearings
- [ ] Test with missing/None speaker metadata
- [ ] Test with hearings that have no valid parse
- [ ] Verify fallback masking works correctly

---

## Phase 8: Documentation and Cleanup

### 8.1 Update Docstrings
- [ ] Update `ClassifierPipeline.predict_hearing_sections()` docstring
- [ ] Update `MaskedClassifier.predict()` docstring
- [ ] Add examples showing new matrix-based input format

### 8.2 Update README or Usage Guide
- [ ] Document the sequence-based prediction workflow
- [ ] Provide example of grouping data by hearing
- [ ] Explain shape conventions and transformations

### 8.3 Remove or Deprecate Old Code
- [ ] If creating new method, mark old one as deprecated
- [ ] Or update all call sites to use new interface
- [ ] Remove unused `utterances_df` filtering logic

---

## Implementation Order Recommendation

1. **Start with Phase 2.1-2.2:** Update `ClassifierPipeline` to accept matrix input
2. **Then Phase 3.1:** Fix `MaskedClassifier.predict()` return format
3. **Then Phase 1:** Update notebook data preparation
4. **Then Phase 5:** Update evaluation loop and concatenation
5. **Finally Phases 7-8:** Test and document

---

## Key Design Decisions to Confirm

### Shape Convention Clarification
**Question:** Should utterances be along axis 0 or axis 1?

**Recommendation:**
- Use sklearn convention: **samples (utterances) along axis 0**
- Input to classifier: `(hearing_len, num_features)`
- Output from classifier: `(hearing_len,)` for labels
- Metadata arrays: `(hearing_len,)` for speaker info

**Rationale:**
- Matches sklearn's `predict()` expectations
- Feature transformers expect features as columns
- More intuitive for downstream evaluation

### Backward Compatibility
**Question:** Keep old interface or create new method?

**Options:**
1. Create `predict_hearing_sequence()` and keep old method
2. Update `predict_hearing_sections()` with optional parameters
3. Fully replace old implementation

**Recommendation:** Option 2
- Update existing method to accept either `utterances_df` OR matrix + metadata
- Check which parameters are provided and route accordingly
- Less code duplication, cleaner API

---

## Expected Benefits

1. **Performance:** Reduced overhead from DataFrame filtering
2. **Clarity:** Explicit sequence structure in data flow
3. **Flexibility:** Easier to batch multiple hearings in future
4. **Correctness:** Better alignment between data and parser expectations

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Shape mismatches breaking predictions | Add extensive shape validation with clear error messages |
| Parse success flag not propagating | Add integration test specifically for this |
| Evaluation metrics misaligned after refactor | Verify with known test case before/after |
| Performance regression | Benchmark key operations |

---

## Related Files

- [evaluate_model.ipynb](evaluate_model.ipynb) - Main evaluation script
- [src/ClassifierPipeline.py](src/ClassifierPipeline.py) - Pipeline orchestration
- [src/classifier/MaskedClassifier.py](src/classifier/MaskedClassifier.py) - Masked prediction logic
- [src/classifier/MaskedSoftmaxHelper.py](src/classifier/MaskedSoftmaxHelper.py) - Masking utilities
- [src/grammar/Parser.py](src/grammar/Parser.py) - CYK parser implementation
