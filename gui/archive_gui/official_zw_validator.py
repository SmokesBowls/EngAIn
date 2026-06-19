"""
ZW Validator - Enforces ZW_SPEC.md rules
"""

class ZWValidationError(Exception):
    """Raised when ZW content violates specification"""
    pass

class ZWValidator:
    """
    Validates ZW structures against the specification.
    Based on ZW_SPEC.md v0.1
    """
    
    def __init__(self, strict=False, max_depth=20):
        self.strict = strict
        self.max_depth = max_depth
        self.errors = []
        self.warnings = []
    
    def validate(self, parsed_zw, zw_type=None):
        """
        Validate a parsed ZW structure
        
        Args:
            parsed_zw: Python dict/list from parse_zw()
            zw_type: Optional type hint ('object', 'container', 'scene', etc.)
        
        Returns:
            bool: True if valid, False otherwise
        
        Raises:
            ZWValidationError: If strict=True and validation fails
        """
        self.errors = []
        self.warnings = []
        
        # Structure validation
        self._validate_structure(parsed_zw, depth=0)
        
        # Type-specific validation
        if zw_type:
            self._validate_type(parsed_zw, zw_type)
        
        # Check for errors
        if self.errors:
            if self.strict:
                raise ZWValidationError(f"Validation failed: {', '.join(self.errors)}")
            return False
        
        return True
    
    def _validate_structure(self, obj, depth=0):
        """Recursively validate structure and depth"""
        
        # Depth check (§6.3)
        if depth > self.max_depth:
            self.errors.append(f"Max depth {self.max_depth} exceeded")
            return
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Validate key format
                if not self._is_valid_key(key):
                    self.errors.append(f"Invalid key format: '{key}'")
                
                # Recurse into value
                self._validate_structure(value, depth + 1)
        
        elif isinstance(obj, list):
            for item in obj:
                self._validate_structure(item, depth + 1)
    
    def _is_valid_key(self, key):
        """
        Check if key is valid bareword
        - No whitespace
        - No special characters {}[]"
        """
        if not isinstance(key, str):
            return False
        if not key:
            return False
        if any(c in key for c in ' \t\n{}[]"'):
            return False
        return True
    
    def _validate_type(self, obj, expected_type):
        """Validate type-specific requirements (§6.2)"""
        
        if not isinstance(obj, dict):
            self.errors.append(f"Expected dict for type '{expected_type}', got {type(obj)}")
            return
        
        # Get the actual object data (might be wrapped in type key)
        data = obj.get(expected_type, obj)
        
        if expected_type == 'object':
            self._validate_object(data)
        elif expected_type == 'container':
            self._validate_container(data)
        elif expected_type == 'scene':
            self._validate_scene(data)
    
    def _validate_object(self, obj):
        """Validate object type requirements"""
        required = ['type', 'id', 'description']
        
        for field in required:
            if field not in obj:
                self.errors.append(f"Object missing required field: '{field}'")
        
        # Type field should be 'object'
        if 'type' in obj and obj['type'] != 'object':
            self.warnings.append(f"Object type is '{obj['type']}', expected 'object'")
    
    def _validate_container(self, obj):
        """Validate container type requirements"""
        required = ['type', 'id', 'contents']
        
        for field in required:
            if field not in obj:
                self.errors.append(f"Container missing required field: '{field}'")
        
        # Contents should be a list or dict
        if 'contents' in obj:
            if not isinstance(obj['contents'], (list, dict)):
                self.errors.append("Container 'contents' must be array or object")
    
    def _validate_scene(self, obj):
        """Validate scene type requirements"""
        required = ['id', 'description']
        
        for field in required:
            if field not in obj:
                self.errors.append(f"Scene missing required field: '{field}'")
    
    def get_report(self):
        """Get validation report"""
        report = []
        
        if self.errors:
            report.append("ERRORS:")
            for error in self.errors:
                report.append(f"  ❌ {error}")
        
        if self.warnings:
            report.append("WARNINGS:")
            for warning in self.warnings:
                report.append(f"  ⚠️  {warning}")
        
        if not self.errors and not self.warnings:
            report.append("✅ Validation passed")
        
        return "\n".join(report)


def validate_zw_file(filepath, zw_type=None, strict=False):
    """
    Convenience function to validate a ZW file
    
    Args:
        filepath: Path to .zw or .zonj.json file
        zw_type: Optional type hint
        strict: Raise exception on validation failure
    
    Returns:
        tuple: (is_valid, validator)
    """
    from core.zw_core import parse_zw
    import json
    
    # Read file
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse based on extension
    if filepath.endswith('.json'):
        parsed = json.loads(content)
    else:
        parsed = parse_zw(content)
    
    # Validate
    validator = ZWValidator(strict=strict)
    is_valid = validator.validate(parsed, zw_type)
    
    return is_valid, validator


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python zw_validator.py <file.zw> [type]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    zw_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        is_valid, validator = validate_zw_file(filepath, zw_type, strict=False)
        print(validator.get_report())
        sys.exit(0 if is_valid else 1)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
