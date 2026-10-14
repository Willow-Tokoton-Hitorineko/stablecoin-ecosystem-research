"""Evidence-led classification and relation integrity, using synthetic records only."""
from __future__ import annotations
import argparse
import json
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

LABELS = {'issuer', 'payment', 'exchange', 'custody', 'infrastructure', 'compliance', 'asset_management'}

def analyze(dataset: dict) -> dict:
    companies = dataset['companies']
    deals = dataset['deals']
    by_id = {}
    review = []
    for row in companies:
        cid = row['id']
        if cid in by_id:
            raise ValueError(f'Duplicate company id: {cid}')
        if not isinstance(row.get('stablecoin_business'), bool):
            raise ValueError('stablecoin_business must be an explicit boolean')
        labels = row.get('labels', [])
        if not isinstance(labels, list) or len(set(labels)) != len(labels) or not set(labels) <= LABELS:
            raise ValueError('Invalid or duplicate value-chain labels')
        evidence = row.get('evidence', '').strip()
        eligible = row['stablecoin_business'] and bool(evidence) and bool(labels)
        by_id[cid] = {**row, 'eligible': eligible}
        if row['stablecoin_business'] and not eligible:
            review.append(cid)
    seen = set()
    selected = []
    unknown_amounts = 0
    currency_totals = Counter()
    for deal in deals:
        if deal['id'] in seen:
            raise ValueError('Duplicate deal id')
        seen.add(deal['id'])
        if deal['company_id'] not in by_id:
            raise ValueError('Deal references unknown company')
        if not by_id[deal['company_id']]['eligible']:
            continue
        selected.append(deal)
        if deal.get('amount') is None:
            unknown_amounts += 1
            continue
        try:
            amount = Decimal(str(deal['amount']))
        except InvalidOperation as exc:
            raise ValueError('Invalid deal amount') from exc
        if not amount.is_finite() or amount < 0:
            raise ValueError('Amount must be finite and nonnegative')
        currency = deal.get('currency')
        if not isinstance(currency, str) or len(currency) != 3 or not currency.isalpha() or not currency.isupper():
            raise ValueError('Explicit uppercase three-letter currency required')
        currency_totals[currency] += amount
    eligible_rows = [x for x in by_id.values() if x['eligible']]
    labels = Counter(label for x in eligible_rows for label in x['labels'])
    return {
        'data_kind': dataset.get('data_kind', 'user-provided, rights not verified'),
        'candidate_companies': len(companies),
        'eligible_companies': len(eligible_rows),
        'excluded_or_pending': len(companies) - len(eligible_rows),
        'pending_review_ids': review,
        'value_chain_label_counts': dict(sorted(labels.items())),
        'eligible_deals': len(selected),
        'missing_amount_deals': unknown_amounts,
        'reported_amount_by_currency': {k: str(v) for k, v in sorted(currency_totals.items())},
        'notes': ['Labels overlap; label counts are not company shares.',
                  'Missing amounts remain unknown; totals cover disclosed amounts only.',
                  'Currency totals are not converted or pooled.',
                  'Business qualification is supplied and reviewed, never inferred from broad crypto keywords.'],
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, default=Path(__file__).parent / 'samples' / 'synthetic.json')
    args = parser.parse_args()
    print(json.dumps(analyze(json.loads(args.input.read_text(encoding='utf-8'))), indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
