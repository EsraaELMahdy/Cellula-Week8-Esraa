"""Run no-account verification only. This script never calls terraform apply."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

parser = argparse.ArgumentParser()
parser.add_argument('--terraform', default='terraform')
args = parser.parse_args()
root = Path(__file__).resolve().parent
evidence = root / 'evidence'
evidence.mkdir(exist_ok=True)
commands = [
    ['version', '-json'], ['fmt', '-check', '-recursive'],
    ['init', '-backend=false', '-input=false', '-no-color'],
    ['validate', '-no-color'],
    ['plan', '-refresh=false', '-input=false', '-no-color', '-var=offline_plan=true'],
    ['test', '-no-color'],
]
summary = {'timestamp_utc': datetime.now(timezone.utc).isoformat(), 'cloud_resources_created': False,
           'plan_kind': 'standalone AWS-provider empty-state plan with credential/API discovery disabled', 'commands': []}
for index, command in enumerate(commands):
    result = subprocess.run([args.terraform, *command], cwd=root, text=True, capture_output=True, encoding='utf-8', errors='replace')
    name = f'{index:02d}_{command[0]}.txt'
    (evidence / name).write_text('$ terraform ' + ' '.join(command) + '\n\n' + result.stdout + result.stderr + f'\nExit code: {result.returncode}\n', encoding='utf-8')
    summary['commands'].append({'command': ['terraform', *command], 'exit_code': result.returncode, 'log': name})
    print(command[0], result.returncode, flush=True)
    if result.returncode:
        (evidence / 'verification.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
        raise SystemExit(result.returncode)
(evidence / 'verification.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
