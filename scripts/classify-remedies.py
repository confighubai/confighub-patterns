#!/usr/bin/env python3
"""
Bulk CCVE Remedy Classification Script

Parses remediation.commands from CCVEs and infers remedy.type based on patterns.
This enables xBOW (executable Bill of Works) automation.

Usage:
    python3 scripts/classify-remedies.py [--dry-run] [--verbose]
"""

import os
import re
import sys
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Classification patterns: (regex, remedy_type, confidence)
COMMAND_PATTERNS = [
    # Config fixes (automatable)
    (r'kubectl\s+patch', 'config_fix', 'high'),
    (r'kubectl\s+annotate', 'config_fix', 'high'),
    (r'kubectl\s+label', 'config_fix', 'high'),
    (r'kubectl\s+scale', 'config_fix', 'high'),
    (r'kubectl\s+set\s+', 'config_fix', 'high'),
    (r'kubectl\s+edit', 'config_fix', 'medium'),  # Interactive but patchable
    (r'kubectl\s+apply', 'config_fix', 'medium'),  # Apply is usually config fix
    (r'kubectl\s+create', 'config_fix', 'medium'),
    (r'kubectl\s+replace', 'config_fix', 'high'),
    (r'kubectl\s+cordon', 'config_fix', 'high'),
    (r'kubectl\s+uncordon', 'config_fix', 'high'),
    (r'kubectl\s+drain', 'config_fix', 'high'),
    (r'kubectl\s+taint', 'config_fix', 'high'),

    # Trigger actions (automatable)
    (r'flux\s+reconcile', 'trigger_action', 'high'),
    (r'flux\s+resume', 'trigger_action', 'high'),
    (r'flux\s+suspend', 'trigger_action', 'high'),
    (r'argocd\s+app\s+sync', 'trigger_action', 'high'),
    (r'argocd\s+app\s+refresh', 'trigger_action', 'high'),
    (r'kubectl\s+rollout\s+restart', 'trigger_action', 'high'),
    (r'kubectl\s+rollout\s+undo', 'trigger_action', 'high'),
    (r'kubectl\s+rollout\s+resume', 'trigger_action', 'high'),

    # Delete operations (require confirmation)
    (r'kubectl\s+delete', 'delete_resource', 'high'),

    # Upgrades (semi-automatable)
    (r'helm\s+upgrade', 'upgrade', 'high'),
    (r'helm\s+install', 'upgrade', 'medium'),
    (r'helm\s+rollback', 'upgrade', 'high'),  # Rollback is a form of version change
    (r'kubectl\s+apply\s+-f\s+https://', 'upgrade', 'medium'),  # Remote manifests
    (r'linkerd\s+upgrade', 'upgrade', 'high'),
    (r'istioctl\s+upgrade', 'upgrade', 'high'),
    (r'kubeadm\s+upgrade', 'upgrade', 'high'),

    # Restarts
    (r'systemctl\s+restart', 'restart', 'high'),
    (r'service\s+\w+\s+restart', 'restart', 'high'),
    (r'crictl\s+', 'restart', 'medium'),  # Container runtime commands

    # Source fixes (require Git access)
    (r'git\s+', 'source_fix', 'medium'),
    (r'kustomize\s+edit', 'source_fix', 'medium'),

    # External actions (require external system access)
    (r'aws\s+', 'external_action', 'high'),
    (r'gcloud\s+', 'external_action', 'high'),
    (r'az\s+', 'external_action', 'high'),
    (r'vault\s+', 'external_action', 'high'),
    (r'curl\s+', 'external_action', 'medium'),

    # Diagnostic commands - if only these, it's manual investigation
    (r'kubectl\s+describe', 'diagnose_then_fix', 'low'),
    (r'kubectl\s+get', 'diagnose_then_fix', 'low'),
    (r'kubectl\s+logs', 'diagnose_then_fix', 'low'),
    (r'kubectl\s+events', 'diagnose_then_fix', 'low'),
    (r'helm\s+list', 'diagnose_then_fix', 'low'),
    (r'helm\s+history', 'diagnose_then_fix', 'low'),
    (r'helm\s+status', 'diagnose_then_fix', 'low'),
    (r'flux\s+get', 'diagnose_then_fix', 'low'),
    (r'argocd\s+app\s+get', 'diagnose_then_fix', 'low'),
]

