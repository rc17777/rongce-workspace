"""
Ingestion V2 — 三轮分类 + 辐射迭代 主入库脚本
P0-1 dedup | P0-2 exception handling | P0-3 cross-cutting themes | P0-4 lower threshold
"""
import sys, os, json, time, hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# Add parent dir for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from taxonomy_manager import get_taxonomy, TaxonomyManager
from ingestion_round1 import classify_round1, extract_doc_number, infer_source_type
from ingestion_round2 import run_round2, Round2Result
from ingestion_round3 import run_round3, process_round3_results, Round3Result


# ---- Deduplication ----

def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text[:5000].encode('utf-8')).hexdigest()[:16]


def is_duplicate(content_hash: str, title: str,
                 ingested_hashes: Optional[set] = None) -> bool:
    """Check if document was already ingested."""
    if ingested_hashes is None:
        ingested_hashes = set()
    if content_hash in ingested_hashes:
        return True
    # TODO: Check against stored index
    return False


# ---- Document Metadata Builder ----

def build_document_metadata(doc_text: str, doc_title: str,
                            source_url: str, source_type: str,
                            doc_number: str,
                            r1_result, r2_result: Round2Result,
                            r3_result: Optional[Round3Result],
                            dedup_result: dict,
                            tags: List[str]) -> dict:
    """Build complete document metadata YAML structure."""
    now = datetime.now().isoformat()

    metadata = {
        'ingestion_version': '2.0',
        'ingested_at': now,
        'source': {
            'url': source_url,
            'type': source_type,
            'title': doc_title,
            'doc_number': doc_number,
            'publish_date': '',  # filled by caller if available
            'content_hash': compute_content_hash(doc_text),
        },
        'classification': {
            'round1': {
                'method': 'keyword_match',
                'direct_hits': r1_result.direct_hits,
                'matched_by': r1_result.matched_by,
            },
            'round2': {
                'method': 'llm_radiation',
                'model': get_taxonomy().get_llm_config().get('round2_model', 'deepseek-v4-flash'),
                'degraded': r2_result.degraded,
                'error': r2_result.error,
                'radiation_hits': [],
            },
            'round3': {
                'method': 'llm_novelty_detection',
                'model': get_taxonomy().get_llm_config().get('round3_model', 'deepseek-v4-pro'),
                'degraded': r3_result.degraded if r3_result else False,
                'error': r3_result.error if r3_result else None,
                'novel_domains': [],
                'cross_cutting_theme': r3_result.cross_cutting_theme if r3_result else None,
            },
            'final_lines': dedup_result['lines'],                   # P0-1 dedup
            'provenance': dedup_result.get('provenance', {}),       # P0-1 provenance
            'degradation_level': _compute_degradation(r1_result, r2_result, r3_result),
        },
        'tags': tags,
        'summary': '',
        'impact_assessment': '',
    }

    # Fill radiation hits
    for rh in r2_result.radiation_hits:
        metadata['classification']['round2']['radiation_hits'].append({
            'line': rh.line_id,
            'aspect': rh.aspect,
            'relevance': rh.relevance,
            'reason': rh.reason,
        })

    # Fill novel domains
    if r3_result and r3_result.novel_domains:
        for nd in r3_result.novel_domains:
            metadata['classification']['round3']['novel_domains'].append({
                'proposed_name': nd.proposed_name,
                'description': nd.description,
                'closest_existing_line': nd.closest_existing_line,
                'target_clients': nd.target_clients,
                'confidence': nd.confidence,
                'reasoning': nd.reasoning,
            })

    return metadata


def _compute_degradation(r1, r2, r3) -> int:
    """P0-2: Compute degradation level (0=full, 3=all failed)."""
    if r2.degraded and (r3 and r3.degraded):
        return 3
    if r3 and r3.degraded:
        return 2
    if r2.degraded:
        return 1
    return 0


# ---- Main Ingestion Pipeline ----

