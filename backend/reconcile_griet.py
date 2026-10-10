#!/usr/bin/env python3
"""Reconcile normalized UPI JSON payloads with a Sheets webhook (stdlib only)."""
import argparse
import csv
import json
import os
import re
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse

UTR = re.compile(r"[0-9]{12}\Z")
SUCCESS = {"success", "successful", "captured", "paid"}

def money(value):
    if isinstance(value, bool):
        raise ValueError("Invalid amount")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid amount") from exc
    if not result.is_finite() or result <= 0 or result != result.quantize(Decimal('0.01')):
        raise ValueError("Amount must be positive with at most two decimal places")
    return result

def text(value):
    return str(value).strip() if value is not None else ""

def parse_payment(raw):
    if not isinstance(raw, dict):
        raise ValueError("Payload must be an object")
    # Configure upstream normalization for provider-specific nested payloads.
    utr = raw.get('utr', raw.get('transaction_id', raw.get('UTR')))
    # Do not coerce numeric IDs: leading zeros may already have been lost.
    if not isinstance(utr, str) or not UTR.fullmatch(utr):
        raise ValueError("UTR/Transaction ID must be a string containing exactly 12 ASCII digits")
    rid = text(raw.get('registration_id'))
    if not rid:
        raise ValueError("registration_id is required")
    return dict(registration_id=rid, utr=utr, amount=money(raw.get('amount')),
                currency=text(raw.get('currency', 'INR')).upper(),
                status=text(raw.get('status')).lower(), event=text(raw.get('event')))

class Webhook:
    def __init__(self, url, token, timeout=30):
        if urlparse(url).scheme != 'https':
            raise ValueError('Webhook URL must use HTTPS')
        self.url, self.token, self.timeout = url, token, timeout

    def call(self, action, **kwargs):
        # Body token supports Apps Script; never put credentials in query strings.
        body = json.dumps(dict(action=action, token=self.token, **kwargs)).encode()
        request = Request(self.url, data=body, headers={'Content-Type': 'application/json'}, method='POST')
        with urlopen(request, timeout=self.timeout) as response:
            result = json.load(response)
        if not isinstance(result, dict) or result.get('ok') is not True:
            raise RuntimeError('Webhook rejected request: ' + str(result.get('error', 'unknown')))
        return result

    def registrations(self):
        rows = self.call('list_registrations').get('registrations')
        if not isinstance(rows, list):
            raise ValueError('Webhook must return a registrations array')
        required = {'registration_id', 'event', 'branch', 'expected_amount', 'payment_status', 'utr', 'paid_amount'}
        ids = set()
        for row in rows:
            if not isinstance(row, dict) or not required <= row.keys():
                raise ValueError('Registration row missing required columns')
            rid = text(row['registration_id'])
            if not rid or rid in ids:
                raise ValueError('Registration IDs must be nonempty and unique')
            ids.add(rid)
            row['registration_id'] = rid
            money(row['expected_amount'])
            if text(row['payment_status']).lower() == 'verified':
                if not isinstance(row['utr'], str) or not UTR.fullmatch(row['utr']):
                    raise ValueError('Verified row has invalid UTR')
                money(row['paid_amount'])
        verified_utrs = [r['utr'] for r in rows if text(r['payment_status']).lower() == 'verified']
        if len(verified_utrs) != len(set(verified_utrs)):
            raise ValueError('Duplicate verified UTRs in sheet; resolve before reporting')
        return rows

