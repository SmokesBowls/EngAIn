            # ... existing spatial facts logic ...

            # PASS B: Extract all location mentions (even without relations)
            mentions = extract_location_mentions(text)
            for raw_mention in mentions:
                canon_id = resolve_canonical_id(raw_mention)
                if canon_id not in self.locations:
                    self.locations[canon_id] = LocationRecord(canonical_id=canon_id)
                
                loc = self.locations[canon_id]
                # Track file presence
                if source_file.name not in loc.files_mentioned:
                    loc.files_mentioned.append(source_file.name)
                
                # Track alias
                if raw_mention not in loc.aliases:
                    loc.aliases.append(raw_mention)
