#!/usr/bin/env python3
"""
Debug script to test what the terminal is actually sending
"""

print("Terminal Input Debug Test")
print("=" * 60)
print("Type '2' and press Enter:")
print("=" * 60)

user_input = input(">>> ")

print(f"\nReceived input:")
print(f"  Raw repr: {repr(user_input)}")
print(f"  Length: {len(user_input)}")
print(f"  Bytes: {user_input.encode('utf-8')}")
print(f"  Stripped: {repr(user_input.strip())}")
print(f"  Is '2'? {user_input.strip() == '2'}")
print(f"  In ['1','2','3','4']? {user_input.strip() in ['1','2','3','4']}")

# Check each character
print(f"\nCharacter analysis:")
for i, char in enumerate(user_input):
    print(f"  [{i}] = {repr(char)} (ord: {ord(char)})")

# Try extracting first digit
print(f"\nFirst digit extraction:")
for char in user_input:
    if char in '1234':
        print(f"  Found: {char}")
        break
else:
    print("  No digit found!")
