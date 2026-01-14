"""
BERTScore Evaluation Module
Compare generated summaries with reference summaries
Following base paper's evaluation methodology
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

logger = logging.getLogger(__name__)


class BERTScoreEvaluator:
    """
    BERTScore evaluator for legal text summarization
    Evaluates precision, recall, and F1 using contextual embeddings
    """
    
    def __init__(self, model_type: str = "microsoft/deberta-xlarge-mnli"):
        """
        Initialize BERTScore evaluator
        
        Args:
            model_type: BERTScore model (deberta-xlarge-mnli is recommended)
        """
        self.model_type = model_type
        self.bertscorer = None
        self._initialize()
    
    def _initialize(self):
        """Initialize BERTScore scorer"""
        try:
            from bert_score import score
            self.score_func = score
            logger.info(f"BERTScore initialized with model: {self.model_type}")
        except ImportError:
            logger.warning("bert-score not installed. Install with: pip install bert-score")
            self.score_func = None
    
    def evaluate(self,
                 generated_summaries: List[str],
                 reference_summaries: List[str],
                 lang: str = "en",
                 verbose: bool = False) -> Dict:
        """
        Evaluate generated summaries against references
        
        Args:
            generated_summaries: List of generated summary texts
            reference_summaries: List of reference summary texts
            lang: Language code (default: "en")
            verbose: Whether to show progress
            
        Returns:
            Dict with P, R, F1 scores and details
        """
        if not self.score_func:
            raise ValueError("BERTScore not available. Install with: pip install bert-score")
        
        if len(generated_summaries) != len(reference_summaries):
            raise ValueError("Generated and reference summaries must have same length")
        
        logger.info(f"Evaluating {len(generated_summaries)} summaries...")
        
        # Calculate BERTScore
        P, R, F1 = self.score_func(
            generated_summaries,
            reference_summaries,
            lang=lang,
            verbose=verbose,
            model_type=self.model_type
        )
        
        # Convert to Python lists/values
        precision_scores = [float(p) for p in P]
        recall_scores = [float(r) for r in R]
        f1_scores = [float(f) for f in F1]
        
        # Calculate averages
        avg_precision = sum(precision_scores) / len(precision_scores)
        avg_recall = sum(recall_scores) / len(recall_scores)
        avg_f1 = sum(f1_scores) / len(f1_scores)
        
        return {
            'precision': precision_scores,
            'recall': recall_scores,
            'f1': f1_scores,
            'avg_precision': avg_precision,
            'avg_recall': avg_recall,
            'avg_f1': avg_f1,
            'num_samples': len(generated_summaries)
        }
    
    def evaluate_single(self,
                       generated: str,
                       reference: str,
                       lang: str = "en") -> Dict:
        """Evaluate a single summary pair"""
        return self.evaluate([generated], [reference], lang=lang)


def compare_with_baseline(our_scores: Dict,
                         baseline_score: float = 0.89,
                         metric: str = 'f1') -> Dict:
    """
    Compare our scores with base paper baseline
    
    Args:
        our_scores: Our evaluation results
        baseline_score: Base paper's BERTScore (0.89)
        metric: Which metric to compare ('precision', 'recall', or 'f1')
        
    Returns:
        Comparison results
    """
    our_avg = our_scores[f'avg_{metric}']
    
    difference = our_avg - baseline_score
    percent_diff = (difference / baseline_score * 100) if baseline_score > 0 else 0
    
    is_better = our_avg > baseline_score
    is_similar = abs(difference) < 0.01  # Within 0.01 difference
    
    return {
        'baseline_score': baseline_score,
        'our_score': our_avg,
        'difference': difference,
        'percent_difference': percent_diff,
        'is_better': is_better,
        'is_similar': is_similar,
        'comparison': 'better' if is_better else ('similar' if is_similar else 'worse')
    }


class ROUGEEvaluator:
    """ROUGE evaluator (alternative metric)"""
    
    def __init__(self):
        self.rouge = None
        self._initialize()
    
    def _initialize(self):
        """Initialize ROUGE scorer"""
        try:
            from rouge_score import rouge_scorer
            self.rouge = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)
            logger.info("ROUGE scorer initialized")
        except ImportError:
            logger.warning("rouge-score not installed. Install with: pip install rouge-score")
    
    def evaluate(self,
                 generated_summaries: List[str],
                 reference_summaries: List[str]) -> Dict:
        """
        Evaluate using ROUGE metrics
        
        Args:
            generated_summaries: List of generated summaries
            reference_summaries: List of reference summaries
            
        Returns:
            Dict with ROUGE-1, ROUGE-2, ROUGE-L scores
        """
        if not self.rouge:
            raise ValueError("ROUGE not available. Install with: pip install rouge-score")
        
        rouge1_scores = []
        rouge2_scores = []
        rougeL_scores = []
        
        for gen, ref in zip(generated_summaries, reference_summaries):
            scores = self.rouge.score(ref, gen)
            rouge1_scores.append(scores['rouge1'].fmeasure)
            rouge2_scores.append(scores['rouge2'].fmeasure)
            rougeL_scores.append(scores['rougeL'].fmeasure)
        
        return {
            'rouge1': {
                'scores': rouge1_scores,
                'avg': sum(rouge1_scores) / len(rouge1_scores)
            },
            'rouge2': {
                'scores': rouge2_scores,
                'avg': sum(rouge2_scores) / len(rouge2_scores)
            },
            'rougeL': {
                'scores': rougeL_scores,
                'avg': sum(rougeL_scores) / len(rougeL_scores)
            }
        }


def create_evaluator(metric: str = "bertscore") -> BERTScoreEvaluator:
    """Factory function to create evaluator"""
    if metric.lower() == "bertscore":
        return BERTScoreEvaluator()
    else:
        raise ValueError(f"Unknown metric: {metric}")