# Step-based patterns (when no commands present)
STEP_PATTERNS = [
    # Config fixes
    (r'update.*config', 'config_fix', 'medium'),
    (r'set.*to', 'config_fix', 'medium'),
    (r'change.*value', 'config_fix', 'medium'),
    (r'increase.*timeout', 'config_fix', 'high'),
    (r'add.*annotation', 'config_fix', 'high'),
    (r'remove.*annotation', 'config_fix', 'high'),
    (r'adjust.*setting', 'config_fix', 'medium'),
    (r'configure.*properly', 'config_fix', 'medium'),
    (r'fix.*configuration', 'config_fix', 'high'),
    (r'correct.*value', 'config_fix', 'medium'),
    (r'ensure.*set', 'config_fix', 'medium'),
    (r'verify.*and.*update', 'config_fix', 'medium'),
    (r'modify.*spec', 'config_fix', 'medium'),
    (r'patch.*resource', 'config_fix', 'high'),
    (r'scale.*deployment', 'config_fix', 'high'),
    (r'right.*siz', 'config_fix', 'high'),  # rightsizing

    # Trigger actions
    (r'restart.*deployment', 'trigger_action', 'high'),
    (r'restart.*pod', 'trigger_action', 'high'),
    (r'reconcile', 'trigger_action', 'high'),
    (r'sync.*application', 'trigger_action', 'high'),
    (r'trigger.*sync', 'trigger_action', 'high'),
    (r'force.*refresh', 'trigger_action', 'high'),
    (r'rollback.*release', 'trigger_action', 'high'),

    # Delete/recreate
    (r'delete.*and.*recreate', 'delete_resource', 'medium'),
    (r'remove.*resource', 'delete_resource', 'medium'),
    (r'delete.*pod', 'delete_resource', 'medium'),
    (r'clean.*up', 'delete_resource', 'low'),

    # Upgrades
    (r'upgrade.*version', 'upgrade', 'high'),
    (r'upgrade.*to.*\d', 'upgrade', 'high'),
    (r'update.*helm', 'upgrade', 'medium'),
    (r'rollback.*to.*previous', 'upgrade', 'medium'),

    # Source fixes
    (r'update.*manifest', 'source_fix', 'medium'),
    (r'modify.*git', 'source_fix', 'high'),
    (r'update.*helm.*values', 'source_fix', 'medium'),
    (r'fix.*yaml', 'source_fix', 'medium'),
    (r'correct.*template', 'source_fix', 'medium'),

    # Manual
    (r'contact.*administrator', 'manual_only', 'high'),
    (r'manual.*intervention', 'manual_only', 'high'),
    (r'consult.*documentation', 'diagnose_then_fix', 'low'),
    (r'review.*logs', 'diagnose_then_fix', 'low'),
    (r'check.*status', 'diagnose_then_fix', 'low'),
    (r'identify.*issue', 'diagnose_then_fix', 'low'),
    (r'verify.*correct', 'diagnose_then_fix', 'low'),
]

def classify_ccve(ccve_data: Dict) -> Tuple[Optional[str], str, List[str]]:
    """
    Classify a CCVE's remedy type based on remediation section.

    Returns:
        (remedy_type, confidence, matched_patterns)
    """
    remediation = ccve_data.get('remediation', {})

    # Already classified?
    if ccve_data.get('remedy', {}).get('type'):
        return None, 'already_classified', []

    commands = remediation.get('commands', [])
    steps = remediation.get('steps', [])

    matched_patterns = []
    type_scores = {}

    # Check command patterns
    for cmd in commands:
        if not isinstance(cmd, str):
            continue
        cmd_lower = cmd.lower()
        for pattern, remedy_type, confidence in COMMAND_PATTERNS:
            if re.search(pattern, cmd_lower):
                matched_patterns.append(f"cmd:{pattern}")
                score = 3 if confidence == 'high' else 2 if confidence == 'medium' else 1
                type_scores[remedy_type] = type_scores.get(remedy_type, 0) + score

    # Check step patterns (lower weight)
    for step in steps:
        if not isinstance(step, str):
            continue
        step_lower = step.lower()
        for pattern, remedy_type, confidence in STEP_PATTERNS:
            if re.search(pattern, step_lower):
                matched_patterns.append(f"step:{pattern}")
                score = 2 if confidence == 'high' else 1
                type_scores[remedy_type] = type_scores.get(remedy_type, 0) + score

    if not type_scores:
        return None, 'no_match', []

    # Get highest scoring type
    best_type = max(type_scores, key=type_scores.get)
    best_score = type_scores[best_type]

    # Determine confidence
    if best_score >= 6:
        confidence = 'high'
    elif best_score >= 3:
        confidence = 'medium'
    else:
        confidence = 'low'

    return best_type, confidence, matched_patterns


