# Analysis: Where We Might Be Wrong in Retrieval

## Overview

Our hybrid retrieval shows **similar performance** to BM25-only instead of improvement. Let's analyze potential issues:

---

## 🔍 Potential Issues Identified

### 1. **Score Normalization Problem** ⚠️ (Most Likely Issue)

**Code Location**: `retrieval/hybrid_retriever.py` lines 318-334

**Issue**:
```python
def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
    min_score = min(scores.values())
    max_score = max(scores.values())
    normalized[chunk_id] = (score - min_score) / (max_score - min_score)
```

**Problems**:
- **Min-Max normalization** assumes equal importance of all scores
- BM25 scores can have very different distributions than vector scores
- If BM25 has one high score and many zeros, normalization amplifies that one score
- Vector scores (0-1) get normalized to 0-1 again, which doesn't help

**Impact**: High - This could make one method dominate the other unfairly

**Example Problem**:
- BM25: scores = [0.1, 0.15, 20.5, 0.2] → normalized = [0.0, 0.0, 1.0, 0.0]
- Vector: scores = [0.7, 0.75, 0.8, 0.72] → normalized = [0.0, 0.5, 1.0, 0.2]
- Result: BM25's one high score dominates, vector scores compressed

---

### 2. **Score Combination Method** ⚠️

**Code Location**: `retrieval/hybrid_retriever.py` lines 307-308

**Issue**:
```python
combined_score = (self.bm25_weight * bm25_score + 
                  self.vector_weight * vector_score)
```

**Problems**:
- **Simple weighted average** assumes scores are comparable after normalization
- Doesn't account for different score distributions
- No reciprocal rank fusion (RRF) - industry standard for hybrid retrieval
- Fixed weights (0.4 BM25, 0.6 Vector) - might not be optimal

**Impact**: Medium-High - RRF is proven better than weighted average

**Better Approach**: Use Reciprocal Rank Fusion (RRF)
```python
# RRF formula:
# score = sum(1 / (rank + k)) for each retriever
# Then combine ranks, not normalized scores
```

---

### 3. **Vector Similarity Threshold Too High** ⚠️

**Code Location**: `retrieval/hybrid_retriever.py` line 257

**Issue**:
```python
similarity_threshold: float = 0.7
```

**Problems**:
- Threshold of 0.7 is **very high** for semantic similarity
- Filters out many potentially relevant chunks
- Vector search might return fewer results than BM25
- Creates imbalance in the hybrid combination

**Impact**: Medium - Reduces vector search contribution

**Better Value**: 0.5-0.6 (more permissive)

---

### 4. **BM25 Scores Can Be Zero or Negative**

**Code Location**: `retrieval/hybrid_retriever.py` line 79

**Issue**:
```python
if scores[idx] > 0:  # Only return documents with positive scores
```

**Problems**:
- BM25 can return scores of 0 for documents with no matching terms
- Normalization of scores that include zeros can be problematic
- Some documents might have zero BM25 score but good vector score

**Impact**: Low-Medium - Might filter out some valid results

---

### 5. **No Reciprocal Rank Fusion (RRF)** ⚠️ (Industry Standard Missing)

**Issue**: We're using weighted score combination instead of RRF

**Problems**:
- RRF is the **industry standard** for hybrid retrieval
- Works better when score distributions differ
- More robust to normalization issues
- Used by Elasticsearch, Pinecone, etc.

**Impact**: High - This is a significant architectural choice

**RRF Formula**:
```
Final Score = Σ (1 / (rank_i + k))
where:
- rank_i is the rank in retriever i
- k is a constant (typically 60)
- Sum over all retrievers
```

**Why RRF is Better**:
- Combines ranks, not scores (more robust)
- Doesn't require normalization
- Proven to work well in practice
- Handles different score scales naturally

---

### 6. **Fixed Weights (0.4 BM25, 0.6 Vector)**

**Issue**: Weights are hardcoded, not tuned

**Problems**:
- No tuning/optimization done
- Legal domain might need different weights
- Some queries favor keyword (higher BM25 weight)
- Some queries favor semantic (higher vector weight)
- Should be query-dependent or tuned

**Impact**: Medium - Suboptimal weights could reduce performance

---

### 7. **Limited Top-K Expansion**

**Code Location**: `retrieval/hybrid_retriever.py` lines 287, 291

**Issue**:
```python
bm25_scores = self.bm25_retriever.retrieve(query, top_k * 2)
vector_scores = self.vector_retriever.retrieve(query, top_k * 2, judgment_id)
```

