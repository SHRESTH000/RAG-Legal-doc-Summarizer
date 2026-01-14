"""
Load legal datasets (IPC, CrPC, Evidence Act, Constitution) into PostgreSQL
"""

import json
import os
import sys
from pathlib import Path
import logging

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Fix import conflict: remove datasets from path temporarily
# We need to import huggingface datasets, not our local datasets directory
if str(project_root / "datasets") in sys.path:
    sys.path.remove(str(project_root / "datasets"))

from database.connection import get_db_manager
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_dataset_json(file_path: str) -> dict:
    """Load dataset JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_legal_sections(db: any, dataset_path: str, act_name: str, embedder: SentenceTransformer):
    """Load legal sections from dataset JSON into database"""
    logger.info(f"Loading {act_name} dataset from {dataset_path}")
    
    data = load_dataset_json(dataset_path)
    sections = data.get('sections', [])
    
    logger.info(f"Found {len(sections)} sections")
    
    inserted = 0
    skipped = 0
    
    for section in sections:
        section_num = str(section.get('section_number', ''))
        title = section.get('title', '')
        content = section.get('text', '')
        chapter = section.get('chapter', '')
        part = section.get('part', '')
        classification = section.get('classification', '')
        punishment = section.get('punishment', '')
        triable_by = section.get('triable_by', '')
        compoundable = section.get('compoundable', '')
        metadata = json.dumps(section.get('metadata', {}))
        
        # Generate embedding
        text_to_embed = f"{title} {content}".strip()
        if not text_to_embed or text_to_embed.startswith('[Text for'):
            # Skip placeholder text
            skipped += 1
            continue
        
        try:
            embedding = embedder.encode(text_to_embed, show_progress_bar=False)
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            # Insert into database
            sql = """
                INSERT INTO legal_sections 
                (act_name, section_number, title, content, chapter, part, 
                 classification, punishment, triable_by, compoundable, 
                 metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (act_name, section_number) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    chapter = EXCLUDED.chapter,
                    part = EXCLUDED.part,
                    classification = EXCLUDED.classification,
                    punishment = EXCLUDED.punishment,
                    triable_by = EXCLUDED.triable_by,
                    compoundable = EXCLUDED.compoundable,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
            """
            
            params = (act_name, section_num, title, content, chapter, part,
                     classification, punishment, triable_by, compoundable,
                     metadata, embedding_str)
            
            db.execute_update(sql, params)
            inserted += 1
            
        except Exception as e:
            logger.error(f"Error inserting section {section_num}: {e}")
            skipped += 1
    
    logger.info(f"{act_name}: {inserted} inserted, {skipped} skipped")
    return inserted, skipped


def load_constitution(db: any, dataset_path: str, embedder: SentenceTransformer):
    """Load Constitution articles and schedules"""
    logger.info(f"Loading Constitution dataset from {dataset_path}")
    
    data = load_dataset_json(dataset_path)
    articles = data.get('articles', [])
    schedules = data.get('schedules', [])
    
    logger.info(f"Found {len(articles)} articles and {len(schedules)} schedules")
    
    inserted = 0
    skipped = 0
    
    # Load articles
    for article in articles:
        article_num = str(article.get('article_number', ''))
        title = article.get('title', '')
        content = article.get('text', '')
        part = article.get('part', '')
        schedule = article.get('schedule', '')
        metadata = json.dumps(article.get('metadata', {}))
        
        text_to_embed = f"{title} {content}".strip()
        if not text_to_embed or text_to_embed.startswith('[Text for'):
            skipped += 1
            continue
        
        try:
            embedding = embedder.encode(text_to_embed, show_progress_bar=False)
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            sql = """
                INSERT INTO legal_sections 
                (act_name, section_number, title, content, part, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (act_name, section_number) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    part = EXCLUDED.part,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
            """
            
            params = ('Constitution', article_num, title, content, part, metadata, embedding_str)
            db.execute_update(sql, params)
            inserted += 1
            
        except Exception as e:
            logger.error(f"Error inserting article {article_num}: {e}")
            skipped += 1
    
    # Load schedules
    for schedule in schedules:
        schedule_num = schedule.get('schedule_number', 0)
        title = schedule.get('title', '')
        content = schedule.get('content', '')
        metadata = json.dumps(schedule.get('metadata', {}))
        
        section_num = f"Schedule {schedule_num}"
        text_to_embed = f"{title} {content}".strip()
        if not text_to_embed or text_to_embed.startswith('[Content for'):
            skipped += 1
            continue
        
        try:
            embedding = embedder.encode(text_to_embed, show_progress_bar=False)
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            sql = """
                INSERT INTO legal_sections 
                (act_name, section_number, title, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                ON CONFLICT (act_name, section_number) 
                DO UPDATE SET
                    title = EXCLUDED.title,
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
            """
            
            params = ('Constitution', section_num, title, content, metadata, embedding_str)
            db.execute_update(sql, params)
            inserted += 1
            
        except Exception as e:
            logger.error(f"Error inserting schedule {schedule_num}: {e}")
            skipped += 1
    
    logger.info(f"Constitution: {inserted} inserted, {skipped} skipped")
    return inserted, skipped


def main():
    """Main function to load all legal datasets"""
    logger.info("Starting legal datasets loading...")
    
    # Initialize database and embedder
    db = get_db_manager()
    embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    datasets_dir = project_root / "datasets"
    
    # Dataset mappings
    datasets = [
        ("IPC", datasets_dir / "ipc" / "ipc_sections.json"),
        ("CrPC", datasets_dir / "crpc" / "crpc_sections.json"),
        ("Evidence_Act", datasets_dir / "evidence_act" / "evidence_act_sections.json"),
    ]
    
    total_inserted = 0
    total_skipped = 0
    
    # Load IPC, CrPC, Evidence Act
    for act_name, file_path in datasets:
        if file_path.exists():
            inserted, skipped = load_legal_sections(db, str(file_path), act_name, embedder)
            total_inserted += inserted
            total_skipped += skipped
        else:
            logger.warning(f"Dataset file not found: {file_path}")
    
    # Load Constitution
    constitution_path = datasets_dir / "constitution" / "constitution_articles.json"
    if constitution_path.exists():
        inserted, skipped = load_constitution(db, str(constitution_path), embedder)
        total_inserted += inserted
        total_skipped += skipped
    else:
        logger.warning(f"Constitution file not found: {constitution_path}")
    
    logger.info(f"\n=== Loading Complete ===")
    logger.info(f"Total inserted: {total_inserted}")
    logger.info(f"Total skipped: {total_skipped}")
    
    # Verify counts
    counts = db.execute_query("""
        SELECT act_name, COUNT(*) as count 
        FROM legal_sections 
        GROUP BY act_name
        ORDER BY act_name
    """)
    
    logger.info("\n=== Database Counts ===")
    for row in counts:
        logger.info(f"{row['act_name']}: {row['count']} sections")


if __name__ == "__main__":
    main()
