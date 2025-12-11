# zw.py
import argparse
import json
import os
from official_zw_validator import ZWValidator, ZWValidationError

def validate_zw_file(path, zw_type=None, strict=False):
    validator = ZWValidator(strict=strict)
    ok = validator.validate_zw_file(path, zw_type=zw_type)
    report = validator.get_report()
    for issue in report:
        print(f"[{issue['level'].upper()}] {issue['message']}")
    return ok

def print_summary(path):
    with open(path, 'r') as f:
        data = json.load(f)
    print(f"--- {path} ---")
    print(f"Type: {data.get('type', 'unknown')}")
    print(f"ID: {data.get('id', 'unnamed')}")
    print(f"Keys: {list(data.keys())}")
    print(f"Chars: {len(json.dumps(data))}")
    print(f"Keys/Values: {len(data)}")

def main():
    parser = argparse.ArgumentParser(description="ZW CLI Tool")
    subparsers = parser.add_subparsers(dest='command', help="Available commands")

    # Validate
    validate_parser = subparsers.add_parser("validate", help="Validate a .zw file")
    validate_parser.add_argument("file", help="Path to the .zw file")
    validate_parser.add_argument("--type", help="ZW block type (object, scene, etc.)")
    validate_parser.add_argument("--strict", action="store_true", help="Fail on any error")

    # Summary
    summary_parser = subparsers.add_parser("summary", help="Quick summary of a .zw file")
    summary_parser.add_argument("file", help="Path to the .zw file")

    args = parser.parse_args()

    if args.command == "validate":
        validate_zw_file(args.file, zw_type=args.type, strict=args.strict)

    elif args.command == "summary":
        print_summary(args.file)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
