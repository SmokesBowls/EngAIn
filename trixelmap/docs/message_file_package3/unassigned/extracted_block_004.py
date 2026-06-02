    for lid in sorted(locations.keys()):
        loc = locations[lid]
        
        # New Status Logic
        if loc.conflicts:
            status = "⚠️ CONFLICT"
        elif not loc.evidence and loc.files_mentioned:
            status = "⚠️ MENTIONED ONLY (Unresolved)"
        else:
            status = "✅ SPATIAL"

        lines.append(f"### `{lid}` {status} (confidence: {loc.confidence:.2f})")
        lines.append(f"- **Files Mentioned:** {', '.join(loc.files_mentioned)}")
        # ... rest of report generation ...
