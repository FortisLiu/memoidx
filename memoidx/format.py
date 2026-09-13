"""Strict reader and writer for MemoIdx memory files."""

from __future__ import annotations

import re
from uuid import UUID
from datetime import datetime

from .clock import parse_datetime, serialize_datetime
from .models import MemoryFile, MemoryUnit


class MemoryFormatError(ValueError):
    def __init__(self, line: int, reason: str, filename: str = "<memory>"):
        self.line = line
        self.reason = reason
        self.filename = filename
        super().__init__(f"{filename}:{line}: {reason}")


def _field(line: str, name: str, number: int, filename: str) -> str:
    prefix = f"{name}:"
    if not line.startswith(prefix):
        raise MemoryFormatError(number, f"expected {prefix}", filename)
    value = line[len(prefix):].strip()
    if not value:
        raise MemoryFormatError(number, f"missing {name}", filename)
    return value


def _time(value: str, number: int, filename: str) -> datetime:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})", value):
        raise MemoryFormatError(number, "invalid datetime", filename)
    try:
        result = parse_datetime(value)
    except ValueError as exc:
        raise MemoryFormatError(number, "invalid datetime", filename) from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise MemoryFormatError(number, "datetime must include timezone", filename)
    return result


def _id(value, prefix, line, filename):
    try:
        if not value.startswith(prefix):
            raise ValueError()
        UUID(value[len(prefix):])
    except ValueError as exc:
        raise MemoryFormatError(line, "invalid ID: expected " + prefix + "UUID", filename) from exc
    return value


def parse_memory(text: str, filename: str = "<memory>") -> MemoryFile:
    lines = text.splitlines()
    def need(index: int) -> str:
        if index >= len(lines):
            raise MemoryFormatError(index + 1, "unexpected end of file", filename)
        return lines[index]

    if need(0) != "Abstraction:":
        raise MemoryFormatError(1, "expected Abstraction:", filename)
    if len(lines) < 4 or any(lines[i].startswith(("file id:", "Latest used time:", "Summary of:")) for i in range(1, min(4, len(lines)))):
        raise MemoryFormatError(len(lines) + 1, "summary must contain three lines", filename)
    summary = tuple(lines[1:4])
    index = 4
    file_id_line = index + 1
    file_id = _field(need(index), "file id", index + 1, filename); index += 1
    latest = _time(_field(need(index), "Latest used time", index + 1, filename), index + 1, filename); index += 1
    summary_of = _field(need(index), "Summary of", index + 1, filename); index += 1
    _id(file_id, "f_", file_id_line, filename)
    if need(index) != "":
        raise MemoryFormatError(index + 1, "expected blank line before units", filename)
    index += 1
    units = []
    seen = {file_id}
    while index < len(lines):
        unit_line = _field(need(index), "Memory id", index + 1, filename); index += 1
        _id(unit_line, "u_", index, filename)
        if unit_line in seen:
            raise MemoryFormatError(index, "duplicate ID", filename)
        seen.add(unit_line)
        unit_time = _time(_field(need(index), "Latest used time", index + 1, filename), index + 1, filename); index += 1
        retention = _field(need(index), "Retention", index + 1, filename); index += 1
        if retention not in ("normal", "pinned"):
            raise MemoryFormatError(index, "retention must be normal or pinned", filename)
        source = _field(need(index), "Source", index + 1, filename); index += 1
        if need(index) != 'Content:"""':
            raise MemoryFormatError(index + 1, 'expected Content:"""', filename)
        index += 1
        content = []
        while index < len(lines) and lines[index] != '"""':
            if not lines[index].startswith("    "):
                raise MemoryFormatError(index + 1, "content line must start with four spaces", filename)
            content.append(lines[index][4:]); index += 1
        if index >= len(lines):
            raise MemoryFormatError(index + 1, "unterminated content", filename)
        index += 1
        units.append(MemoryUnit(unit_line, unit_time, retention, source, "\n".join(content)))
        if index < len(lines):
            if need(index) != "":
                raise MemoryFormatError(index + 1, "expected blank line between units", filename)
            index += 1
    if not units:
        raise MemoryFormatError(index + 1, "at least one unit is required", filename)
    return MemoryFile(file_id, summary, latest, summary_of, units)


def serialize_memory(memory: MemoryFile) -> str:
    if len(memory.summary) != 3:
        raise ValueError("summary must contain exactly three lines")
    if not memory.units:
        raise ValueError("at least one unit is required")
    out = ["Abstraction:", *memory.summary, f"file id: {memory.id}",
           f"Latest used time: {serialize_datetime(memory.latest_used_time)}",
           f"Summary of: {memory.summary_of}", ""]
    for position, unit in enumerate(memory.units):
        out += [f"Memory id: {unit.id}", f"Latest used time: {serialize_datetime(unit.latest_used_time)}",
                f"Retention: {unit.retention}", f"Source: {unit.source}", 'Content:"""']
        out += [f"    {line}" for line in unit.content.split("\n")]
        out.append('"""')
        if position + 1 < len(memory.units): out.append("")
    text = "\n".join(out) + "\n"
    parsed = parse_memory(text)
    if parsed != memory:
        raise MemoryFormatError(1, "serialization would change data")
    return text