def ingest_document(doc_text: str, doc_title: str = '',
                    source_url: str = '', source_type: str = '',
                    publish_date: str = '',
                    existing_hashes: Optional[set] = None,
                    api_config: Optional[dict] = None,
                    dry_run: bool = False) -> Dict:
    """
    Full ingestion pipeline for a single document.

    Returns dict with status, metadata, and any notifications.
    """
    start_time = time.time()

    # Step 0: Preprocessing
    content_hash = compute_content_hash(doc_text)
    if is_duplicate(content_hash, doc_title, existing_hashes):
        return {'status': 'skipped', 'reason': 'duplicate'}

    if source_type:
        inferred_type = source_type
    else:
        inferred_type = infer_source_type(doc_text, source_url)

    doc_number = extract_doc_number(doc_text)

    if dry_run:
        return {'status': 'dry_run', 'source_type': inferred_type, 'doc_number': doc_number}

    print(f"[ingest] {doc_title[:60]} | type={inferred_type} | docnum={doc_number}")

    # Round 1: Rule-based classification (zero cost)
    try:
        r1 = classify_round1(doc_text, doc_title, doc_number)
        print(f"  R1: {r1.direct_hits if r1.direct_hits else '零命中'} ({len(r1.matched_by)} keywords)")
    except Exception as e:
        print(f"  R1 FAILED: {e}")
        return {'status': 'error', 'reason': f'Round 1 failed: {e}', 'degradation': 3}

    # Round 2: LLM radiation analysis
    r2 = run_round2(doc_text, doc_title, api_config)
    print(f"  R2: {len(r2.radiation_hits)} radiation hits" +
          (f' [DEGRADED: {r2.error}]' if r2.degraded else ''))

    # P0-1: Dedup and merge
    dedup = TaxonomyManager.deduplicate_lines(
        r1.direct_hits,
        [{'line_id': h.line_id, 'relevance': h.relevance} for h in r2.radiation_hits]
    )
    print(f"  Dedup: {dedup['lines']} (from {len(r1.direct_hits)} direct + {len(r2.radiation_hits)} radiation)")

    # Round 3: Novelty detection (conditional)
    r3 = None
    notifications = []
    should_run_r3 = (not r1.direct_hits and not r2.radiation_hits) or \
                    inferred_type == 'government_policy'

    if should_run_r3:
        r3 = run_round3(doc_text, doc_title, inferred_type, r1.direct_hits, r2, api_config)
        print(f"  R3: {'novel!' if r3.has_novel_domain else 'no novel'} " +
              f"cct={'✓' if r3.cross_cutting_theme else '✗'}" +
              (f' [DEGRADED: {r3.error}]' if r3.degraded else ''))

        if r3.has_novel_domain or r3.cross_cutting_theme:
            notifications = process_round3_results(r3, doc_title, source_url)

    # P0-3: Store cross-cutting theme in taxonomy
    if r3 and r3.cross_cutting_theme:
        taxonomy = get_taxonomy()
        taxonomy.add_or_update_meta_tag(
            name=r3.cross_cutting_theme,
            description=f'Auto-detected from: {doc_title}',
            affected_lines=dedup['lines'],
        )

    # Build metadata
    tags = []  # Can be extended with keyword extraction
    metadata = build_document_metadata(
        doc_text, doc_title, source_url, inferred_type,
        doc_number, r1, r2, r3, dedup, tags
    )
    metadata['source']['publish_date'] = publish_date

    elapsed = time.time() - start_time
    print(f"  Done in {elapsed:.1f}s | final_lines={dedup['lines']} | " +
          f"degradation={metadata['classification']['degradation_level']}")

    return {
        'status': 'success',
        'content_hash': content_hash,
        'metadata': metadata,
        'notifications': notifications,
        'elapsed_seconds': elapsed,
        'degradation_level': metadata['classification']['degradation_level'],
    }


# ---- Batch Ingestion ----

def ingest_batch(documents: List[dict], api_config: Optional[dict] = None,
                 dry_run: bool = False) -> Dict:
    """
    Batch ingest multiple documents.

    documents: list of dicts with keys:
        - text (required)
        - title (optional)
        - url (optional)
        - source_type (optional)
        - publish_date (optional)
    """
    results = {
        'total': len(documents),
        'success': 0,
        'skipped': 0,
        'error': 0,
        'notifications': [],
        'documents': [],
    }
    hashes = set()

    for i, doc in enumerate(documents):
        print(f"\n[{i+1}/{len(documents)}]", end=" ")
        result = ingest_document(
            doc_text=doc['text'],
            doc_title=doc.get('title', f'untitled_{i}'),
            source_url=doc.get('url', ''),
            source_type=doc.get('source_type', ''),
            publish_date=doc.get('publish_date', ''),
            existing_hashes=hashes,
            api_config=api_config,
            dry_run=dry_run,
        )

        if result['status'] == 'success':
            results['success'] += 1
            hashes.add(result['content_hash'])
            results['notifications'].extend(result.get('notifications', []))
            results['documents'].append(result['metadata'])
        elif result['status'] == 'skipped':
            results['skipped'] += 1
        else:
            results['error'] += 1

    return results


# ---- CLI ----

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Ingestion V2 — 三轮分类入库')
    parser.add_argument('--file', '-f', help='Single file to ingest')
    parser.add_argument('--title', '-t', help='Document title')
    parser.add_argument('--url', '-u', help='Source URL')
    parser.add_argument('--type', help='Source type override')
    parser.add_argument('--dry-run', action='store_true', help='Dry run without API calls')
    parser.add_argument('--stats', action='store_true', help='Show taxonomy statistics')
    args = parser.parse_args()

    if args.stats:
        taxonomy = get_taxonomy()
        stats = taxonomy.get_stats()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
        sys.exit(0)

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()

        result = ingest_document(
            doc_text=text,
            doc_title=args.title or Path(args.file).stem,
            source_url=args.url or '',
            source_type=args.type or '',
            dry_run=args.dry_run,
        )

        if args.dry_run:
            print(f"Dry run: type={result.get('source_type')}, docnum={result.get('doc_number')}")
        else:
            print(f"\nResult: {result['status']}")
            if result['status'] == 'success':
                m = result['metadata']['classification']
                print(f"  Lines: {m['final_lines']}")
                print(f"  Provenance: {m['provenance']}")
                print(f"  Degradation: Level {m['degradation_level']}")
                print(f"  Time: {result['elapsed_seconds']:.1f}s")
                for n in result.get('notifications', []):
                    print(f"  🔔 {n['message']}")
    else:
        parser.print_help()
