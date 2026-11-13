"""XLSX reading and writing for the admin import/export center (Release 1.0 F1L-6).

Reading is bounded (file size, rows, columns, decompressed size) and returns
plain string cells so the existing JSON import pipeline (preview -> confirm)
stays the single validation path. Writing neutralises spreadsheet formula
injection and keeps identifier columns as text so leading zeros survive.
"""
import io
import zipfile
from datetime import date, datetime, time
from decimal import Decimal

from django.utils import timezone
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from rest_framework.exceptions import ValidationError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024
MAX_ROWS = 1000
MAX_COLUMNS = 50
XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
FORMULA_PREFIXES = ('=', '+', '-', '@', '\t', '\r')


def _cell_text(value):
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, datetime):
        return value.date().isoformat() if value.time() == time(0) else value.isoformat(timespec='minutes')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def read_xlsx_rows(upload):
    """Return (headers, rows) from the first sheet; rows are dicts of strings."""
    if upload is None:
        raise ValidationError({'file': 'An .xlsx file is required.'})
    if upload.size > MAX_UPLOAD_BYTES:
        raise ValidationError({'file': 'The file exceeds the 5 MB limit.'})
    data = upload.read()
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            if sum(item.file_size for item in archive.infolist()) > MAX_UNCOMPRESSED_BYTES:
                raise ValidationError({'file': 'The workbook is too large when uncompressed.'})
            if 'xl/workbook.xml' not in archive.namelist():
                raise ValidationError({'file': 'The file is not a valid .xlsx workbook.'})
        workbook = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    except ValidationError:
        raise
    except Exception as exc:  # zipfile.BadZipFile, KeyError, openpyxl parse errors
        raise ValidationError({'file': 'The file is not a valid .xlsx workbook.'}) from exc
    try:
        sheet = workbook.worksheets[0]
        iterator = sheet.iter_rows(values_only=True)
        header_row = next(iterator, None)
        if not header_row:
            raise ValidationError({'file': 'The first sheet has no header row.'})
        if len(header_row) > MAX_COLUMNS:
            raise ValidationError({'file': f'A sheet is limited to {MAX_COLUMNS} columns.'})
        headers = [_cell_text(value) for value in header_row]
        while headers and not headers[-1]:
            headers.pop()
        if not any(headers):
            raise ValidationError({'file': 'The first sheet has no header row.'})
        rows = []
        for values in iterator:
            texts = [_cell_text(value) for value in (values or ())[:len(headers)]]
            if not any(texts):
                continue
            if len(rows) >= MAX_ROWS:
                raise ValidationError({'file': f'A single import is limited to {MAX_ROWS} rows.'})
            rows.append({name: (texts[i] if i < len(texts) else '') for i, name in enumerate(headers) if name})
        return [name for name in headers if name], rows
    finally:
        workbook.close()


def _safe_value(value):
    if value is None:
        return ''
    if isinstance(value, datetime) and timezone.is_aware(value):
        return timezone.localtime(value).replace(tzinfo=None)
    if isinstance(value, (bool, int, float, Decimal, date, datetime)):
        return value
    text = str(value)
    if text.startswith(FORMULA_PREFIXES):
        # A leading apostrophe makes Excel show the text instead of evaluating it.
        return "'" + text
    return text


def build_xlsx(columns, rows, sheet_title='Data', text_columns=(), notes=()):
    """Build an RTL workbook. `columns` is [(key, header_label)]; returns bytes."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title[:31]
    sheet.sheet_view.rightToLeft = True
    sheet.freeze_panes = 'A2'
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='1F5FAF')
    for index, (_, label) in enumerate(columns, start=1):
        cell = sheet.cell(row=1, column=index, value=label)
        cell.font, cell.fill = header_font, header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
    widths = [max(12, len(str(label)) + 4) for _, label in columns]
    for row_index, row in enumerate(rows, start=2):
        for col_index, (key, _) in enumerate(columns, start=1):
            value = row.get(key)
            if key in text_columns and value not in (None, ''):
                value = str(value)
            cell = sheet.cell(row=row_index, column=col_index, value=_safe_value(value))
            if key in text_columns:
                cell.number_format = '@'
            elif isinstance(value, datetime):
                cell.number_format = 'yyyy-mm-dd hh:mm'
            elif isinstance(value, date):
                cell.number_format = 'yyyy-mm-dd'
            widths[col_index - 1] = min(60, max(widths[col_index - 1], len(str(cell.value)) + 2))
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
        if not rows and columns[index - 1][0] in text_columns:
            # Pre-format empty template rows too, so typed codes keep their zeros.
            for row_index in range(len(rows) + 2, len(rows) + 202):
                sheet.cell(row=row_index, column=index).number_format = '@'
    if notes:
        guide = workbook.create_sheet('تعليمات')
        guide.sheet_view.rightToLeft = True
        guide.column_dimensions['A'].width = 90
        for row_index, note in enumerate(notes, start=1):
            guide.cell(row=row_index, column=1, value=_safe_value(note))
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()
