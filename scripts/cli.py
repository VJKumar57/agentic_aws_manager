#!/usr/bin/env python3
import argparse
import requests
import sys

DEFAULT_BASE = 'http://localhost:8000'

def plan_s3(base: str, bucket_name: str):
    prompt = f"Create an S3 bucket named {bucket_name} (for demo)."
    resp = requests.post(f"{base}/plan", json={"prompt": prompt})
    resp.raise_for_status()
    data = resp.json()
    print('Proposal created:')
    print(data)

def list_proposals(base: str):
    resp = requests.get(f"{base}/proposals")
    resp.raise_for_status()
    for p in resp.json():
        print(p)

def approve(base: str, pid: str, dry_run: bool = True):
    resp = requests.post(f"{base}/approve/{pid}", json={"dry_run": dry_run})
    resp.raise_for_status()
    print(resp.json())

def audits(base: str):
    resp = requests.get(f"{base}/audits")
    resp.raise_for_status()
    for a in resp.json():
        print(a)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', default=DEFAULT_BASE)
    sub = p.add_subparsers(dest='cmd')
    ps = sub.add_parser('plan-s3')
    ps.add_argument('bucket')
    sub.add_parser('list-proposals')
    ap = sub.add_parser('approve')
    ap.add_argument('proposal_id')
    ap.add_argument('--no-dry', dest='dry', action='store_false', help='Execute for real')
    sub.add_parser('audits')
    args = p.parse_args()
    base = args.base
    try:
        if args.cmd == 'plan-s3':
            plan_s3(base, args.bucket)
        elif args.cmd == 'list-proposals':
            list_proposals(base)
        elif args.cmd == 'approve':
            approve(base, args.proposal_id, dry_run=args.dry)
        elif args.cmd == 'audits':
            audits(base)
        else:
            p.print_help()
    except requests.HTTPError as e:
        print('HTTP error:', e, file=sys.stderr)
        print(e.response.text if e.response is not None else '', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
