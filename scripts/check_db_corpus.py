"""Check comprehensive database corpus status"""
import sys
from pathlib import Path
import os

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from database.connection import get_db_manager
import logging

logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)


def check_pgvector():
    """Check if pgvector extension is available"""
    db = get_db_manager()
    
    try:
        result = db.execute_one("""
            SELECT EXISTS(
                SELECT 1 FROM pg_extension WHERE extname = 'vector'
            ) as installed
        """)
        
        if result and result.get('installed'):
            # Try a test query with vector type
            test_result = db.execute_one("""
                SELECT pg_typeof('[]'::vector) as vector_type
            """)
            if test_result:
                return True, "pgvector is installed and working"
        
        return False, "pgvector extension not found"
    except Exception as e:
        return False, f"pgvector check failed: {e}"


def get_corpus_stats():
    """Get comprehensive corpus statistics"""
    db = get_db_manager()
    
    stats = {}
    
    # Judgments
    judgment_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total,
            COUNT(DISTINCT year) as years_covered,
            MIN(year) as earliest_year,
            MAX(year) as latest_year,
            COUNT(DISTINCT court) as courts
        FROM judgments
        WHERE year IS NOT NULL
    """)
    
    if judgment_stats:
        stats['judgments'] = judgment_stats[0]
    
    # Chunks
    chunk_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_chunks,
            COUNT(DISTINCT judgment_id) as judgments_with_chunks,
            AVG(token_count) as avg_tokens_per_chunk,
            SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_embeddings
        FROM judgment_chunks
    """)
    
    if chunk_stats:
        stats['chunks'] = chunk_stats[0]
    
    # Entities
    entity_stats = db.execute_query("""
        SELECT 
            COUNT(*) as total_entities,
            COUNT(DISTINCT judgment_id) as judgments_with_entities,
            COUNT(DISTINCT entity_type) as entity_types
        FROM named_entities
    """)
    
    if chunk_stats:
        stats['entities'] = entity_stats[0]
    
    # Entity types breakdown
    entity_breakdown = db.execute_query("""
        SELECT 
            entity_type,
            COUNT(*) as count
        FROM named_entities
        GROUP BY entity_type
        ORDER BY count DESC
        LIMIT 10
    """)
    
    stats['entity_breakdown'] = entity_breakdown if entity_breakdown else []
    
    # Legal sections
    legal_sections = db.execute_query("""
        SELECT 
            act_name,
            COUNT(*) as sections,
            SUM(CASE WHEN embedding IS NOT NULL THEN 1 ELSE 0 END) as with_embeddings
        FROM legal_sections
        GROUP BY act_name
        ORDER BY act_name
    """)
    
    stats['legal_sections'] = legal_sections if legal_sections else []
    
    # Judgments by year
    by_year = db.execute_query("""
        SELECT 
            year,
            COUNT(*) as count
        FROM judgments
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year DESC
    """)
    
    stats['by_year'] = by_year if by_year else []
    
    # Section types in chunks
    section_types = db.execute_query("""
        SELECT 
            section_type,
            COUNT(*) as count
        FROM judgment_chunks
        WHERE section_type IS NOT NULL
        GROUP BY section_type
        ORDER BY count DESC
    """)
    
    stats['section_types'] = section_types if section_types else []
    
    return stats


