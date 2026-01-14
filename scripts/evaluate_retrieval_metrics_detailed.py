"""
Detailed Retrieval Evaluation - Testing both keyword and semantic queries
Shows where hybrid approach excels vs BM25-only
"""

import sys
from pathlib import Path
import os
import time
from typing import List, Dict, Tuple, Set
import json

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from retrieval.hybrid_retriever import BM25Retriever, VectorRetriever, HybridRetriever
from database.connection import get_db_manager
import logging
import numpy as np

logging.basicConfig(level=logging.WARNING)


class DetailedRetrievalEvaluator:
    """Evaluate retrieval with keyword vs semantic query distinction"""
    
    def __init__(self):
        self.db = get_db_manager()
        
        print("Loading corpus...")
        chunks = self.db.execute_query(
            "SELECT id, content FROM judgment_chunks ORDER BY id LIMIT 50000"
        )
        
        if not chunks:
            raise ValueError("No chunks found in database")
        
        self.documents = [row['content'] for row in chunks]
        self.chunk_ids = [row['id'] for row in chunks]
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
    
    def find_relevant_chunks(self, query: str, expected_sections: List[str], 
                            expected_terms: List[str], expected_semantic_terms: List[str] = None,
                            top_n: int = 30) -> Set[int]:
        """Find relevant chunks using both keyword and semantic matching"""
        relevant = set()
        
        for i, doc in enumerate(self.documents):
            doc_lower = doc.lower()
            
            # Keyword matches (exact terms/sections)
            section_match = any(section.lower() in doc_lower for section in expected_sections)
            term_match = any(term.lower() in doc_lower for term in expected_terms)
            
            # Semantic matches (related concepts)
            semantic_match = False
            if expected_semantic_terms:
                semantic_match = any(term.lower() in doc_lower for term in expected_semantic_terms)
            
            if section_match or term_match or semantic_match:
                relevant.add(self.chunk_ids[i])
        
        # Limit to most relevant if too many
        if len(relevant) > top_n:
            bm25_scores = self.bm25_retriever.retrieve(query, top_k=len(relevant))
            relevant_ids = [chunk_id for chunk_id, _ in bm25_scores]
            relevant = set(relevant_ids[:top_n])
        
        return relevant
    
    def evaluate_query(self, query: str, query_type: str, expected_sections: List[str], 
                      expected_terms: List[str], expected_semantic_terms: List[str] = None,
                      k_values: List[int] = [3, 5, 10]) -> Dict:
        """Evaluate a single query"""
        
        relevant = self.find_relevant_chunks(query, expected_sections, expected_terms, 
                                            expected_semantic_terms)
        
        if len(relevant) == 0:
            return None
        
        results = {
            'query': query,
            'query_type': query_type,
            'num_relevant': len(relevant),
            'bm25': {},
            'hybrid': {}
        }
        
        # BM25-only
        start_time = time.time()
        bm25_results = self.bm25_retriever.retrieve(query, top_k=max(k_values))
        bm25_time = time.time() - start_time
        bm25_retrieved = [chunk_id for chunk_id, _ in bm25_results]
        
        results['bm25']['retrieval_time'] = bm25_time
        results['bm25']['retrieved_ids'] = bm25_retrieved[:20]
        
        for k in k_values:
            results['bm25'][f'precision@{k}'] = self.calculate_precision_at_k(
                bm25_retrieved, relevant, k
            )
            results['bm25'][f'recall@{k}'] = self.calculate_recall_at_k(
                bm25_retrieved, relevant, k
            )
        
        # Hybrid
        start_time = time.time()
        hybrid_results = self.hybrid_retriever.retrieve(query, top_k=max(k_values))
        hybrid_time = time.time() - start_time
        hybrid_retrieved = [chunk_id for chunk_id, _ in hybrid_results]
        
        results['hybrid']['retrieval_time'] = hybrid_time
        results['hybrid']['retrieved_ids'] = hybrid_retrieved[:20]
        
        for k in k_values:
            results['hybrid'][f'precision@{k}'] = self.calculate_precision_at_k(
                hybrid_retrieved, relevant, k
            )
            results['hybrid'][f'recall@{k}'] = self.calculate_recall_at_k(
                hybrid_retrieved, relevant, k
            )
        
        return results


