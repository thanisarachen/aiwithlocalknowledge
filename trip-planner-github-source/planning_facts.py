"""Deterministic date and budget arithmetic for a reviewed traveler profile.

The optional profile is local data, not instructions extracted from uploads.
File hashes prevent a reviewed profile from surviving changes to its source files.
"""
import hashlib
import json
from datetime import date, timedelta

import knowledge


def calculated_trip_facts():
    try:
        manifest = json.loads(knowledge.CONTEXT_MANIFEST.read_text())
        profile = manifest.get('reviewed_profile')
        if not isinstance(profile, dict):
            return ''
        for name, digest in profile['source_hashes'].items():
            if '/' in name or '\\' in name or not knowledge.read_index(name):
                return ''
            if hashlib.sha256((knowledge.UPLOAD_DIR / name).read_bytes()).hexdigest() != digest:
                return ''
        start, end = date.fromisoformat(profile['start']), date.fromisoformat(profile['end'])
        if not 0 <= (end - start).days <= 90:
            return ''
        calendar = [(start + timedelta(days=n)).strftime('%d %b %Y = %A')
                    for n in range((end - start).days + 1)]
        budget = profile['budget']
        subtotal = sum(budget['allocations'].values())
        total = subtotal + budget['buffer']
        nights = (date.fromisoformat(profile['checkout']) - date.fromisoformat(profile['checkin'])).days
        room_total = budget['allocations']['Hotel personal share'] * profile['travelers']
        output = {
            'source_files': list(profile['source_hashes']),
            'calendar_computed': calendar,
            'flights_local_times_from_user': profile['flights'],
            'hotel_nights_computed': nights,
            'requirements': profile['requirements'],
            'personal_budget_currency': budget['currency'],
            'personal_allocations': budget['allocations'],
            'personal_subtotal_computed': subtotal,
            'buffer': budget['buffer'],
            'personal_total_including_buffer': total,
            'personal_target': budget['target'],
            'personal_over_target_computed': total - budget['target'],
            'unpriced_exclusions': budget['exclusions'],
            'whole_room_allowance_THB_assuming_equal_shares': room_total,
            'whole_room_average_THB_per_night_assuming_equal_shares': round(room_total / nights, 2),
            'fx_rate': None,
            'hotel_price_quotes': None,
            'notes': profile['notes'],
        }
        if budget.get('separate_purchase'):
            output['separate_purchase'] = budget['separate_purchase']
            output['personal_total_with_separate_purchase_computed'] = total + budget['separate_purchase']['amount']
        return json.dumps(output, ensure_ascii=False, indent=2)
    except (OSError, ValueError, KeyError, TypeError, ZeroDivisionError):
        return ''
