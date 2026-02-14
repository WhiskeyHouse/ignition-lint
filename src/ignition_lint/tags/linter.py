"""Ignition Tag/UDT JSON Linter.

Validates tag JSON structures against the tag schema and checks for
best-practice violations such as missing dataType, missing typeId on
UDT instances, misconfigured value sources, and unknown property names.
"""

import json
import re
from pathlib import Path

try:
    from jsonschema import ValidationError, validate

    JSONSCHEMA_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    validate = None  # type: ignore[var-annotated]
    JSONSCHEMA_AVAILABLE = False

    class ValidationError(Exception):  # type: ignore[no-redef]
        """Fallback error when jsonschema is unavailable."""

        pass


from ..reporting import LintIssue, LintSeverity
from ..schemas import tag_schema_path_for as _tag_schema_path_for
from ..validators.jython import JythonValidator

# Keys that are present on every tagType (shared base)
_SHARED_TAG_KEYS = frozenset(
    {
        "name",
        "tagType",
        "documentation",
        "enabled",
        "tooltip",
        "tags",
        "tagGroup",
    }
)


class IgnitionTagLinter:
    """Lint Ignition tag/UDT JSON files for structural and best-practice issues."""

    def __init__(self, schema_path: str | None = None):
        if schema_path is None:
            schema_path = _tag_schema_path_for("robust")
        else:
            schema_path = Path(schema_path)

        self.schema_path = schema_path
        self.jsonschema_available = JSONSCHEMA_AVAILABLE and validate is not None
        self.schema = self._load_schema(schema_path)
        self.issues: list[LintIssue] = []
        self.tag_stats = {
            "total_files": 0,
            "total_tags": 0,
            "valid_tags": 0,
            "invalid_tags": 0,
            "tag_types": set(),
        }
        self.jython_validator = JythonValidator()
        self.known_atomic_props = self._extract_known_atomic_props()

    # ------------------------------------------------------------------
    # Schema loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_schema(schema_path: str | Path) -> dict:
        try:
            with open(schema_path) as f:
                return json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Tag schema file not found: {schema_path}") from e
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in tag schema file: {schema_path}: {e}"
            ) from e

    def _extract_known_atomic_props(self) -> frozenset:
        """Extract known AtomicTag property names from the loaded schema."""
        props: set[str] = set()
        try:
            atomic_def = self.schema.get("definitions", {}).get("atomicTagProps", {})
            schema_props = atomic_def.get("properties", {})
            props.update(schema_props.keys())
        except (AttributeError, TypeError):
            pass

        if not props:
            # Minimal fallback
            props = {
                "name",
                "tagType",
                "dataType",
                "valueSource",
                "value",
                "enabled",
                "documentation",
                "tooltip",
                "tagGroup",
            }

        return frozenset(props)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def lint_file(self, file_path: str) -> bool:
        """Lint a single tag JSON file. Returns True if the file is valid."""
        self.tag_stats["total_files"] += 1

        try:
            with open(file_path, encoding="utf-8") as f:
                raw_text = f.read()
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            self.issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="INVALID_JSON",
                    message=f"Invalid JSON format: {e}",
                    file_path=file_path,
                    component_path="file",
                    component_type="tag",
                    suggestion=f"Line {e.lineno}: {e.msg}",
                )
            )
            return False
        except Exception as e:
            self.issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="FILE_READ_ERROR",
                    message=f"Could not read file: {e}",
                    file_path=file_path,
                    component_path="file",
                    component_type="tag",
                )
            )
            return False

        line_map = self._build_tag_line_map(raw_text)
        issues_start = len(self.issues)

        # Walk the tag tree
        if isinstance(data, list):
            # Handle top-level arrays (common in tag exports)
            file_valid = True
            for i, entry in enumerate(data):
                if not self._validate_tag_node(entry, file_path, f"[{i}]"):
                    file_valid = False
        else:
            # Single tag node
            file_valid = self._validate_tag_node(data, file_path, "")

        # Enrich issues with line numbers
        self._enrich_issue_line_numbers(self.issues, line_map, issues_start, raw_text)

        return file_valid

    # ------------------------------------------------------------------
    # Recursive tag walker
    # ------------------------------------------------------------------

    def _validate_tag_node(self, node: dict, file_path: str, tag_path: str) -> bool:
        """Validate a single tag node and recurse into children."""
        if not isinstance(node, dict):
            # Report error for malformed tag entries
            node_type = type(node).__name__
            node_repr = repr(node) if len(repr(node)) < 50 else repr(node)[:47] + "..."
            self.issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="INVALID_TAG_NODE",
                    message=f"Tag node must be a dict/object, got {node_type}: {node_repr}",
                    file_path=file_path,
                    component_path=tag_path or "root",
                    component_type="invalid",
                    suggestion="Each tag must be a JSON object with 'name', 'tagType', etc.",
                )
            )
            self.tag_stats["invalid_tags"] += 1
            return False

        tag_name = node.get("name", "")
        current_path = f"{tag_path}/{tag_name}" if tag_path else tag_name
        tag_type = node.get("tagType", "")

        self.tag_stats["total_tags"] += 1
        if tag_type:
            self.tag_stats["tag_types"].add(tag_type)

        # Schema validation
        schema_valid = self._validate_tag_schema(node, file_path, current_path)

        # Best practices checks
        self._check_tag_best_practices(node, file_path, current_path)

        # Event script validation
        self._validate_event_scripts(node, file_path, current_path)

        if schema_valid:
            self.tag_stats["valid_tags"] += 1
        else:
            self.tag_stats["invalid_tags"] += 1

        # Recurse into child tags
        tags = node.get("tags")
        node_valid = schema_valid
        if isinstance(tags, list):
            for i, child in enumerate(tags):
                child_path = f"{current_path}/tags[{i}]"
                child_valid = self._validate_tag_node(child, file_path, child_path)
                if not child_valid:
                    node_valid = False

        return node_valid

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def _validate_tag_schema(self, node: dict, file_path: str, tag_path: str) -> bool:
        """Validate a tag node against the JSON schema."""
        if not self.jsonschema_available or validate is None:
            return True

        try:
            validate(instance=node, schema=self.schema)
            return True
        except ValidationError as e:
            metadata: dict[str, str] = {}
            if e.absolute_path:
                path_parts = list(e.absolute_path)
                search_prop = None
                for part in reversed(path_parts):
                    if isinstance(part, str):
                        search_prop = part
                        break
                if search_prop:
                    metadata["search_key"] = f'"{search_prop}"'

            tag_name = node.get("name", "")
            if tag_name:
                metadata["tag_name"] = tag_name

            self.issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="SCHEMA_VALIDATION",
                    message=f"Schema validation failed: {e.message}",
                    file_path=file_path,
                    component_path=tag_path,
                    component_type=node.get("tagType", "unknown"),
                    suggestion=(
                        f"Path: {'.'.join(map(str, e.absolute_path))}"
                        if e.absolute_path
                        else None
                    ),
                    metadata=metadata,
                )
            )
            return False

    # ------------------------------------------------------------------
    # Best practices
    # ------------------------------------------------------------------

    def _check_tag_best_practices(
        self, node: dict, file_path: str, tag_path: str
    ) -> None:
        """Run programmatic best-practice checks on a tag node."""
        tag_type = node.get("tagType", "")
        tag_name = node.get("name", "")
        base_metadata: dict[str, str] = {}
        if tag_name:
            base_metadata["tag_name"] = tag_name

        # MISSING_TAG_NAME — INFO level because the git module stores
        # one tag per file, with the name derived from the filename.
        if "name" not in node:
            self.issues.append(
                LintIssue(
                    severity=LintSeverity.INFO,
                    code="MISSING_TAG_NAME",
                    message="Tag has no 'name' property (may be derived from filename)",
                    file_path=file_path,
                    component_path=tag_path,
                    component_type=tag_type or "unknown",
                    suggestion="Name may come from the filename in file-per-tag format",
                    metadata={**base_metadata, "search_key": '"tagType"'},
                )
            )

        # INVALID_TAG_TYPE
        valid_tag_types = {"AtomicTag", "UdtType", "UdtInstance", "Folder", "Provider"}
        if tag_type and tag_type not in valid_tag_types:
            self.issues.append(
                LintIssue(
                    severity=LintSeverity.ERROR,
                    code="INVALID_TAG_TYPE",
                    message=f"Invalid tagType: '{tag_type}'",
                    file_path=file_path,
                    component_path=tag_path,
                    component_type=tag_type,
                    suggestion=f"Valid values: {', '.join(sorted(valid_tag_types))}",
                    metadata={**base_metadata, "search_key": '"tagType"'},
                )
            )

        # AtomicTag-specific checks
        if tag_type == "AtomicTag":
            # MISSING_DATA_TYPE
            if "dataType" not in node:
                self.issues.append(
                    LintIssue(
                        severity=LintSeverity.WARNING,
                        code="MISSING_DATA_TYPE",
                        message="AtomicTag is missing 'dataType'",
                        file_path=file_path,
                        component_path=tag_path,
                        component_type=tag_type,
                        suggestion="Add 'dataType' (e.g., Int4, Float8, Boolean, String)",
                        metadata=base_metadata,
                    )
                )

            # MISSING_VALUE_SOURCE
            if "valueSource" not in node:
                self.issues.append(
                    LintIssue(
                        severity=LintSeverity.INFO,
                        code="MISSING_VALUE_SOURCE",
                        message="AtomicTag has no explicit 'valueSource' (defaults to memory)",
                        file_path=file_path,
                        component_path=tag_path,
                        component_type=tag_type,
                        metadata=base_metadata,
                    )
                )

            value_source = node.get("valueSource", "")

            # OPC_MISSING_CONFIG
            if value_source == "opc":
                if "opcServer" not in node or "opcItemPath" not in node:
                    missing_fields = []
                    if "opcServer" not in node:
                        missing_fields.append("'opcServer'")
                    if "opcItemPath" not in node:
                        missing_fields.append("'opcItemPath'")

                    self.issues.append(
                        LintIssue(
                            severity=LintSeverity.WARNING,
                            code="OPC_MISSING_CONFIG",
                            message=f"OPC tag is missing {' and '.join(missing_fields)}",
                            file_path=file_path,
                            component_path=tag_path,
                            component_type=tag_type,
                            suggestion="Add 'opcServer' and 'opcItemPath' properties",
                            metadata={**base_metadata, "search_key": '"valueSource"'},
                        )
                    )

            # EXPR_MISSING_EXPRESSION
            if value_source == "expr":
                if "expression" not in node:
                    self.issues.append(
                        LintIssue(
                            severity=LintSeverity.ERROR,
                            code="EXPR_MISSING_EXPRESSION",
                            message="Expression tag is missing 'expression' property",
                            file_path=file_path,
                            component_path=tag_path,
                            component_type=tag_type,
                            suggestion="Add an 'expression' property",
                            metadata={**base_metadata, "search_key": '"valueSource"'},
                        )
                    )

            # DB_MISSING_QUERY
            if value_source == "db":
                if "query" not in node:
                    self.issues.append(
                        LintIssue(
                            severity=LintSeverity.WARNING,
                            code="DB_MISSING_QUERY",
                            message="Database tag is missing 'query' property",
                            file_path=file_path,
                            component_path=tag_path,
                            component_type=tag_type,
                            suggestion="Add a 'query' property",
                            metadata={**base_metadata, "search_key": '"valueSource"'},
                        )
                    )

            # HISTORY_NO_PROVIDER
            if node.get("historyEnabled") is True and "historyProvider" not in node:
                self.issues.append(
                    LintIssue(
                        severity=LintSeverity.INFO,
                        code="HISTORY_NO_PROVIDER",
                        message="History is enabled but no 'historyProvider' is specified",
                        file_path=file_path,
                        component_path=tag_path,
                        component_type=tag_type,
                        suggestion="Add 'historyProvider' to ensure history goes to the correct provider",
                        metadata={**base_metadata, "search_key": '"historyEnabled"'},
                    )
                )

            # UNKNOWN_TAG_PROP — only for AtomicTag
            for key in node:
                if key in self.known_atomic_props:
                    continue
                # Skip binding objects (dict with bindType key)
                val = node[key]
                if isinstance(val, dict) and "bindType" in val:
                    continue
                self.issues.append(
                    LintIssue(
                        severity=LintSeverity.STYLE,
                        code="UNKNOWN_TAG_PROP",
                        message=f"Unknown property '{key}' on AtomicTag",
                        file_path=file_path,
                        component_path=tag_path,
                        component_type=tag_type,
                        suggestion="Check for typos or remove if unneeded",
                        metadata={**base_metadata, "search_key": f'"{key}"'},
                    )
                )

        # UdtInstance-specific checks
        if tag_type == "UdtInstance":
            if "typeId" not in node:
                self.issues.append(
                    LintIssue(
                        severity=LintSeverity.ERROR,
                        code="MISSING_TYPE_ID",
                        message="UdtInstance is missing 'typeId'",
                        file_path=file_path,
                        component_path=tag_path,
                        component_type=tag_type,
                        suggestion="Add 'typeId' pointing to the UDT definition",
                        metadata=base_metadata,
                    )
                )

    # ------------------------------------------------------------------
    # Event script validation
    # ------------------------------------------------------------------

    def _validate_event_scripts(
        self, node: dict, file_path: str, tag_path: str
    ) -> None:
        """Validate embedded event scripts using JythonValidator."""
        event_scripts = node.get("eventScripts")
        if not event_scripts:
            return

        # Dict format: {"valueChanged": {"eventScript": "...", "enabled": true}}
        if isinstance(event_scripts, dict):
            for event_name, event_data in event_scripts.items():
                if not isinstance(event_data, dict):
                    continue
                script = event_data.get("eventScript", "")
                if not script or not script.strip():
                    continue

                context = f"{tag_path}.eventScripts.{event_name}"
                self._validate_jython_script(
                    script,
                    event_name,
                    context,
                    file_path,
                    tag_path,
                    node.get("tagType", "unknown"),
                )

        # Array format: [{"eventid": "...", "script": "...", "enabled": true}]
        elif isinstance(event_scripts, list):
            for i, entry in enumerate(event_scripts):
                if not isinstance(entry, dict):
                    continue
                script = entry.get("script", "")
                event_id = entry.get("eventid", f"event[{i}]")
                if not script or not script.strip():
                    continue

                context = f"{tag_path}.eventScripts[{i}]"
                self._validate_jython_script(
                    script,
                    event_id,
                    context,
                    file_path,
                    tag_path,
                    node.get("tagType", "unknown"),
                )

    def _validate_jython_script(
        self,
        script_content: str,
        prop_name: str,
        context: str,
        file_path: str,
        tag_path: str,
        tag_type: str,
    ) -> None:
        """Validate a Jython script and append issues."""
        if not script_content or not script_content.strip():
            return

        validator_issues = self.jython_validator.validate_script(
            script_content, context=context
        )
        for issue in validator_issues:
            issue.file_path = file_path
            issue.component_path = f"{tag_path}.{prop_name}"
            issue.component_type = tag_type
            self.issues.append(issue)

    # ------------------------------------------------------------------
    # Line number mapping and enrichment
    # ------------------------------------------------------------------

    @staticmethod
    def _build_tag_line_map(raw_text: str) -> dict[str, int]:
        """Map tag names to 1-based line numbers in the raw JSON text."""
        line_map: dict[str, int] = {}
        name_pattern = re.compile(r'"name"\s*:\s*"([^"]*)"')
        tag_type_pattern = re.compile(r'"tagType"\s*:\s*"([^"]*)"')

        for lineno, line in enumerate(raw_text.splitlines(), start=1):
            m = name_pattern.search(line)
            if m:
                line_map[m.group(1)] = lineno
            else:
                m = tag_type_pattern.search(line)
                if m:
                    line_map.setdefault(f"__tagType__{m.group(1)}__{lineno}", lineno)

        return line_map

    def _enrich_issue_line_numbers(
        self,
        issues: list[LintIssue],
        line_map: dict[str, int],
        start_idx: int,
        raw_text: str = "",
    ) -> None:
        """Fill in line_number for issues that lack one."""
        raw_lines = raw_text.splitlines() if raw_text else []

        for issue in issues[start_idx:]:
            if issue.line_number is not None:
                continue

            search_key = issue.metadata.get("search_key")
            tag_name = issue.metadata.get("tag_name")

            # Try search_key — direct text search
            if search_key and raw_lines:
                start_line = 0
                if tag_name and tag_name in line_map:
                    start_line = line_map[tag_name] - 1  # 0-indexed
                for i, line in enumerate(raw_lines[start_line:], start_line + 1):
                    if search_key in line:
                        issue.line_number = i
                        break
                if issue.line_number is not None:
                    continue

            # Try tag name from line_map
            if tag_name and tag_name in line_map:
                issue.line_number = line_map[tag_name]
                continue

            # Try tagType fallback
            if issue.component_type:
                for key, lineno in line_map.items():
                    if key.startswith(f"__tagType__{issue.component_type}__"):
                        issue.line_number = lineno
                        break