def run_detailed_evaluation():
    """Run evaluation with both keyword and semantic queries"""
    
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    
    evaluator = DetailedRetrievalEvaluator()
    
    # Test queries categorized by type
    keyword_queries = [
        {
            "query": "IPC Section 302 murder punishment",
            "query_type": "keyword_exact",
            "expected_sections": ["IPC Section 302", "Section 302"],
            "expected_terms": ["murder", "punishment"],
            "description": "Exact Section Reference"
        },
        {
            "query": "CrPC Section 439 bail cancellation",
            "query_type": "keyword_exact",
            "expected_sections": ["CrPC Section 439"],
            "expected_terms": ["bail", "cancellation"],
            "description": "Exact Section with Terms"
        }
    ]
    
    semantic_queries = [
        {
            "query": "What happens when someone intentionally kills another person?",
            "query_type": "semantic",
            "expected_sections": ["Section 302", "Section 300"],
            "expected_terms": ["murder"],
            "expected_semantic_terms": ["intentional killing", "homicide", "culpable homicide", 
                                       "intentional", "kills", "death penalty"],
            "description": "Semantic: Murder Concept"
        },
        {
            "query": "How can an accused person be released before trial conclusion?",
            "query_type": "semantic",
            "expected_sections": ["Section 439", "Section 437", "Section 438"],
            "expected_terms": ["bail"],
            "expected_semantic_terms": ["release", "trial", "before judgment", "custody", 
                                       "interim relief", "liberty"],
            "description": "Semantic: Bail Concept"
        },
        {
            "query": "When can a statement made by a person before death be used as evidence?",
            "query_type": "semantic",
            "expected_sections": ["Evidence Act Section 32", "Section 32"],
            "expected_terms": ["dying declaration"],
            "expected_semantic_terms": ["statement before death", "evidence", "admissible", 
                                       "final statement", "deathbed"],
            "description": "Semantic: Dying Declaration"
        },
        {
            "query": "What factors determine the severity of punishment for causing death?",
            "query_type": "semantic",
            "expected_sections": ["Section 302", "Section 304", "Section 300"],
            "expected_terms": ["murder", "culpable homicide", "punishment"],
            "expected_semantic_terms": ["severity", "factors", "aggravating", "mitigating", 
                                       "sentencing", "circumstances"],
            "description": "Semantic: Sentencing Factors"
        },
        {
            "query": "How is guilt established when multiple people act together in a crime?",
            "query_type": "semantic",
            "expected_sections": ["IPC Section 34", "Section 34"],
            "expected_terms": ["common intention", "joint liability"],
            "expected_semantic_terms": ["multiple people", "together", "collective action", 
                                       "group crime", "jointly"],
            "description": "Semantic: Common Intention"
        }
    ]
    
    all_queries = keyword_queries + semantic_queries
    
    print("\n" + "="*80)
    print("DETAILED RETRIEVAL EVALUATION")
    print("="*80)
    print("\nQuery Types:")
    print("  - Keyword Queries: Exact section/term matches (BM25 should excel)")
    print("  - Semantic Queries: Conceptual queries (Hybrid should excel)\n")
    
    all_results = []
    k_values = [3, 5, 10]
    
    for i, test in enumerate(all_queries, 1):
        print(f"[{i}/{len(all_queries)}] {test['query_type']}: {test['description']}")
        
        result = evaluator.evaluate_query(
            test['query'],
            test['query_type'],
            test['expected_sections'],
            test['expected_terms'],
            test.get('expected_semantic_terms', []),
            k_values
        )
        
        if result:
            all_results.append(result)
            print(f"  Relevant: {result['num_relevant']} | "
                  f"BM25 P@5: {result['bm25']['precision@5']:.3f} | "
                  f"Hybrid P@5: {result['hybrid']['precision@5']:.3f}")
    
    if not all_results:
        print("\n[ERROR] No results to evaluate")
        return
    
    # Separate by query type
    keyword_results = [r for r in all_results if r['query_type'] == 'keyword_exact']
    semantic_results = [r for r in all_results if r['query_type'] == 'semantic']
    
    print("\n" + "="*80)
    print("RESULTS BY QUERY TYPE")
    print("="*80)
    
    # Keyword queries analysis
    if keyword_results:
        print("\n[KEYWORD QUERIES] - Exact section/term matches:")
        print("-"*80)
        
        for k in k_values:
            bm25_prec = np.mean([r['bm25'][f'precision@{k}'] for r in keyword_results])
            hybrid_prec = np.mean([r['hybrid'][f'precision@{k}'] for r in keyword_results])
            bm25_recall = np.mean([r['bm25'][f'recall@{k}'] for r in keyword_results])
            hybrid_recall = np.mean([r['hybrid'][f'recall@{k}'] for r in keyword_results])
            
            print(f"\nK={k}:")
            print(f"  Precision: BM25={bm25_prec:.4f}, Hybrid={hybrid_prec:.4f}, "
                  f"Diff={((hybrid_prec-bm25_prec)/bm25_prec*100):+.2f}%")
            print(f"  Recall:    BM25={bm25_recall:.4f}, Hybrid={hybrid_recall:.4f}, "
                  f"Diff={((hybrid_recall-bm25_recall)/bm25_recall*100):+.2f}%")
    
    # Semantic queries analysis
    if semantic_results:
        print("\n[SEMANTIC QUERIES] - Conceptual/paraphrased queries:")
        print("-"*80)
        
        for k in k_values:
            bm25_prec = np.mean([r['bm25'][f'precision@{k}'] for r in semantic_results])
            hybrid_prec = np.mean([r['hybrid'][f'precision@{k}'] for r in semantic_results])
            bm25_recall = np.mean([r['bm25'][f'recall@{k}'] for r in semantic_results])
            hybrid_recall = np.mean([r['hybrid'][f'recall@{k}'] for r in semantic_results])
            
            improvement_prec = ((hybrid_prec - bm25_prec) / bm25_prec * 100) if bm25_prec > 0 else 0
            improvement_recall = ((hybrid_recall - bm25_recall) / bm25_recall * 100) if bm25_recall > 0 else 0
            
            print(f"\nK={k}:")
            print(f"  Precision: BM25={bm25_prec:.4f}, Hybrid={hybrid_prec:.4f}, "
                  f"Improvement={improvement_prec:+.2f}%")
            print(f"  Recall:    BM25={bm25_recall:.4f}, Hybrid={hybrid_recall:.4f}, "
                  f"Improvement={improvement_recall:+.2f}%")
    
    # Overall comparison
    print("\n" + "="*80)
    print("OVERALL COMPARISON")
    print("="*80)
    
    print("\n[ALL QUERIES] - Combined results:")
    for k in k_values:
        bm25_prec = np.mean([r['bm25'][f'precision@{k}'] for r in all_results])
        hybrid_prec = np.mean([r['hybrid'][f'precision@{k}'] for r in all_results])
        bm25_recall = np.mean([r['bm25'][f'recall@{k}'] for r in all_results])
        hybrid_recall = np.mean([r['hybrid'][f'recall@{k}'] for r in all_results])
        
        improvement_prec = ((hybrid_prec - bm25_prec) / bm25_prec * 100) if bm25_prec > 0 else 0
        improvement_recall = ((hybrid_recall - bm25_recall) / bm25_recall * 100) if bm25_recall > 0 else 0
        
        print(f"\nK={k}:")
        print(f"  Precision: BM25={bm25_prec:.4f}, Hybrid={hybrid_prec:.4f} "
              f"({improvement_prec:+.2f}%)")
        print(f"  Recall:    BM25={bm25_recall:.4f}, Hybrid={hybrid_recall:.4f} "
              f"({improvement_recall:+.2f}%)")
    
    # Key findings
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    
    if semantic_results:
        semantic_improvement = np.mean([
            ((r['hybrid']['precision@5'] - r['bm25']['precision@5']) / r['bm25']['precision@5'] * 100)
            for r in semantic_results if r['bm25']['precision@5'] > 0
        ])
        
        if semantic_improvement > 0:
            print(f"\n[IMPORTANT] Hybrid approach shows {semantic_improvement:.2f}% improvement")
            print("            on semantic queries (real-world user queries)")
            print("\nThis demonstrates that hybrid retrieval is better for:")
            print("  - Natural language queries")
            print("  - Conceptual searches")
            print("  - Paraphrased questions")
            print("  - Legal concept explanations")
    
    # Save results
    output_file = "detailed_retrieval_evaluation.json"
    with open(output_file, 'w') as f:
        json.dump({
            'keyword_results': keyword_results,
            'semantic_results': semantic_results,
            'all_results': all_results
        }, f, indent=2)
    
    print(f"\n[OK] Detailed results saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    run_detailed_evaluation()