**Problems**:
- Only retrieving `top_k * 2` from each retriever
- If BM25 and Vector have very different top results, we might miss good combinations
- Should retrieve more candidates (e.g., top_k * 5) for better fusion

**Impact**: Low-Medium - Might miss some good results

---

### 8. **Embedding Model Might Not Be Optimal**

**Issue**: Using `sentence-transformers/all-MiniLM-L6-v2`

**Problems**:
- General-purpose model, not legal-domain specific
- Smaller model (384 dimensions)
- Might not capture legal semantic relationships well
- Base paper might use a better/larger model

**Impact**: Medium - Could affect vector search quality

**Better Options**:
- Legal-domain fine-tuned models
- Larger models (768+ dimensions)
- Domain-specific sentence transformers

---

### 9. **Evaluation Methodology Issues**

**From EVALUATION_RESULTS_SUMMARY.md**:

**Potential Issues**:
1. **Relevance threshold too low** (0.3) - marks too many chunks as relevant
2. **Large corpus** - 50,000 chunks means very low recall naturally
3. **Query characteristics** - many queries have exact keyword matches (favor BM25)
4. **Automated annotation** - might not capture semantic relevance well

**Impact**: High - This affects whether we can see improvements

---

## 🎯 Most Likely Root Causes

### Primary Issues (High Impact):

1. **❌ No RRF (Reciprocal Rank Fusion)**
   - Using weighted average instead of industry standard
   - **Fix**: Implement RRF for score combination

2. **❌ Score Normalization Problems**
   - Min-max normalization doesn't work well for different score distributions
   - **Fix**: Use RRF (which doesn't need normalization) or better normalization

3. **❌ Evaluation Methodology**
   - Relevance threshold, corpus size, query characteristics
   - **Fix**: Refine evaluation setup

### Secondary Issues (Medium Impact):

4. **Vector similarity threshold too high** (0.7)
5. **Fixed weights not tuned** (0.4/0.6)
6. **General-purpose embedding model**

---

## ✅ What We Should Fix First

### Priority 1: Implement RRF (Reciprocal Rank Fusion)

**Why**: 
- Industry standard for hybrid retrieval
- More robust to score distribution differences
- Proven to work better than weighted average

**How**:
```python
def combine_with_rrf(self, bm25_results, vector_results, k=60):
    # Get ranks from each retriever
    bm25_ranks = {chunk_id: rank+1 for rank, (chunk_id, _) in enumerate(bm25_results)}
    vector_ranks = {chunk_id: rank+1 for rank, (chunk_id, _) in enumerate(vector_results)}
    
    # Combine ranks using RRF
    combined_scores = {}
    all_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())
    
    for chunk_id in all_ids:
        score = 0.0
        if chunk_id in bm25_ranks:
            score += 1.0 / (bm25_ranks[chunk_id] + k)
        if chunk_id in vector_ranks:
            score += 1.0 / (vector_ranks[chunk_id] + k)
        combined_scores[chunk_id] = score
    
    return sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
```

### Priority 2: Lower Vector Similarity Threshold

Change from 0.7 to 0.5-0.6 to get more vector results.

### Priority 3: Improve Evaluation Setup

- Increase relevance threshold to 0.5-0.6
- Test on queries that favor semantic matching
- Manual spot-checks for validation

---

## 📊 Expected Impact of Fixes

### If We Fix RRF:
- **Expected**: +2-5% improvement in Precision@K
- **Reason**: More robust combination method

### If We Fix Evaluation:
- **Expected**: Better visibility of improvements
- **Reason**: More appropriate test setup

### Combined Fixes:
- **Expected**: 3-7% improvement over BM25-only
- **Reason**: Better retrieval method + better evaluation

---

## 🔬 How to Test Fixes

1. **Implement RRF**
2. **Re-run evaluation** with same queries
3. **Compare**: BM25-only vs Hybrid (with RRF)
4. **Expected**: Hybrid should show improvement on semantic queries

---

## Conclusion

**Main Issues**:
1. ❌ Using weighted average instead of RRF
2. ❌ Score normalization problems
3. ❌ Evaluation methodology limitations
4. ⚠️ Vector threshold too high
5. ⚠️ Fixed weights not optimal

**Primary Fix**: **Implement RRF** - this is the biggest architectural issue.

**Secondary Fixes**: Lower threshold, tune weights, improve evaluation.

**Expected Result**: After fixes, hybrid should show **measurable improvement** over BM25-only, especially on semantic queries.
