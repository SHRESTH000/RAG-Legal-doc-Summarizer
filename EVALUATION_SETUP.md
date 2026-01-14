# BERTScore Evaluation Setup Guide

## Overview

This guide explains how to set up BERTScore evaluation to compare with the base paper's score of 0.89.

## Installation

### Required Packages

```bash
pip install bert-score
pip install rouge-score  # Optional: for ROUGE metrics
```

### BERTScore Model

BERTScore will automatically download the model on first use:
- Recommended: `microsoft/deberta-xlarge-mnli` (default)
- Alternative: `roberta-large`

## Step-by-Step Evaluation

### Step 1: Generate Summaries

First, generate summaries for your test cases:

```python
from rag.integrated_rag_with_summarization import IntegratedRAGWithSummarization

system = IntegratedRAGWithSummarization(
    summarizer_model_type="openai",
    summarizer_model_name="gpt-4"
)

# Process test cases
summaries = {}
for test_case in test_cases:
    result = system.process(test_case['query'], generate_summary=True)
    summaries[test_case['case_number']] = result['summary']
```

### Step 2: Create Reference Summaries

You need reference (ground truth) summaries for evaluation. Options:

**Option A: Manual Annotation**
- Have legal experts create reference summaries
- Ensure quality and accuracy

**Option B: Use Existing Summaries**
- If judgments have existing summaries, use those
- Verify they're of good quality

**Option C: Use Base Paper's Dataset**
- If available, use the same test set as base paper
- Ensures fair comparison

**Format**: Create `evaluation/reference_summaries.json`:
```json
{
    "case_number_1": "Reference summary text...",
    "case_number_2": "Reference summary text...",
    ...
}
```

### Step 3: Run Evaluation

```bash
export OPENAI_API_KEY="your-key"  # If using OpenAI
python scripts/evaluate_summarization.py
```

## Evaluation Metrics

### BERTScore

BERTScore measures semantic similarity using contextual embeddings:
- **Precision**: How much generated text matches reference
- **Recall**: How much reference content is covered
- **F1**: Harmonic mean of precision and recall

**Base Paper**: BERTScore F1 = **0.89**

### ROUGE (Optional)

Additional metrics:
- **ROUGE-1**: Unigram overlap
- **ROUGE-2**: Bigram overlap
- **ROUGE-L**: Longest common subsequence

## Comparing Results

The evaluation script automatically compares with baseline:

```
Comparison with Base Paper (BERTScore 0.89):
  Base Paper:  0.8900
  Our System:  0.XXXX
  Difference:  +X.XXXX (+X.XX%)
  Status:      BETTER / SIMILAR / WORSE
```

## Expected Outcomes

### If Our Score ≥ 0.89:
- ✅ **Better or equal to base paper**
- Our hybrid retrieval + enhanced KB provides better context
- Summarization quality matches/exceeds baseline

### If Our Score < 0.89:
- Analyze differences:
  - Is retrieval quality good?
  - Are summaries coherent?
  - Is context assembly working?
- Possible improvements:
  - Fine-tune LLM prompts
  - Adjust compression ratio
  - Improve retrieval quality

## Files Created

1. `evaluation/bertscore_evaluator.py` - BERTScore evaluation module
2. `scripts/evaluate_summarization.py` - Evaluation script
3. `evaluation/reference_summaries.json` - Reference summaries (create this)

## Tips for Good Evaluation

1. **Test Set Size**: At least 20-30 test cases for reliable results
2. **Reference Quality**: High-quality reference summaries are crucial
3. **Consistent Format**: Use same format for all summaries
4. **Multiple Runs**: Average results over multiple runs for stability

## Troubleshooting

### BERTScore Import Error
```bash
pip install bert-score
```

### Model Download Issues
BERTScore downloads models on first use. Ensure internet connection.

### Low Scores
- Check reference summary quality
- Verify generated summaries are coherent
- Review retrieval context quality
- Adjust compression ratio

## Next Steps After Evaluation

1. **If score ≥ 0.89**: ✅ Success! Document results
2. **If score < 0.89**: Analyze and improve:
   - Prompt engineering
   - Retrieval tuning
   - Context assembly
   - LLM model selection
