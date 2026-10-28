from __future__ import annotations

import csv
import io
import pandas as pd

SUPPORTED_DELIMITERS = [",", ";", "\t"]
SNIFF_SAMPLE_SIZE = 8192


def detect_encoding(raw: bytes) -> tuple[str, bool]:
    try:
        raw.decode("utf-8")
        return "utf-8", False
    except UnicodeDecodeError:
        return "latin-1", True


def detect_delimiter(text: str) -> str:
    sample = text[:SNIFF_SAMPLE_SIZE]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        if dialect.delimiter in SUPPORTED_DELIMITERS:
            return dialect.delimiter
    except csv.Error:
        pass

    lines = sample.splitlines()[:5]
    counts = {d: sum(line.count(d) for line in lines) for d in SUPPORTED_DELIMITERS}
    best = max(counts, key=lambda d: counts[d])
    return best if counts[best] > 0 else ","


def read_csv_to_dataframe(raw: bytes) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []

    encoding, had_fallback = detect_encoding(raw)
    if had_fallback:
        warnings.append(
            "Encoding-Warnung: Die Datei ist nicht UTF-8-kodiert. "
            "Latin-1 (ISO-8859-1) wird als Fallback verwendet. "
            "Bitte exportieren Sie die CSV-Datei als UTF-8 für beste Ergebnisse."
        )

    text = raw.decode(encoding, errors="replace")
    delimiter = detect_delimiter(text)

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,
        )
    except Exception as exc:
        raise ValueError(f"CSV konnte nicht gelesen werden: {exc}") from exc

    str_cols = df.select_dtypes(include="object").columns
    df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())

    df.replace("", pd.NA, inplace=True)

    return df, warnings
