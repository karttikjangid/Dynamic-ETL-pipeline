"""DeepDiff-based schema versioning for Tier-B pipeline."""

from typing import Any, Dict, Optional

from deepdiff import DeepDiff

from core.models import SchemaDiff
from utils.logger import get_logger

logger = get_logger(__name__)


def compare_schemas_with_deepdiff(
    old_schema: Dict[str, Any],
    new_schema: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Compare two Genson schemas using DeepDiff.
    
    Args:
        old_schema: Previous Genson schema
        new_schema: New Genson schema
        
    Returns:
        DeepDiff result as dict, or None if schemas are identical
    """
    diff = DeepDiff(
        old_schema,
        new_schema,
        ignore_order=True,
        report_repetition=True,
        verbose_level=2
    )
    
    if not diff:
        logger.info("Schemas are identical, no diff")
        return None
    
    diff_dict = diff.to_dict()
    logger.info(f"Schema diff detected: {len(diff_dict)} change categories")
    
    return diff_dict


def is_structural_change(diff: Optional[Dict[str, Any]]) -> bool:
    """Determine if a diff represents a structural schema change.
    
    Structural changes require a version bump. Cosmetic changes (like
    reordering, whitespace) do not.
    
    Args:
        diff: DeepDiff result dict
        
    Returns:
        True if structural change detected
    """
    if not diff:
        return False
    
    # Structural change indicators
    structural_keys = [
        'dictionary_item_added',
        'dictionary_item_removed',
        'type_changes',
        'values_changed'  # If types changed
    ]
    
    # Check if any structural keys are present
    for key in structural_keys:
        if key in diff:
            # Special case: values_changed might be cosmetic
            if key == 'values_changed':
                # Check if actual type changes occurred
                changes = diff[key]
                for change_path, change_data in changes.items():
                    if 'new_value' in change_data and 'old_value' in change_data:
                        if type(change_data['new_value']) != type(change_data['old_value']):
                            return True
            else:
                return True
    
    logger.info("Changes detected but not structural (cosmetic only)")
    return False


def convert_deepdiff_to_schema_diff(
    diff: Optional[Dict[str, Any]],
    old_fields: list,
    new_fields: list
) -> SchemaDiff:
    """Convert a DeepDiff result into a SchemaDiff model.
    
    Args:
        diff: DeepDiff result dict
        old_fields: Previous schema fields
        new_fields: New schema fields
        
    Returns:
        SchemaDiff model
    """
    if not diff:
        return SchemaDiff(
            added_fields=[],
            removed_fields=[],
            type_changes={},
            migration_notes="No changes detected"
        )
    
    # Extract added fields
    added_fields = []
    if 'dictionary_item_added' in diff:
        for item in diff['dictionary_item_added']:
            # Extract field name from path like "root['properties']['new_field']"
            field_name = _extract_field_name(item)
            if field_name:
                added_fields.append(field_name)
    
    # Extract removed fields
    removed_fields = []
    if 'dictionary_item_removed' in diff:
        for item in diff['dictionary_item_removed']:
            field_name = _extract_field_name(item)
            if field_name:
                removed_fields.append(field_name)
    
    # Extract type changes
    type_changes = {}
    if 'type_changes' in diff:
        for path, change in diff['type_changes'].items():
            field_name = _extract_field_name(path)
            if field_name:
                type_changes[field_name] = {
                    "old_type": str(change.get('old_type', 'unknown')),
                    "new_type": str(change.get('new_type', 'unknown'))
                }
    
    # Generate migration notes
    migration_notes = _generate_migration_notes(added_fields, removed_fields, type_changes)
    
    return SchemaDiff(
        added_fields=added_fields,
        removed_fields=removed_fields,
        type_changes=type_changes,
        migration_notes=migration_notes
    )


def _extract_field_name(path: str) -> Optional[str]:
    """Extract field name from a DeepDiff path.
    
    Args:
        path: DeepDiff path string like "root['properties']['field_name']"
        
    Returns:
        Field name or None
    """
    import re
    
    # Pattern to match: ['field_name'] or ["field_name"]
    matches = re.findall(r"\['([^']+)'\]", path)
    
    if matches:
        # Look for the field name after 'properties'
        try:
            properties_idx = matches.index('properties')
            if properties_idx + 1 < len(matches):
                return matches[properties_idx + 1]
        except ValueError:
            # 'properties' not in path, return last match
            return matches[-1]
    
    return None


def _generate_migration_notes(
    added: list,
    removed: list,
    type_changes: dict
) -> str:
    """Generate human-readable migration notes.
    
    Args:
        added: List of added field names
        removed: List of removed field names
        type_changes: Dict of type changes
        
    Returns:
        Migration notes string
    """
    notes = []
    
    if added:
        notes.append(f"Added fields: {', '.join(added)}")
    
    if removed:
        notes.append(f"Removed fields: {', '.join(removed)}")
    
    if type_changes:
        for field, change in type_changes.items():
            notes.append(
                f"Type changed for '{field}': {change['old_type']} → {change['new_type']}"
            )
    
    return "; ".join(notes) if notes else "Schema structure unchanged"