def main():
    print("="*70)
    print("DATABASE CORPUS STATUS")
    print("="*70)
    
    # Check pgvector
    pgvector_ok, pgvector_msg = check_pgvector()
    print(f"\npgvector Status: {'[OK]' if pgvector_ok else '[NOT AVAILABLE]'}")
    print(f"  {pgvector_msg}")
    
    if not pgvector_ok:
        print("\nNote: You mentioned installing pgvector. If it's newly installed,")
        print("      you may need to restart PostgreSQL or run:")
        print("      CREATE EXTENSION vector;")
    
    # Get corpus stats
    stats = get_corpus_stats()
    
    # Judgments
    print("\n" + "="*70)
    print("JUDGMENTS")
    print("="*70)
    if stats.get('judgments'):
        j = stats['judgments']
        print(f"Total Judgments: {j.get('total', 0)}")
        print(f"Years Covered: {j.get('years_covered', 0)}")
        if j.get('earliest_year') and j.get('latest_year'):
            print(f"Year Range: {j.get('earliest_year')} - {j.get('latest_year')}")
        print(f"Unique Courts: {j.get('courts', 0)}")
    
    # Chunks
    print("\n" + "="*70)
    print("JUDGMENT CHUNKS")
    print("="*70)
    if stats.get('chunks'):
        c = stats['chunks']
        print(f"Total Chunks: {c.get('total_chunks', 0)}")
        print(f"Judgments with Chunks: {c.get('judgments_with_chunks', 0)}")
        if c.get('avg_tokens_per_chunk'):
            print(f"Avg Tokens per Chunk: {c.get('avg_tokens_per_chunk', 0):.1f}")
        print(f"Chunks with Embeddings: {c.get('chunks_with_embeddings', 0)}")
        if c.get('total_chunks', 0) > 0:
            pct = (c.get('chunks_with_embeddings', 0) / c.get('total_chunks', 1)) * 100
            print(f"Embedding Coverage: {pct:.1f}%")
    
    # Legal Sections
    print("\n" + "="*70)
    print("LEGAL SECTIONS")
    print("="*70)
    if stats.get('legal_sections'):
        for row in stats['legal_sections']:
            print(f"{row['act_name']:20s}: {row['sections']:4d} sections" + 
                  (f" ({row['with_embeddings']} with embeddings)" if row.get('with_embeddings') else ""))
    
    # Entities
    print("\n" + "="*70)
    print("NAMED ENTITIES")
    print("="*70)
    if stats.get('entities'):
        e = stats['entities']
        print(f"Total Entities: {e.get('total_entities', 0)}")
        print(f"Entity Types: {e.get('entity_types', 0)}")
        print(f"Judgments with Entities: {e.get('judgments_with_entities', 0)}")
    
    if stats.get('entity_breakdown'):
        print("\nTop Entity Types:")
        for row in stats['entity_breakdown']:
            print(f"  {row['entity_type']:20s}: {row['count']:5d}")
    
    # By Year
    if stats.get('by_year'):
        print("\n" + "="*70)
        print("JUDGMENTS BY YEAR")
        print("="*70)
        for row in stats['by_year']:
            print(f"  {row['year']}: {row['count']:4d} judgments")
    
    # Section Types
    if stats.get('section_types'):
        print("\n" + "="*70)
        print("DOCUMENT SECTION TYPES")
        print("="*70)
        for row in stats['section_types']:
            print(f"  {row['section_type']:20s}: {row['count']:5d} chunks")
    
    print("\n" + "="*70)
    print("CORPUS SUMMARY")
    print("="*70)
    
    total_data_points = 0
    if stats.get('judgments'):
        total_data_points += stats['judgments'].get('total', 0)
    if stats.get('chunks'):
        total_data_points += stats['chunks'].get('total_chunks', 0)
    if stats.get('legal_sections'):
        total_data_points += sum([r['sections'] for r in stats['legal_sections']])
    
    print(f"\nTotal Data Points: {total_data_points:,}")
    print(f"  - Judgments: {stats['judgments'].get('total', 0) if stats.get('judgments') else 0}")
    print(f"  - Chunks: {stats['chunks'].get('total_chunks', 0) if stats.get('chunks') else 0}")
    print(f"  - Legal Sections: {sum([r['sections'] for r in stats['legal_sections']]) if stats.get('legal_sections') else 0}")
    print(f"  - Entities: {stats['entities'].get('total_entities', 0) if stats.get('entities') else 0}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    if not os.getenv('DB_PASSWORD'):
        os.environ['DB_PASSWORD'] = 'postgres'
    main()