def reconcile(payments, rows, webhook, trusted=False, dry_run=False):
    by_id = {r['registration_id']: r for r in rows}
    used = {r['utr']: r['registration_id'] for r in rows if text(r['payment_status']).lower() == 'verified'}
    # Includes unverified claims to prevent re-use of the same reference.
    claims = defaultdict(set)
    for r in rows:
        if isinstance(r['utr'], str) and UTR.fullmatch(r['utr']):
            claims[r['utr']].add(r['registration_id'])
    for raw in payments:
        if isinstance(raw, dict):
            u = raw.get('utr', raw.get('transaction_id', raw.get('UTR')))
            if isinstance(u, str) and UTR.fullmatch(u):
                claims[u].add(text(raw.get('registration_id')))
    results = []
    for index, raw in enumerate(payments, 1):
        rid = text(raw.get('registration_id')) if isinstance(raw, dict) else ''
        try:
            payment = parse_payment(raw)
            rid, utr = payment['registration_id'], payment['utr']
            row = by_id.get(rid)
            if row is None:
                raise ValueError('Unknown registration_id')
            if payment['currency'] != 'INR':
                raise ValueError('Currency must be INR')
            if payment['event'] and payment['event'] != text(row['event']):
                raise ValueError('Event mismatch')
            if payment['amount'] != money(row['expected_amount']):
                raise ValueError('Amount mismatch')
            if len(claims[utr]) > 1 or (utr in used and used[utr] != rid):
                raise ValueError('UTR claimed by multiple registrations')
            if text(row['payment_status']).lower() == 'verified':
                if row['utr'] != utr or money(row['paid_amount']) != payment['amount']:
                    raise ValueError('Registration already verified with different payment')
                outcome = 'already_verified'
            elif payment['status'] not in SUCCESS:
                outcome = 'pending_provider_confirmation'
            elif not trusted:
                outcome = 'pending_authenticity_verification'
            elif dry_run:
                outcome = 'would_verify'
            else:
                response = webhook.call('verify_payment', registration_id=rid, utr=utr,
                                        paid_amount=str(payment['amount']), currency='INR',
                                        expected_amount=str(payment['amount']))
                if response.get('status') not in {'verified', 'already_verified'}:
                    raise RuntimeError('Webhook did not confirm verification')
                row.update(payment_status='verified', utr=utr, paid_amount=str(payment['amount']))
                used[utr] = rid
                outcome = response['status']
            results.append(dict(index=index, registration_id=rid, outcome=outcome, reason=''))
        except ValueError as exc:
            results.append(dict(index=index, registration_id=rid, outcome='needs_review', reason=str(exc)))
        # Network/API errors deliberately stop the run: don't pretend an update succeeded.
    return results

def summary(rows, outcomes):
    revenue = defaultdict(lambda: Decimal('0'))
    counts = Counter()
    pending = []
    for r in rows:
        event, branch = text(r['event']), text(r['branch']) or 'Unknown'
        counts[(event, branch)] += 1
        revenue[event] += Decimal('0')
        if text(r['payment_status']).lower() == 'verified':
            revenue[event] += money(r['paid_amount'])
        else:
            pending.append(dict(registration_id=r['registration_id'], event=event, branch=branch,
                                payment_status=r['payment_status']))
    return dict(currency='INR', total_verified_revenue=str(sum(revenue.values(), Decimal('0')).quantize(Decimal('.01'))),
                revenue_per_event={k: str(v.quantize(Decimal('.01'))) for k, v in sorted(revenue.items())},
                branch_registration_counts=[dict(event=e, branch=b, count=n) for (e,b),n in sorted(counts.items())],
                pending_payment_verifications=len(pending), pending_registrations=pending,
                payload_outcomes=dict(Counter(r['outcome'] for r in outcomes)))

def load_payments(path):
    content = Path(path).read_text(encoding='utf-8')
    if path.endswith('.jsonl'):
        return [json.loads(line) for line in content.splitlines() if line.strip()]
    data = json.loads(content)
    if isinstance(data, dict) and 'payments' in data:
        data = data['payments']
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError('Input must be a payment, array, or {"payments": [...]}')
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payments', required=True, help='JSON or JSONL input')
    parser.add_argument('--output-dir', default='reconciliation_output')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--trusted-source', action='store_true',
                        help='ONLY for bank/provider-confirmed data authenticated upstream')
    args = parser.parse_args()
    api = Webhook(os.environ['GRIET_WEBHOOK_URL'], os.environ['GRIET_WEBHOOK_TOKEN'])
    rows = api.registrations()
    outcomes = reconcile(load_payments(args.payments), rows, api, args.trusted_source, args.dry_run)
    if not args.dry_run:
        rows = api.registrations()  # Re-read authoritative state, including concurrent updates.
    report = summary(rows, outcomes)
    report['dry_run'] = args.dry_run
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out/'summary.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    with (out/'payment_audit.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'registration_id', 'outcome', 'reason'])
        writer.writeheader()
        # Prevent spreadsheet formula injection when opening an audit CSV.
        writer.writerows({k: "'"+v if isinstance(v,str) and v.startswith(('=', '+', '-', '@')) else v
                          for k,v in r.items()} for r in outcomes)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