def add_remedy_block(ccve_data: Dict, remedy_type: str, confidence: str) -> Dict:
    """Add or update remedy block in CCVE data."""
    if 'remedy' not in ccve_data:
        ccve_data['remedy'] = {}

    ccve_data['remedy']['type'] = remedy_type
    ccve_data['remedy']['confidence'] = confidence
    ccve_data['remedy']['auto_classified'] = True

    return ccve_data


def process_ccve_file(filepath: Path, dry_run: bool, verbose: bool) -> Dict:
    """Process a single CCVE file."""
    result = {
        'file': str(filepath),
        'status': None,
        'remedy_type': None,
        'confidence': None,
        'patterns': []
    }

    try:
        with open(filepath, 'r') as f:
            content = f.read()
            ccve_data = yaml.safe_load(content)

        if not ccve_data:
            result['status'] = 'empty_file'
            return result

        remedy_type, confidence, patterns = classify_ccve(ccve_data)

        if confidence == 'already_classified':
            result['status'] = 'already_classified'
            result['remedy_type'] = ccve_data.get('remedy', {}).get('type')
            return result

        if remedy_type is None:
            result['status'] = 'no_match'
            return result

        result['remedy_type'] = remedy_type
        result['confidence'] = confidence
        result['patterns'] = patterns

        if dry_run:
            result['status'] = 'would_update'
        else:
            # Update the file
            ccve_data = add_remedy_block(ccve_data, remedy_type, confidence)

            # Write back preserving format as much as possible
            with open(filepath, 'w') as f:
                yaml.dump(ccve_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            result['status'] = 'updated'

        if verbose:
            print(f"  {filepath.name}: {remedy_type} ({confidence})")
            for p in patterns[:3]:
                print(f"    - {p}")

    except Exception as e:
        result['status'] = 'error'
        result['error'] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(description='Classify CCVE remedies for xBOW')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    parser.add_argument('--path', default='risks', help='Path to CCVE directory')
    args = parser.parse_args()

    ccve_dir = Path(args.path)
    if not ccve_dir.exists():
        print(f"Error: Directory {ccve_dir} not found")
        sys.exit(1)

    ccve_files = list(ccve_dir.glob('CCVE-2025-*.yaml'))
    print(f"Found {len(ccve_files)} CCVE files")

    if args.dry_run:
        print("DRY RUN - no files will be modified\n")

    stats = {
        'total': len(ccve_files),
        'already_classified': 0,
        'updated': 0,
        'would_update': 0,
        'no_match': 0,
        'error': 0,
        'by_type': {}
    }

    for filepath in sorted(ccve_files):
        result = process_ccve_file(filepath, args.dry_run, args.verbose)

        status = result['status']
        if status in stats:
            stats[status] += 1

        if result['remedy_type']:
            rtype = result['remedy_type']
            stats['by_type'][rtype] = stats['by_type'].get(rtype, 0) + 1

    # Print summary
    print("\n" + "="*50)
    print("CLASSIFICATION SUMMARY")
    print("="*50)
    print(f"Total files:        {stats['total']}")
    print(f"Already classified: {stats['already_classified']}")
    print(f"Newly classified:   {stats['updated'] or stats['would_update']}")
    print(f"No match:           {stats['no_match']}")
    print(f"Errors:             {stats['error']}")

    print("\nBy remedy type:")
    for rtype, count in sorted(stats['by_type'].items(), key=lambda x: -x[1]):
        print(f"  {rtype}: {count}")

    # Calculate automation potential
    automatable = stats['by_type'].get('config_fix', 0) + stats['by_type'].get('trigger_action', 0)
    semi_auto = stats['by_type'].get('upgrade', 0) + stats['by_type'].get('delete_resource', 0)
    total_classified = stats['updated'] or stats['would_update']

    if total_classified > 0:
        print(f"\nAutomation potential:")
        print(f"  Fully automatable: {automatable} ({100*automatable/total_classified:.1f}%)")
        print(f"  Semi-automatable:  {semi_auto} ({100*semi_auto/total_classified:.1f}%)")


if __name__ == '__main__':
    main()
