from __future__ import annotations

from fastapi import UploadFile
import pandas as pd
from typing import Dict, Any, List, Optional
from database.supabase_client import get_supabase_client
from services.csv_service import read_csv_to_dataframe
import io
import re
import html


CANDIDATES_ALLOWED = {
    "titel","status","datum","update_datum",
    "durchschnittsbewertung","gerundete_durchschnittsbewertung",
    "stellenbeschreibung","verbesserungsvorschlaege",
    "sternebewertung_erklaerung_der_weiteren_schritte",
    "sternebewertung_zufriedenstellende_reaktion",
    "sternebewertung_vollstaendigkeit_der_infos",
    "sternebewertung_zufriedenstellende_antworten",
    "sternebewertung_angenehme_atmosphaere",
    "sternebewertung_professionalitaet_des_gespraechs",
    "sternebewertung_wertschaetzende_behandlung",
    "sternebewertung_erwartbarkeit_des_prozesses",
    "sternebewertung_zeitgerechte_zu_oder_absage",
    "sternebewertung_schnelle_antwort",
    "company_id",
}

EMPLOYEE_ALLOWED = {
    "titel","status","datum","update_datum",
    "durchschnittsbewertung","gerundete_durchschnittsbewertung",
    "jobbeschreibung",
    "gut_am_arbeitgeber_finde_ich",
    "schlecht_am_arbeitgeber_finde_ich",
    "verbesserungsvorschlaege",

    "sternebewertung_arbeitsatmosphaere",
    "sternebewertung_image",
    "sternebewertung_work_life_balance",
    "sternebewertung_karriere_weiterbildung",
    "sternebewertung_gehalt_sozialleistungen",
    "sternebewertung_kollegenzusammenhalt",
    "sternebewertung_umwelt_sozialbewusstsein",
    "sternebewertung_vorgesetztenverhalten",
    "sternebewertung_kommunikation",
    "sternebewertung_interessante_aufgaben",
    "sternebewertung_umgang_mit_aelteren_kollegen",
    "sternebewertung_arbeitsbedingungen",
    "sternebewertung_gleichberechtigung",

    "arbeitsatmosphaere",
    "image",
    "work_life_balance",
    "karriere_weiterbildung",
    "gehalt_sozialleistungen",
    "kollegenzusammenhalt",
    "umwelt_sozialbewusstsein",
    "vorgesetztenverhalten",
    "kommunikation",
    "interessante_aufgaben",
    "umgang_mit_aelteren_kollegen",
    "arbeitsbedingungen",
    "gleichberechtigung",
    "company_id",
}

CANDIDATES_REQUIRED: set[str] = {"titel", "stellenbeschreibung"}
EMPLOYEE_REQUIRED: set[str] = {"titel"}


def slugify(s: str) -> str:
    s = str(s).strip().lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def clean_text(text: str) -> str:
    if not text:
        return text
    return html.unescape(text)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [slugify(c) for c in df.columns]
    return df


def is_sternebewertung_col(col: str) -> bool:
    return col == "sternebewertung" or re.fullmatch(r"sternebewertung_\d+", col) is not None


def extract_sternebewertungen_by_name(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    cols = list(df.columns)

    for col in cols:
        if col.startswith("sternebewertung_") and not re.fullmatch(r"sternebewertung_\d+", col):
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for i, col in enumerate(cols):
        if is_sternebewertung_col(col):
            if i + 1 >= len(cols):
                continue
            topic_col = cols[i + 1]
            new_col = f"sternebewertung_{slugify(topic_col)}"
            if new_col not in df.columns:
                df[new_col] = pd.to_numeric(df[col], errors="coerce")

    drop_cols = [c for c in df.columns if is_sternebewertung_col(c)]
    df = df.drop(columns=drop_cols, errors="ignore")
    return df


def validate_required_columns(df: pd.DataFrame, required: set[str]) -> list[str]:
    return sorted(col for col in required if col not in df.columns)


def to_iso_dt(val) -> Optional[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)) or pd.isna(val):
        return None
    dt = pd.to_datetime(val, errors="coerce")
    if pd.isna(dt):
        return None
    return dt.isoformat()


def get_star_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if c.startswith("sternebewertung_")]


