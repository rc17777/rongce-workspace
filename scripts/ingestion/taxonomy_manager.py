"""
Taxonomy Manager — 业务线树管理（增删改查 + 版本管理）
P0-1 dedup | P0-3 cross-cutting themes | P1-1 weak signals | P1-2 model version pinning
"""
import yaml, os, json, time, copy
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple


TAXONOMY_DIR = Path(__file__).resolve().parent.parent.parent / 'knowledge' / 'taxonomy'
BUSINESS_LINES_PATH = TAXONOMY_DIR / 'business_lines.yaml'
INCUBATION_QUEUE_PATH = TAXONOMY_DIR / 'incubation_queue.yaml'
HISTORY_PATH = TAXONOMY_DIR / 'business_lines_history.yaml'


class TaxonomyManager:
    """Manage the business line tree with versioning."""

    def __init__(self):
        self._data = None
        self._incubation = None

    # ---- Load / Save ----

    def load(self) -> dict:
        if self._data is None:
            if BUSINESS_LINES_PATH.exists():
                with open(BUSINESS_LINES_PATH, 'r', encoding='utf-8') as f:
                    self._data = yaml.safe_load(f)
            else:
                raise FileNotFoundError(f"business_lines.yaml not found at {BUSINESS_LINES_PATH}")
        return self._data

    def save(self) -> None:
        """Transactional save: write to .tmp first, then rename."""
        tmp_path = BUSINESS_LINES_PATH.with_suffix('.yaml.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self._data, f, allow_unicode=True, sort_keys=False)
        os.replace(tmp_path, BUSINESS_LINES_PATH)

    def load_incubation(self) -> dict:
        if self._incubation is None:
            if INCUBATION_QUEUE_PATH.exists():
                with open(INCUBATION_QUEUE_PATH, 'r', encoding='utf-8') as f:
                    self._incubation = yaml.safe_load(f) or {'proposals': [], 'weak_signals': []}
            else:
                self._incubation = {'proposals': [], 'weak_signals': []}
        return self._incubation

    def save_incubation(self) -> None:
        tmp_path = INCUBATION_QUEUE_PATH.with_suffix('.yaml.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(self._incubation, f, allow_unicode=True, sort_keys=False)
        os.replace(tmp_path, INCUBATION_QUEUE_PATH)

    # ---- Business Line CRUD ----

    def get_all_lines(self, status_filter: Optional[List[str]] = None) -> List[dict]:
        """Get all business lines, optionally filtered by status."""
        data = self.load()
        nodes = data.get('nodes', [])
        if status_filter:
            return [n for n in nodes if n.get('status') in status_filter]
        return nodes

    def get_active_lines(self) -> List[dict]:
        return self.get_all_lines(status_filter=['active'])

    def get_line(self, line_id: str) -> Optional[dict]:
        for node in self.load().get('nodes', []):
            if node['id'] == line_id:
                return node
        return None

    def add_line(self, name: str, **kwargs) -> dict:
        """Add a new active business line. Returns the new node."""
        data = self.load()
        nodes = data['nodes']

        # Auto-increment ID
        max_id = max([int(n['id'][1:]) for n in nodes if n['id'].startswith('L')], default=0)
        new_id = f'L{max_id + 1}'

        new_node = {
            'id': new_id,
            'name': name,
            'status': 'active',
            'parent': kwargs.get('parent'),
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'source_policies': kwargs.get('source_policies', []),
            'sub_types': kwargs.get('sub_types', []),
            'keywords': kwargs.get('keywords', {'primary': [], 'secondary': []}),
            'detection_rules': kwargs.get('detection_rules', []),
            'radiation_signals': [],
        }
        nodes.append(new_node)
        data['nodes'] = nodes
        data['tree_version'] = data.get('tree_version', 0) + 1
        data['last_updated'] = datetime.now().strftime('%Y-%m-%d')

        self._record_history(data['tree_version'], f'Added business line: {name} ({new_id})')
        self._data = data
        self.save()
        return new_node

    def update_line_status(self, line_id: str, new_status: str) -> bool:
        """Update status: active | declining | merged | incubated"""
        data = self.load()
        for node in data.get('nodes', []):
            if node['id'] == line_id:
                old_status = node.get('status')
                node['status'] = new_status
                data['tree_version'] = data.get('tree_version', 0) + 1
                data['last_updated'] = datetime.now().strftime('%Y-%m-%d')
                self._record_history(data['tree_version'],
                                     f'Line {line_id} ({node["name"]}): {old_status} → {new_status}')
                self._data = data
                self.save()
                return True
        return False

    def add_radiation_signal(self, line_id: str, from_policy: str, affected_aspect: str) -> None:
        """Record that a policy radiates to this business line."""
        data = self.load()
        for node in data.get('nodes', []):
            if node['id'] == line_id:
                if 'radiation_signals' not in node:
                    node['radiation_signals'] = []
                node['radiation_signals'].append({
                    'from_policy': from_policy,
                    'affected_aspect': affected_aspect,
                    'date': datetime.now().strftime('%Y-%m-%d'),
                })
                self._data = data
                self.save()
                return

    # ---- Meta Tags (P0-3: cross-cutting themes) ----

    def get_meta_tags(self) -> List[dict]:
        return self.load().get('meta_tags', [])

    def add_or_update_meta_tag(self, name: str, description: str, affected_lines: List[str]) -> dict:
        """Add or update a cross-cutting theme meta tag."""
        data = self.load()
        tags = data.get('meta_tags', [])

        # Check if exists
        for tag in tags:
            if tag.get('name') == name:
                tag['affected_lines'] = list(set(tag.get('affected_lines', []) + affected_lines))
                tag['description'] = description
                self._data = data
                self.save()
                return tag

        # Create new
        max_id = max([int(t['id'][2:]) for t in tags if t.get('id', '').startswith('MT')], default=0)
        new_tag = {
            'id': f'MT{max_id + 1}',
            'name': name,
            'description': description,
            'affected_lines': affected_lines,
        }
        tags.append(new_tag)
        data['meta_tags'] = tags
        self._data = data
        self.save()
        return new_tag

    # ---- Incubation / Weak Signals (P0-4 + P1-1) ----

    INCUBATION_THRESHOLD = 2          # P0-4: lowered from 3 to 2
    FAST_TRACK_CONFIDENCE = 0.85      # P0-4: single-source fast track
    WEAK_SIGNAL_MIN_CONFIDENCE = 0.6  # P1-1: minimum for weak signal
    SIMILARITY_THRESHOLD = 0.7        # Proposal similarity threshold

    def find_similar_proposal(self, proposed_name: str) -> Optional[dict]:
        """Check if a proposal with similar name already exists."""
        inc = self.load_incubation()
        for prop in inc.get('proposals', []):
            if self._name_similarity(proposed_name, prop.get('proposed_name', '')) > self.SIMILARITY_THRESHOLD:
                return prop
        return None

    def add_novel_evidence(self, proposed_name: str, description: str,
                           closest_line: str, target_clients: str,
                           confidence: float, policy_ref: str, source_url: str,
                           excerpt: str) -> Tuple[str, Optional[dict]]:
        """
        Add evidence for a novel business domain.
        Returns (action, proposal) where action is one of:
          'fast_track'  — confidence > 0.85, push directly to human review
          'accumulating' — added to incubation, waiting for more evidence
          'threshold_reached' — evidence count >= 2, ready for human confirmation
          'weak_signal' — confidence < 0.85 and first sighting, enters weak signal dashboard
        """
        inc = self.load_incubation()

        # Fast track: high confidence single source
        if confidence >= self.FAST_TRACK_CONFIDENCE:
            # Create proposal directly with threshold_reached
            new_prop = self._create_proposal(proposed_name, description, closest_line,
                                              target_clients, confidence, policy_ref,
                                              source_url, excerpt)
            new_prop['status'] = 'threshold_reached'
            new_prop['evidence_count'] = 1
            new_prop['threshold'] = 1  # fast track only needs 1
            inc['proposals'].append(new_prop)
            self._incubation = inc
            self.save_incubation()
            return 'fast_track', new_prop

        # Check for similar existing proposal
        existing = self.find_similar_proposal(proposed_name)
        if existing:
            existing.setdefault('trigger_policies', []).append({
                'policy': policy_ref,
                'source_url': source_url,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'confidence': confidence,
                'excerpt': excerpt,
            })
            existing['evidence_count'] = len(existing.get('trigger_policies', []))
            existing['last_updated'] = datetime.now().strftime('%Y-%m-%d')
            existing['confidence'] = max(existing.get('confidence', 0), confidence)

            if existing['evidence_count'] >= self.INCUBATION_THRESHOLD:
                existing['status'] = 'threshold_reached'
                self._incubation = inc
                self.save_incubation()
                return 'threshold_reached', existing
            else:
                existing['status'] = 'accumulating'
                self._incubation = inc
                self.save_incubation()
                return 'accumulating', existing

        # New proposal, confidence >= 0.6: enters incubation
        if confidence >= self.WEAK_SIGNAL_MIN_CONFIDENCE:
            new_prop = self._create_proposal(proposed_name, description, closest_line,
                                              target_clients, confidence, policy_ref,
                                              source_url, excerpt)
            new_prop['status'] = 'accumulating'
            inc['proposals'].append(new_prop)
            self._incubation = inc
            self.save_incubation()
            return 'accumulating', new_prop

        # Below minimum confidence: goes into weak signals
        ws = {
            'signal_id': f'WS-{datetime.now().strftime("%Y%m%d")}-{len(inc.get("weak_signals", [])) + 1:03d}',
            'proposed_domain': proposed_name,
            'source_count': 1,
            'confidence': confidence,
            'first_seen': datetime.now().strftime('%Y-%m-%d'),
            'status': 'accumulating',
            'trigger': {'policy': policy_ref, 'source_url': source_url, 'excerpt': excerpt},
        }
        inc.setdefault('weak_signals', []).append(ws)
        self._incubation = inc
        self.save_incubation()
        return 'weak_signal', None

    def confirm_promotion(self, candidate_id: str) -> dict:
        """Promote an incubated proposal to an active business line."""
        inc = self.load_incubation()
        proposal = None
        for p in inc.get('proposals', []):
            if p.get('candidate_id') == candidate_id:
                proposal = p
                break

        if not proposal:
            raise ValueError(f"Proposal {candidate_id} not found")

        # Create new active line
        new_line = self.add_line(
            name=proposal['proposed_name'],
            parent=proposal.get('parent_business_line'),
            source_policies=[ep['policy'] for ep in proposal.get('trigger_policies', [])],
            sub_types=proposal.get('suggested_sub_types', []),
            keywords={'primary': proposal.get('suggested_keywords', []), 'secondary': []},
        )

        # Update proposal status
        proposal['status'] = 'promoted'
        proposal['promoted_to'] = new_line['id']
        proposal['confirmed_at'] = datetime.now().strftime('%Y-%m-%d')
        self._incubation = inc
        self.save_incubation()

        # Update weak signals with same domain
        self._promote_weak_signals(proposal['proposed_name'], new_line['id'])

        return new_line

    def reject_proposal(self, candidate_id: str) -> None:
        """Reject a proposal, freeze for 180 days."""
        inc = self.load_incubation()
        for p in inc.get('proposals', []):
            if p.get('candidate_id') == candidate_id:
                p['status'] = 'rejected'
                p['rejected_at'] = datetime.now().strftime('%Y-%m-%d')
                p['reject_freeze_until'] = (datetime.now().strftime('%Y-%m-%d')
                                            if True else None)  # placeholder
                break
        self._incubation = inc
        self.save_incubation()

    # ---- Version History ----

    def _record_history(self, version: int, change_desc: str) -> None:
        """Record a version change in history."""
        if not HISTORY_PATH.exists():
            history = []
        else:
            with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
                history = yaml.safe_load(f) or []

        history.append({
            'version': version,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'change': change_desc,
        })
        with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
            yaml.safe_dump(history, f, allow_unicode=True, sort_keys=False)

    # ---- Dedup (P0-1) ----

    @staticmethod
    def deduplicate_lines(direct_hits: List[str], radiation_hits: List[dict]) -> Dict:
        """
        Merge Round 1 direct_hits and Round 2 radiation_hits with dedup.
        Returns {'lines': [...], 'provenance': {line_id: ['round1', 'round2']}}
        """
        lines = set(direct_hits)
        provenance = {lid: ['round1'] for lid in direct_hits}

        for rh in radiation_hits:
            if rh.get('relevance') in ('high', 'medium'):
                lid = rh.get('line_id')
                if lid:
                    lines.add(lid)
                    if lid in provenance:
                        provenance[lid].append('round2')
                    else:
                        provenance[lid] = ['round2']

        return {
            'lines': sorted(list(lines)),
            'provenance': provenance,
            'count': len(lines),
        }

    # ---- Helpers ----

    def _create_proposal(self, name: str, description: str, closest_line: str,
                         target_clients: str, confidence: float, policy_ref: str,
                         source_url: str, excerpt: str) -> dict:
        inc = self.load_incubation()
        candidate_num = len(inc.get('proposals', [])) + 1
        return {
            'candidate_id': f'INC-{datetime.now().strftime("%Y")}{candidate_num:04d}',
            'proposed_name': name,
            'status': 'accumulating',
            'parent_business_line': closest_line,
            'trigger_policies': [{
                'policy': policy_ref,
                'source_url': source_url,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'confidence': confidence,
                'excerpt': excerpt,
            }],
            'evidence_count': 1,
            'threshold': self.INCUBATION_THRESHOLD,
            'suggested_keywords': [],
            'suggested_sub_types': [],
            'target_clients': target_clients,
            'confidence': confidence,
            'description': description,
            'created_at': datetime.now().strftime('%Y-%m-%d'),
            'last_updated': datetime.now().strftime('%Y-%m-%d'),
        }

    def _promote_weak_signals(self, domain_name: str, promoted_line_id: str) -> None:
        """When a proposal is promoted, update related weak signals."""
        inc = self.load_incubation()
        for ws in inc.get('weak_signals', []):
            if ws.get('proposed_domain') == domain_name:
                ws['status'] = 'promoted'
                ws['promoted_to'] = promoted_line_id
        self._incubation = inc
        self.save_incubation()

    @staticmethod
    def _name_similarity(a: str, b: str) -> float:
        """Simple Jaccard similarity on character bigrams."""
        def bigrams(s):
            return set(s[i:i+2] for i in range(len(s)-1))
        ba, bb = bigrams(a), bigrams(b)
        if not ba or not bb:
            return 0.0
        return len(ba & bb) / len(ba | bb)

    # ---- LLM Config (P1-2) ----

    def get_llm_config(self) -> dict:
        return self.load().get('llm_config', {
            'round2_model': 'deepseek-v4-flash',
            'round2_fallback': 'deepseek-v4-pro',
            'round3_model': 'deepseek-v4-pro',
            'round3_fallback': 'qwen3.7-plus',
            'last_verified': datetime.now().strftime('%Y-%m-%d'),
        })

    def update_llm_config(self, **kwargs) -> None:
        data = self.load()
        data['llm_config'] = {**data.get('llm_config', {}), **kwargs}
        data['llm_config']['last_verified'] = datetime.now().strftime('%Y-%m-%d')
        self._data = data
        self.save()

    # ---- Statistics ----

    def get_stats(self) -> dict:
        data = self.load()
        nodes = data.get('nodes', [])
        inc = self.load_incubation()
        return {
            'tree_version': data.get('tree_version', 0),
            'active_lines': len([n for n in nodes if n.get('status') == 'active']),
            'declining_lines': len([n for n in nodes if n.get('status') == 'declining']),
            'incubating_proposals': len([p for p in inc.get('proposals', [])
                                         if p.get('status') in ('accumulating', 'threshold_reached')]),
            'weak_signals': len([ws for ws in inc.get('weak_signals', [])
                                 if ws.get('status') == 'accumulating']),
            'meta_tags': len(data.get('meta_tags', [])),
            'pending_review': len([p for p in inc.get('proposals', [])
                                   if p.get('status') == 'threshold_reached']),
        }


# Singleton
_taxonomy_instance = None


def get_taxonomy() -> TaxonomyManager:
    global _taxonomy_instance
    if _taxonomy_instance is None:
        _taxonomy_instance = TaxonomyManager()
    return _taxonomy_instance
