"""
Comprehensive Evaluation with Statistical Significance Testing
Includes 40+ semantic queries, automated relevance annotation, and paired t-test
"""

import sys
from pathlib import Path
import os
import time
from typing import List, Dict, Tuple, Set
import json
import numpy as np
from scipy import stats

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from retrieval.hybrid_retriever import BM25Retriever, HybridRetriever
from database.connection import get_db_manager
from scripts.automated_relevance_annotation import (
    AutomatedRelevanceAnnotator,
    load_test_queries
)
import logging

logging.basicConfig(level=logging.WARNING)


class ComprehensiveEvaluator:
    """Comprehensive evaluation with statistical testing"""
    
    def __init__(self):
        self.db = get_db_manager()
        self.annotator = AutomatedRelevanceAnnotator()
        
        # Load corpus
        print("Loading corpus...")
        chunks = self.db.execute_query(
            "SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000"
        )
        
        if not chunks:
            raise ValueError("No chunks found in database")
        
        self.documents = [row['content'] for row in chunks]
        self.chunk_ids = [row['id'] for row in chunks]
        self.chunks_dict = {row['id']: {'id': row['id'], 'content': row['content']} 
                           for row in chunks}
        
        print(f"[OK] Loaded {len(self.documents):,} chunks")
        
        # Initialize retrievers
        self.bm25_retriever = BM25Retriever()
        self.bm25_retriever.build_index(self.documents, self.chunk_ids)
        
        self.hybrid_retriever = HybridRetriever(
            bm25_weight=0.4,
            vector_weight=0.6,
            similarity_threshold=0.7
        )
        self.hybrid_retriever.initialize_bm25(self.documents, self.chunk_ids)
    
    def calculate_precision_at_k(self, retrieved: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Precision@K"""
        if k == 0:
            return 0.0
        retrieved_k = set(retrieved[:k])
        if len(retrieved_k) == 0:
            return 0.0
        return len(retrieved_k & relevant) / len(retrieved_k)
    
    def calculate_recall_at_k(self, retrieved: List[int], relevant: Set[int], k: int) -> float:
        """Calculate Recall@K"""
        if len(relevant) == 0:
            return 1.0 if len(retrieved) == 0 else 0.0
        retrieved_k = set(retrieved[:k])
        return len(retrieved_k & relevant) / len(relevant)
    
    def calculate_f1_at_k(self, retrieved: List[int], relevant: Set[int], k: int) -> float:
        """Calculate F1@K"""
        precision = self.calculate_precision_at_k(retrieved, relevant, k)
        recall = self.calculate_recall_at_k(retrieved, relevant, k)
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    def calculate_mrr(self, retrieved: List[int], relevant: Set[int]) -> float:
        """Calculate Mean Reciprocal Rank"""
        if len(relevant) == 0:
            return 0.0
        for rank, chunk_id in enumerate(retrieved, 1):
            if chunk_id in relevant:
                return 1.0 / rank
        return 0.0
    
    def get_relevant_chunks_automated(self, query_data: Dict) -> Set[int]:
        """Get relevant chunks using automated annotation"""
        query = query_data['query']
        expected_sections = query_data.get('expected_sections', [])
        expected_terms = query_data.get('expected_terms', [])
        expected_semantic_terms = query_data.get('expected_semantic_terms', [])
        
        # Get all chunks as list of dicts
        all_chunks = list(self.chunks_dict.values())
        
        # Use automated annotator
        relevant_ids = self.annotator.annotate_relevant_chunks(
            all_chunks,
            query,
            expected_sections,
            expected_terms,
            expected_semantic_terms,
            threshold=0.3  # Relevance threshold
        )
        
        return relevant_ids
    
    def evaluate_query(self, query_data: Dict, k_values: List[int] = [3, 5, 10]) -> Dict:
        """Evaluate a single query"""
        query = query_data['query']
        
        # Get relevant chunks using automated annotation
        relevant = self.get_relevant_chunks_automated(query_data)
        
        if len(relevant) == 0:
            return None
        
        results = {
            'query': query,
            'category': query_data.get('category', 'unknown'),
            'num_relevant': len(relevant),
            'bm25': {},
            'hybrid': {}
        }
        
        # Evaluate BM25-only
        start_time = time.time()
        bm25_results = self.bm25_retriever.retrieve(query, top_k=max(k_values) * 2)
        bm25_time = time.time() - start_time
        bm25_retrieved = [chunk_id for chunk_id, _ in bm25_results]
        
        results['bm25']['retrieval_time'] = bm25_time
        
        for k in k_values:
            results['bm25'][f'precision@{k}'] = self.calculate_precision_at_k(
                bm25_retrieved, relevant, k
            )
            results['bm25'][f'recall@{k}'] = self.calculate_recall_at_k(
                bm25_retrieved, relevant, k
            )
            results['bm25'][f'f1@{k}'] = self.calculate_f1_at_k(
                bm25_retrieved, relevant, k
            )
        
        results['bm25']['mrr'] = self.calculate_mrr(bm25_retrieved, relevant)
        
        # Evaluate Hybrid
        start_time = time.time()
        hybrid_results = self.hybrid_retriever.retrieve(query, top_k=max(k_values) * 2)
        hybrid_time = time.time() - start_time
        hybrid_retrieved = [chunk_id for chunk_id, _ in hybrid_results]
        
        results['hybrid']['retrieval_time'] = hybrid_time
        
        for k in k_values:
            results['hybrid'][f'precision@{k}'] = self.calculate_precision_at_k(
                hybrid_retrieved, relevant, k
            )
            results['hybrid'][f'recall@{k}'] = self.calculate_recall_at_k(
                hybrid_retrieved, relevant, k
            )
            results['hybrid'][f'f1@{k}'] = self.calculate_f1_at_k(
                hybrid_retrieved, relevant, k
            )
        
        results['hybrid']['mrr'] = self.calculate_mrr(hybrid_retrieved, relevant)
        
        return results
    
    def statistical_significance_test(self, bm25_scores: List[float], 
                                     hybrid_scores: List[float],
                                     metric_name: str) -> Dict:
        """Perform paired t-test"""
        if len(bm25_scores) != len(hybrid_scores):
            return None
        
        # Paired t-test
        t_stat, p_value = stats.ttest_rel(hybrid_scores, bm25_scores)
        
        # Calculate means and difference
        bm25_mean = np.mean(bm25_scores)
        hybrid_mean = np.mean(hybrid_scores)
        mean_diff = hybrid_mean - bm25_mean
        percent_improvement = (mean_diff / bm25_mean * 100) if bm25_mean > 0 else 0
        
        # Determine significance
        is_significant = p_value < 0.05
        significance_level = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.4f}"
        
        return {
            'metric': metric_name,
            'bm25_mean': bm25_mean,
            'hybrid_mean': hybrid_mean,
            'mean_difference': mean_diff,
            'percent_improvement': percent_improvement,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': is_significant,
            'significance_level': significance_level
        }


def run_comprehensive_evaluation():
    """Run full evaluation with 40+ queries and statistical testing"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    evaluator = ComprehensiveEvaluator()
    
    # Load queries
    print("\nLoading test queries...")
    try:
        queries = load_test_queries()
        print(f"[OK] Loaded {len(queries)} queries")
    except FileNotFoundError:
        print("[ERROR] Query file not found. Please ensure test_queries/semantic_queries.json exists")
        return
    
    print("\n" + "="*80)
    print("COMPREHENSIVE RETRIEVAL EVALUATION")
    print("="*80)
    print(f"\nTesting {len(queries)} queries...")
    print("Automated relevance annotation using multi-heuristic approach\n")
    
    all_results = []
    k_values = [3, 5, 10]
    
    for i, query_data in enumerate(queries, 1):
        print(f"[{i}/{len(queries)}] {query_data.get('category', 'unknown')}: {query_data['query'][:60]}...")
        
        result = evaluator.evaluate_query(query_data, k_values)
        
        if result:
            all_results.append(result)
            print(f"  Relevant: {result['num_relevant']} | "
                  f"BM25 F1@5: {result['bm25']['f1@5']:.3f} | "
                  f"Hybrid F1@5: {result['hybrid']['f1@5']:.3f}")
    
    if not all_results:
        print("\n[ERROR] No results to evaluate")
        return
    
    print("\n" + "="*80)
    print("AGGREGATE RESULTS")
    print("="*80)
    
    # Calculate aggregate metrics
    metrics_summary = {}
    
    for k in k_values:
        metrics_summary[f'precision@{k}'] = {
            'bm25': [r['bm25'][f'precision@{k}'] for r in all_results],
            'hybrid': [r['hybrid'][f'precision@{k}'] for r in all_results]
        }
        metrics_summary[f'recall@{k}'] = {
            'bm25': [r['bm25'][f'recall@{k}'] for r in all_results],
            'hybrid': [r['hybrid'][f'recall@{k}'] for r in all_results]
        }
        metrics_summary[f'f1@{k}'] = {
            'bm25': [r['bm25'][f'f1@{k}'] for r in all_results],
            'hybrid': [r['hybrid'][f'f1@{k}'] for r in all_results]
        }
    
    metrics_summary['mrr'] = {
        'bm25': [r['bm25']['mrr'] for r in all_results],
        'hybrid': [r['hybrid']['mrr'] for r in all_results]
    }
    
    # Print summary table
    print("\nMETRIC COMPARISON:")
    print("-"*80)
    print(f"{'Metric':<20} {'BM25-only':<15} {'Hybrid':<15} {'Improvement':<15} {'Significance':<15}")
    print("-"*80)
    
    stats_results = []
    
    for metric_name, scores in metrics_summary.items():
        bm25_scores = scores['bm25']
        hybrid_scores = scores['hybrid']
        
        bm25_mean = np.mean(bm25_scores)
        hybrid_mean = np.mean(hybrid_scores)
        improvement = ((hybrid_mean - bm25_mean) / bm25_mean * 100) if bm25_mean > 0 else 0
        
        # Statistical test
        stat_result = evaluator.statistical_significance_test(bm25_scores, hybrid_scores, metric_name)
        stats_results.append(stat_result)
        
        significance = stat_result['significance_level'] if stat_result['is_significant'] else "not significant"
        
        print(f"{metric_name:<20} {bm25_mean:>6.4f}        {hybrid_mean:>6.4f}        "
              f"{improvement:>6.2f}%        {significance:<15}")
    
    # Statistical significance summary
    print("\n" + "="*80)
    print("STATISTICAL SIGNIFICANCE TEST (Paired t-test)")
    print("="*80)
    
    significant_metrics = [r for r in stats_results if r and r['is_significant']]
    
    if significant_metrics:
        print("\n[STATISTICALLY SIGNIFICANT IMPROVEMENTS]:\n")
        for result in significant_metrics:
            print(f"  {result['metric']}:")
            print(f"    BM25: {result['bm25_mean']:.4f}")
            print(f"    Hybrid: {result['hybrid_mean']:.4f}")
            print(f"    Improvement: {result['percent_improvement']:+.2f}%")
            print(f"    {result['significance_level']} (t={result['t_statistic']:.4f})")
            print()
    else:
        print("\nNo statistically significant differences found.")
        print("(This may indicate both methods perform similarly on this test set)")
    
    # Category breakdown
    print("\n" + "="*80)
    print("RESULTS BY CATEGORY")
    print("="*80)
    
    categories = {}
    for result in all_results:
        cat = result.get('category', 'unknown')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(result)
    
    for category, cat_results in categories.items():
        print(f"\n[{category}] ({len(cat_results)} queries):")
        bm25_f1 = np.mean([r['bm25']['f1@5'] for r in cat_results])
        hybrid_f1 = np.mean([r['hybrid']['f1@5'] for r in cat_results])
        improvement = ((hybrid_f1 - bm25_f1) / bm25_f1 * 100) if bm25_f1 > 0 else 0
        print(f"  F1@5: BM25={bm25_f1:.4f}, Hybrid={hybrid_f1:.4f} ({improvement:+.2f}%)")
    
    # Save results
    output_file = "comprehensive_evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_queries': len(all_results),
                'metrics': {
                    name: {
                        'bm25_mean': float(np.mean(scores['bm25'])),
                        'hybrid_mean': float(np.mean(scores['hybrid'])),
                        'improvement_pct': float(((np.mean(scores['hybrid']) - np.mean(scores['bm25'])) / np.mean(scores['bm25']) * 100) if np.mean(scores['bm25']) > 0 else 0)
                    }
                    for name, scores in metrics_summary.items()
                }
            },
            'statistical_tests': [
                {
                    'metric': r['metric'],
                    'is_significant': bool(r['is_significant']),
                    'p_value': float(r['p_value']),
                    'improvement_pct': float(r['percent_improvement'])
                }
                for r in stats_results if r
            ],
            'detailed_results': all_results
        }, f, indent=2)
    
    print(f"\n[OK] Results saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    run_comprehensive_evaluation()