class ExcelProcessor:
    @property
    def supabase(self):
        return get_supabase_client()

    async def process_excel_file(self, file: UploadFile, company_id: int) -> Dict[str, Any]:
        filename = getattr(file, "filename", None)
        try:
            contents = await file.read()
            if not contents:
                return self._error_result(filename, "Leere Datei oder Upload-Inhalt leer.")
            df = pd.read_excel(io.BytesIO(contents))
            return await self._process_dataframe(df, filename, company_id, warnings=[])
        except Exception as exc:
            return self._error_result(filename, str(exc))

    async def process_csv_file(self, file: UploadFile, company_id: int) -> Dict[str, Any]:
        filename = getattr(file, "filename", None)
        try:
            contents = await file.read()
            if not contents:
                return self._error_result(filename, "Leere Datei oder Upload-Inhalt leer.")
            df, warnings = read_csv_to_dataframe(contents)
            return await self._process_dataframe(df, filename, company_id, warnings=warnings)
        except Exception as exc:
            return self._error_result(filename, str(exc))

    @staticmethod
    def _error_result(filename: Optional[str], message: str) -> Dict[str, Any]:
        return {
            "status": "error",
            "filename": filename,
            "total_rows": 0,
            "detected_type": None,
            "imported": {"candidates": 0, "employees": 0},
            "errors": [message],
            "warnings": [],
        }

    async def _process_dataframe(
        self,
        df: pd.DataFrame,
        filename: Optional[str],
        company_id: int,
        warnings: List[str],
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "status": "success",
            "filename": filename,
            "total_rows": int(len(df)),
            "detected_type": None,
            "imported": {"candidates": 0, "employees": 0},
            "errors": [],
            "warnings": list(warnings),
        }

        try:
            df = normalize_columns(df)
            df = extract_sternebewertungen_by_name(df)

            if self._is_candidates_data(df):
                result["detected_type"] = "candidates"
                missing = validate_required_columns(df, CANDIDATES_REQUIRED)
                if missing:
                    result["status"] = "error"
                    result["errors"].append(
                        f"Required columns missing for candidates sheet: {', '.join(missing)}"
                    )
                    return result
                imported, errors = await self._import_candidates(df, company_id)
                result["imported"]["candidates"] = imported
                result["errors"].extend(errors)
            else:
                result["detected_type"] = "employees"
                missing = validate_required_columns(df, EMPLOYEE_REQUIRED)
                if missing:
                    result["status"] = "error"
                    result["errors"].append(
                        f"Required columns missing for employees sheet: {', '.join(missing)}"
                    )
                    return result
                imported, errors = await self._import_employees(df, company_id)
                result["imported"]["employees"] = imported
                result["errors"].extend(errors)

            if (result["imported"]["candidates"] + result["imported"]["employees"]) == 0 and result["errors"]:
                result["status"] = "error"

        except Exception as exc:
            result["status"] = "error"
            result["errors"].append(str(exc))

        return result

    def _is_candidates_data(self, df: pd.DataFrame) -> bool:
        return "stellenbeschreibung" in df.columns

    def _is_employee_data(self, df: pd.DataFrame) -> bool:
        return "stellenbeschreibung" not in df.columns

    async def _import_candidates(self, df: pd.DataFrame, company_id: int) -> tuple[int, List[str]]:
        errors: List[str] = []
        rows_to_insert: List[Dict[str, Any]] = []

        star_columns = [c for c in get_star_columns(df) if c in CANDIDATES_ALLOWED]

        for idx, row in df.iterrows():
            try:
                data: Dict[str, Any] = {
                    "titel": clean_text(str(row.get("titel"))) if pd.notna(row.get("titel")) else None,
                    "status": clean_text(str(row.get("status"))) if pd.notna(row.get("status")) else None,
                    "datum": to_iso_dt(row.get("datum")),
                    "update_datum": to_iso_dt(row.get("update_datum")),
                    "stellenbeschreibung": clean_text(str(row.get("stellenbeschreibung"))) if pd.notna(row.get("stellenbeschreibung")) else None,
                    "verbesserungsvorschlaege": clean_text(str(row.get("verbesserungsvorschlaege"))) if pd.notna(row.get("verbesserungsvorschlaege")) else None,
                    "company_id": company_id,
                }

                vals: List[float] = []
                for c in star_columns:
                    v = row.get(c)
                    if pd.notna(v):
                        fv = float(v)
                        data[c] = fv
                        vals.append(fv)

                avg_excel = row.get("durchschnittsbewertung")
                rnd_excel = row.get("gerundete_durchschnittsbewertung")

                avg = float(avg_excel) if pd.notna(avg_excel) else (sum(vals) / len(vals) if vals else None)
                rnd = float(rnd_excel) if pd.notna(rnd_excel) else (round(avg, 1) if avg is not None else None)

                data["durchschnittsbewertung"] = avg
                data["gerundete_durchschnittsbewertung"] = rnd

                data = {k: v for k, v in data.items() if k in CANDIDATES_ALLOWED}

                rows_to_insert.append(data)

            except Exception as e:
                errors.append(f"candidates row {idx}: {e}")

        if rows_to_insert:
            try:
                self.supabase.table("candidates").insert(rows_to_insert).execute()
            except Exception as e:
                errors.append(f"candidates bulk insert failed: {e}")
                return 0, errors

        return len(rows_to_insert), errors

    async def _import_employees(self, df: pd.DataFrame, company_id: int) -> tuple[int, List[str]]:
        errors: List[str] = []
        rows_to_insert: List[Dict[str, Any]] = []

        star_columns = [c for c in get_star_columns(df) if c in EMPLOYEE_ALLOWED]

        base_cols = {
            "titel", "status", "datum", "update_datum",
            "durchschnittsbewertung", "gerundete_durchschnittsbewertung",
            "jobbeschreibung", "gut_am_arbeitgeber_finde_ich",
            "schlecht_am_arbeitgeber_finde_ich", "verbesserungsvorschlaege",
            "stellenbeschreibung",
        }

        topic_text_cols = [
            c for c in df.columns
            if (c in EMPLOYEE_ALLOWED and not c.startswith("sternebewertung_") and c not in base_cols)
        ]

        for idx, row in df.iterrows():
            try:
                data: Dict[str, Any] = {
                    "titel": clean_text(str(row.get("titel"))) if pd.notna(row.get("titel")) else None,
                    "status": clean_text(str(row.get("status"))) if pd.notna(row.get("status")) else None,
                    "datum": to_iso_dt(row.get("datum")),
                    "update_datum": to_iso_dt(row.get("update_datum")),
                    "jobbeschreibung": clean_text(str(row.get("jobbeschreibung"))) if pd.notna(row.get("jobbeschreibung")) else None,
                    "gut_am_arbeitgeber_finde_ich": clean_text(str(row.get("gut_am_arbeitgeber_finde_ich"))) if pd.notna(row.get("gut_am_arbeitgeber_finde_ich")) else None,
                    "schlecht_am_arbeitgeber_finde_ich": clean_text(str(row.get("schlecht_am_arbeitgeber_finde_ich"))) if pd.notna(row.get("schlecht_am_arbeitgeber_finde_ich")) else None,
                    "verbesserungsvorschlaege": clean_text(str(row.get("verbesserungsvorschlaege"))) if pd.notna(row.get("verbesserungsvorschlaege")) else None,
                    "company_id": company_id,
                }

                for c in topic_text_cols:
                    v = row.get(c)
                    if pd.notna(v):
                        data[c] = clean_text(str(v))

                vals: List[float] = []
                for c in star_columns:
                    v = row.get(c)
                    if pd.notna(v):
                        fv = float(v)
                        data[c] = fv
                        vals.append(fv)

                avg_excel = row.get("durchschnittsbewertung")
                rnd_excel = row.get("gerundete_durchschnittsbewertung")

                avg = float(avg_excel) if pd.notna(avg_excel) else (sum(vals) / len(vals) if vals else None)
                rnd = float(rnd_excel) if pd.notna(rnd_excel) else (round(avg, 1) if avg is not None else None)

                data["durchschnittsbewertung"] = avg
                data["gerundete_durchschnittsbewertung"] = rnd

                data = {k: v for k, v in data.items() if k in EMPLOYEE_ALLOWED}

                rows_to_insert.append(data)

            except Exception as e:
                errors.append(f"employees row {idx}: {e}")

        if rows_to_insert:
            try:
                self.supabase.table("employee").insert(rows_to_insert).execute()
            except Exception as e:
                errors.append(f"employees bulk insert failed: {e}")
                return 0, errors

        return len(rows_to_insert), errors
