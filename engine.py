"""Project Outlier: safe, auditable research-agent prototype.

Default mode uses synthetic observations. Optional OpenAI API commentary is
only enabled when OUTLIER_USE_AI=1 and OPENAI_API_KEY is configured.
No trading, payments, scraping, or brokerage integrations.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT /  'sample_markets.json'
REPORT = ROOT / 'reports' / 'latest.md'

ROLES = {
    'SCOUT': 'Identify candidate mismatches in paired YES/NO event contracts. Do not claim identical settlement rules without verification.',
    'QUANT': 'Compute gross spread and hypothetical net spread after specified fees; flag non-positive values and missing execution evidence.',
    'SKEPTIC': 'Try to falsify the opportunity: settlement differences, liquidity, slippage, fees, availability, jurisdiction, and operational failure.',
}

def load_observations(path=DATA):
    data = json.loads(path.read_text())
    if not isinstance(data, list):
        raise ValueError('Expected a list of observations')
    for item in data:
        for key in ('event', 'yes_price', 'no_price', 'estimated_fees'):
            if key not in item:
                raise ValueError(f'Missing {key}')
        if not all(0 <= float(item[k]) <= 1 for k in ('yes_price', 'no_price', 'estimated_fees')):
            raise ValueError('Prices and estimated fees must be between 0 and 1')
    return data

def scout(items):
    return sorted(items, key=lambda x: 1 - float(x['yes_price']) - float(x['no_price']), reverse=True)

def quant(item):
    gross = 1 - float(item['yes_price']) - float(item['no_price'])
    net = gross - float(item['estimated_fees'])
    return {'gross_spread': round(gross, 4), 'estimated_net_spread': round(net, 4), 'positive_estimate': net > 0}

def skeptic(item, metrics):
    issues = []
    if not item.get('rules_verified', False):
        issues.append('Settlement equivalence not independently verified')
    if not item.get('executable_quotes_verified', False):
        issues.append('Simultaneous executable quotes and size not verified')
    if not item.get('jurisdiction_verified', False):
        issues.append('Platform eligibility and jurisdiction not verified')
    if not metrics['positive_estimate']:
        issues.append('No positive estimated spread after listed fees')
    issues.append('Slippage, capital lockup, counterparty and tax risks remain')
    return issues

def optional_ai_review(role, payload):
    if os.getenv('OUTLIER_USE_AI') != '1':
        return None
    key = os.getenv('OPENAI_API_KEY')
    if not key:
        return 'AI review skipped: OPENAI_API_KEY missing.'
    model = os.getenv('OUTLIER_MODEL', 'gpt-4.1-mini')
    body = json.dumps({
        'model': model,
        'input': [
            {'role': 'developer', 'content': ROLES[role] + ' Research only. No trade recommendations or execution. Be skeptical and concise.'},
            {'role': 'user', 'content': json.dumps(payload)},
        ],
        'max_output_tokens': 300,
    }).encode()
    request = urllib.request.Request('https://api.openai.com/v1/responses', data=body,
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'}, method='POST')
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            result = json.load(response)
        return ' '.join(c.get('text', '') for out in result.get('output', [])
                        for c in out.get('content', []) if c.get('type') == 'output_text') or 'No textual output.'
    except Exception as exc:
        return 'AI review unavailable: ' + type(exc).__name__

def run():
    observations = scout(load_observations())
    lines = ['# Outlier Engine | Research Report', '',
             f"Generated (UTC): {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}", '',
             '**Mode:** Synthetic demonstration. Not live prices, executable quotes, or investment advice.', '',
             '## Agent assignments', '']
    for role, task in ROLES.items():
        lines.append(f'- **{role}:** {task}')
    lines.extend(['', '## Candidate observations', ''])
    for item in observations:
        metrics = quant(item)
        issues = skeptic(item, metrics)
        lines += [f"### {item['event']}", '',
                  f"- YES: ${item['yes_price']:.2f}; NO: ${item['no_price']:.2f}; estimated fees: ${item['estimated_fees']:.2f}",
                  f"- Gross spread: {metrics['gross_spread']:.2%}; estimated net spread: {metrics['estimated_net_spread']:.2%}",
                  '- **Status: RESEARCH ONLY. NOT CLEARED FOR EXECUTION.**',
                  '- Skeptic findings:']
        lines += [f'  - {issue}' for issue in issues]
        lines.append('')
    for role in ROLES:
        response = optional_ai_review(role, {'observations': observations[:3], 'mode': 'synthetic'})
        if response:
            lines.extend([f'## {role} AI commentary', '', response, ''])
    lines.extend(['## Gate to live-data research', '',
                  'Require authenticated data provenance, timestamped executable quotes, matched settlement rules, fee schedules, order-book depth, platform eligibility, and independent out-of-sample testing.', ''])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines))
    print(f'Wrote {REPORT}')

if __name__ == '__main__':
    run()
