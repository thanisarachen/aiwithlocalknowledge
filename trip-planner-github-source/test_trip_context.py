"""Focused regression checks using fictional traveler fixtures."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import knowledge
import app as planner
from planning_facts import calculated_trip_facts


class TripContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.uploads = self.root / 'uploads'
        self.indexes = self.root / 'index'
        self.uploads.mkdir()
        self.indexes.mkdir()
        self.manifest = self.root / 'trip_context.json'
        self.patches = [patch.object(knowledge, 'UPLOAD_DIR', self.uploads),
                        patch.object(knowledge, 'INDEX_DIR', self.indexes),
                        patch.object(knowledge, 'CONTEXT_MANIFEST', self.manifest),
                        patch.object(planner, 'UPLOAD_DIR', self.uploads)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def put(self, name, text):
        raw = text.encode()
        (self.uploads/name).write_bytes(raw)
        (self.indexes/(name+'.json')).write_text(json.dumps({
            'name': name, 'size': len(raw), 'model': knowledge.EMBED_MODEL,
            'sha256': hashlib.sha256(raw).hexdigest(),
            'chunks': [{'text': text, 'page': None, 'vector': [1.0]}]}))

    def test_complete_brief_and_all_categories_survive_broad_request(self):
        self.put('trip.txt', 'EX100 12:00 NRT; two travelers; 1 room 1 bed; slow pace')
        self.put('budget.txt', '60,000 THB per person; hotel 12,000 personal share')
        refs = ['hotels.md', 'transport.md', 'food.md', 'shopping.md', 'activities.md']
        for name in refs:
            self.put(name, '# Reference\n\n## Place\nFacts, caveat and https://example.org/source')
        self.manifest.write_text(json.dumps({'profiles':['trip.txt','budget.txt'], 'references':refs}))
        result = knowledge.trip_collection_context()
        self.assertEqual({m['name'] for m in result['matches']}, set(refs+['trip.txt','budget.txt']))
        self.assertFalse(result['truncated'])
        self.assertIn('12:00', result['matches'][0]['text'])

    def test_deleted_changed_and_outside_files_are_not_used(self):
        self.put('valid.txt', 'AAAA')
        (self.uploads/'valid.txt').write_text('BBBB')  # same size, stale index
        (self.root/'secret.txt').write_text('Never include')
        self.manifest.write_text(json.dumps({'profiles':['valid.txt','missing.txt','../secret.txt'],'references':[]}))
        self.assertEqual(knowledge.trip_collection_context()['matches'], [])

    def test_card_keeps_source_and_caveat_and_budget_is_bounded(self):
        card = '## [H01] Hotel\n' + 'Location facts. ' * 70 + '\nRate UNKNOWN. Source: https://example.org/hotel'
        chunks = knowledge.chunk_segments(knowledge.extract_segments(card.encode(), '.md'))
        self.assertEqual(len(chunks), 1)
        self.assertIn('Rate UNKNOWN', chunks[0]['text'])
        self.assertIn('https://example.org/hotel', chunks[0]['text'])
        self.put('hotel.md', card)
        self.manifest.write_text(json.dumps({'profiles':[], 'references':['hotel.md']}))
        result = knowledge.trip_collection_context(max_chars=100)
        self.assertTrue(result['truncated'])
        self.assertLessEqual(sum(len(m['text']) for m in result['matches']), 100)

    def test_revision_accepts_long_prior_plan_and_preserves_context(self):
        self.put('trip.txt', 'EX100 12:00 NRT; 7 hotel nights')
        self.manifest.write_text(json.dumps({'profiles':['trip.txt'], 'references':[]}))
        captured = {}
        def respond(endpoint, body, **kwargs):
            captured.update(body)
            return {'message':{'content':'Revised proposal; no booking made.'}}
        with patch.object(planner, 'ollama_post', side_effect=respond):
            response = planner.app.test_client().post('/api/chat', json={'messages':[
                {'role':'user','content':'Make a full plan'},
                {'role':'assistant','content':'Prior day-by-day plan. '*500},
                {'role':'user','content':'Make it cheaper while keeping the flights.'}]})
        self.assertEqual(response.status_code, 200)
        self.assertIn('12:00', '\n'.join(m['content'] for m in captured['messages']))
        self.assertIn('Prior day-by-day plan.', '\n'.join(m['content'] for m in captured['messages']))
        self.assertIn('Live web search is OFF', captured['messages'][0]['content'])
        self.assertEqual(captured['messages'][-1]['role'], 'user')
        self.assertGreaterEqual(captured['options']['num_ctx'], 24000)

    def test_budget_and_calendar_are_calculated_with_explicit_units(self):
        self.put('budget.txt', 'Reviewed traveler budget')
        digest = hashlib.sha256((self.uploads/'budget.txt').read_bytes()).hexdigest()
        profile = {
            'source_hashes': {'budget.txt': digest},
            'start': '2026-12-08', 'end': '2026-12-16',
            'checkin': '2026-12-09', 'checkout': '2026-12-16', 'travelers': 2,
            'flights': ['EX100 12:00 NRT'], 'requirements': ['1 room, 1 bed'], 'notes': [],
            'budget': {'currency': 'THB', 'target': 60000, 'buffer': 8000,
                       'allocations': {'Hotel personal share': 12000, 'Other allocations': 44000},
                       'exclusions':['Insurance']}}
        self.manifest.write_text(json.dumps({'reviewed_profile': profile}))
        data = json.loads(calculated_trip_facts())
        self.assertEqual(data['calendar_computed'][0], '08 Dec 2026 = Tuesday')
        self.assertEqual(data['hotel_nights_computed'], 7)
        self.assertEqual(data['personal_total_including_buffer'], 64000)
        self.assertNotIn('separate_purchase', data)
        self.assertNotIn('personal_total_with_separate_purchase_computed', data)
        self.assertEqual(data['whole_room_allowance_THB_assuming_equal_shares'], 24000)
        self.assertEqual(data['personal_over_target_computed'], 4000)
        self.assertIsNone(data['fx_rate'])
        self.assertIsNone(data['hotel_price_quotes'])
        (self.uploads/'budget.txt').unlink()
        self.assertEqual(calculated_trip_facts(), '')

if __name__ == '__main__':
    unittest.main()
