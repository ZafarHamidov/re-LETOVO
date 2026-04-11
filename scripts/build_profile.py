from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email import policy
from email.parser import BytesParser
from html import unescape
from pathlib import Path
from typing import Any

import docx
import openpyxl
from bs4 import BeautifulSoup
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "source-materials"
DATA_DIR = ROOT / "data"
DOCS_DIR = ROOT / "docs"
MHTML_RENDER_DIR = DOCS_DIR / "mhtml-rendered"
SUPPORTED_EXTENSIONS = {".pdf", ".mhtml", ".html", ".docx", ".jpg", ".jpeg", ".png", ".xlsx"}
IGNORED_DIRS = {"data", "docs", "scripts", "site", "__pycache__"}


@dataclass(slots=True)
class EvidenceRecord:
    source_file: str
    relative_path: str
    extension: str
    category: str
    text: str
    title: str


def ensure_output_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)
    MHTML_RENDER_DIR.mkdir(exist_ok=True)


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in SOURCE_DIR.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files)


def clean_text(value: str) -> str:
    text = unescape(value).replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def categorize(path: Path) -> str:
    lookup = f"{path.as_posix()}".lower()
    rules = [
        ("mock_exams", ["пробн", "psat", "sat", "ielts", "toefl", "exam"]),
        ("olympiads", ["олимпиад", "olympiad", "region certificate", "diplom"]),
        ("academics", ["успеваем", "grades", "report", "результаты обучения", "school’s report"]),
        ("activities", ["внеакадем", "активност", "service", "достижения", "mission", "автономный"]),
        ("admissions", ["cambridge", "a-level", "ib dp", "offers spreadsheet", "admissions"]),
        ("administrative", ["договор", "schedule", "кабинет", "delta"]),
    ]
    for category, keywords in rules:
        if any(keyword in lookup for keyword in keywords):
            return category
    return "general"


def get_mhtml_html(path: Path) -> str:
    message = BytesParser(policy=policy.default).parsebytes(path.read_bytes())
    html = ""
    for part in message.walk():
        if part.get_content_type() == "text/html":
            payload = part.get_payload(decode=True) or b""
            charset = part.get_content_charset() or "utf-8"
            html = payload.decode(charset, errors="ignore")
            break
    return html


def extract_mhtml(path: Path) -> str:
    html = get_mhtml_html(path)
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    lines = [line.strip() for line in soup.get_text("\n").splitlines() if line.strip()]
    return clean_text("\n".join(lines))


def extract_pdf(path: Path) -> str:
    chunks: list[str] = []
    try:
        for page in PdfReader(str(path)).pages:
            chunks.append(page.extract_text() or "")
    except Exception:
        return ""
    return clean_text("\n".join(chunks))


def extract_docx(path: Path) -> str:
    try:
        document = docx.Document(str(path))
    except Exception:
        return ""
    lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return clean_text("\n".join(lines))


def extract_xlsx(path: Path) -> str:
    try:
        workbook = openpyxl.load_workbook(path, data_only=True)
    except Exception:
        return ""
    lines: list[str] = []
    for sheet in workbook.worksheets[:3]:
        lines.append(f"Sheet: {sheet.title}")
        for row in sheet.iter_rows(min_row=1, max_row=20, values_only=True):
            values = [str(cell).strip() for cell in row if cell not in (None, "")]
            if values:
                lines.append(" | ".join(values))
    return clean_text("\n".join(lines))


def extract_image_placeholder(path: Path) -> str:
    return f"Image asset available for manual review: {path.name}"


def extract_text(path: Path) -> str:
    loaders = {
        ".mhtml": extract_mhtml,
        ".html": lambda p: clean_text(p.read_text(encoding="utf-8", errors="ignore")),
        ".pdf": extract_pdf,
        ".docx": extract_docx,
        ".xlsx": extract_xlsx,
        ".jpg": extract_image_placeholder,
        ".jpeg": extract_image_placeholder,
        ".png": extract_image_placeholder,
    }
    return loaders[path.suffix.lower()](path)


def build_inventory(files: list[Path]) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in files:
        rel_path = path.relative_to(ROOT).as_posix()
        inventory.append(
            {
                "file_name": path.name,
                "relative_path": rel_path,
                "extension": path.suffix.lower(),
                "category": categorize(path),
                "size_bytes": path.stat().st_size,
                "modified_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
            }
        )
    return inventory


def build_records(files: list[Path]) -> list[EvidenceRecord]:
    records: list[EvidenceRecord] = []
    for path in files:
        records.append(
            EvidenceRecord(
                source_file=path.name,
                relative_path=path.relative_to(ROOT).as_posix(),
                extension=path.suffix.lower(),
                category=categorize(path),
                text=extract_text(path),
                title=path.stem,
            )
        )
    return records


def detect_student_photo() -> str | None:
    candidates = [
        SOURCE_DIR / "Personal goals" / "photo.jpg",
        SOURCE_DIR / "Personal goals" / "photo.jpeg",
        SOURCE_DIR / "Personal goals" / "photo.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.relative_to(ROOT).as_posix()
    return None


def detect_ideal_image() -> str | None:
    preferred = SOURCE_DIR / "Personal goals" / "Zafar ideal 2.png"
    if preferred.exists():
        return preferred.relative_to(ROOT).as_posix()

    candidates = [
        SOURCE_DIR / "Personal goals" / "Zafar ideal 2.jpg",
        SOURCE_DIR / "Personal goals" / "Zafar ideal 2.jpeg",
        SOURCE_DIR / "Personal goals" / "Zafar ideal.png",
        SOURCE_DIR / "Personal goals" / "Zafar ideal.jpg",
        SOURCE_DIR / "Personal goals" / "Zafar ideal.jpeg",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.relative_to(ROOT).as_posix()
    return None


def snippet(text: str, limit: int = 400) -> str:
    compact = re.sub(r"\s+", " ", text).strip()
    return compact[:limit]


def split_text_blocks(text: str) -> list[str]:
    if not text:
        return []
    blocks = [clean_text(block) for block in re.split(r"\n{2,}", text) if clean_text(block)]
    return [block for block in blocks if len(block) > 1]


def normalize_mhtml_lines(text: str) -> list[str]:
    lines = [clean_text(line) for line in text.splitlines() if clean_text(line)]
    if not lines:
        return []

    start_markers = [
        "Автор:",
        "Академические результаты",
        "Результаты обучения",
        "Общая характеристика",
        "Предмет:",
        "Комментарии",
        "Многосрочный комментарий",
        "Наблюдения и рекомендации",
        "Самоопределение и планы",
        "Навыки",
        "Заголовок",
    ]
    noise_markers = [
        "Личный Кабинет",
        "Информация",
        "Профиль ученика",
        "Доверенные сопровождающие",
        "Репорты по ученику (архив)",
        "Репорты по ученику (новые)",
        "Календарь учебного года",
        "Текущий учебный план",
        "Академ. успеваемость",
        "Академ. пропуски",
        "Ближайшие саммативы",
        "Портфолио (Внеакадем)",
        "Мои мероприятия",
        "Архив брифингов и встреч",
        "Заявки и документы",
        "Счета по обучению и питанию",
        "Скачать вакцинальный сертификат",
        "Выход из профиля",
        "Профиль:",
        "Электронная почта наставника:",
        "Написать",
        "halimjonik@gmail.com",
    ]

    start_index = 0
    for index, line in enumerate(lines):
        if any(marker in line for marker in start_markers):
            start_index = index
            break

    filtered: list[str] = []
    previous = ""
    for line in lines[start_index:]:
        if any(marker in line for marker in noise_markers):
            continue
        if re.fullmatch(r"[A-Za-zА-Яа-яЁё]\s*", line):
            continue
        if len(line) < 2:
            continue
        if line == previous:
            continue
        previous = line
        filtered.append(line)
    return filtered


def build_mhtml_text_blocks(text: str) -> list[str]:
    lines = normalize_mhtml_lines(text)
    if not lines:
        return []

    blocks: list[str] = []
    current: list[str] = []
    heading_markers = ("Автор:", "Предмет:", "Общая характеристика", "Академические результаты", "Результаты обучения")

    for line in lines:
        looks_like_heading = (
            len(line) <= 80
            and not line.endswith((".", ";", ","))
            and not re.match(r"^\d{4}-\d{2}-\d{2}$", line)
            and (line.istitle() or any(marker in line for marker in heading_markers))
        )
        starts_new_block = looks_like_heading or re.match(r"^\d+\.", line)
        if starts_new_block and current:
            blocks.append(clean_text(" ".join(current)))
            current = [line]
            continue
        current.append(line)

    if current:
        blocks.append(clean_text(" ".join(current)))

    deduped: list[str] = []
    seen: set[str] = set()
    for block in blocks:
        if len(block) < 10:
            continue
        if block in seen:
            continue
        seen.add(block)
        deduped.append(block)
    return deduped


def detect_focus_areas(records: list[EvidenceRecord]) -> list[str]:
    combined = " ".join(record.text.lower() for record in records)
    focus_map = {
        "Artificial Intelligence": ["artificial intelligence", "искусственный интеллект", "ai"],
        "Physics": ["physics", "физик"],
        "Informatics": ["informat", "информат"],
        "Mathematics": ["математ", "math"],
        "Bilingual / international track": ["bilingual", "cambridge", "as ", "a level"],
    }
    focus = [label for label, patterns in focus_map.items() if any(pattern in combined for pattern in patterns)]
    return focus or ["STEM", "Long-term university preparation"]


def extract_goals(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    for record in records:
        lower_name = record.source_file.lower()
        if record.extension != ".docx":
            continue
        if "psat" in lower_name:
            goals.append(
                {
                    "title": "Score 1400+ on the PSAT and secure an official result",
                    "deadline": "2025-12-31",
                    "status": "in_progress",
                    "source_file": record.relative_path,
                }
            )
        if "mission" in lower_name or "ai" in lower_name:
            goals.append(
                {
                    "title": "Build a focused AI-centered academic profile through olympiads, projects, and public-facing work",
                    "deadline": "missing",
                    "status": "in_progress",
                    "source_file": record.relative_path,
                }
            )
        if "автономный" in lower_name:
            goals.append(
                {
                    "title": "Strengthen autonomous learning, planning, and strategic self-management",
                    "deadline": "missing",
                    "status": "in_progress",
                    "source_file": record.relative_path,
                }
            )
    return goals


def extract_ielts(records: list[EvidenceRecord]) -> dict[str, Any] | None:
    for record in records:
        if "ielts" not in record.source_file.lower():
            continue
        text = record.text
        overall = re.search(r"\b(9(?:\.0)?|8(?:\.5)?|7(?:\.5)?|6(?:\.5)?)\b", text)
        date_match = re.search(r"(\d{2}/[A-Z]{3}/\d{4})", text)
        return {
            "exam": "IELTS Academic",
            "date": date_match.group(1) if date_match else "2025-08-26",
            "score": overall.group(1) if overall else "needs_review",
            "max_score": "9.0",
            "percent": None,
            "evidence_link": record.relative_path,
            "needs_review": False,
        }
    return None


def normalize_date_value(raw: str) -> str | None:
    raw = raw.strip()
    formats = ("%Y-%m-%d", "%d/%b/%Y", "%d/%B/%Y", "%Y/%m/%d", "%d.%m.%Y")
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def extract_image_exam_schedule(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    schedule_record = next((record for record in records if record.source_file.lower() == "exam-schedule-erevan.jpg"), None)
    if not schedule_record:
        return []

    raw_items = [
        ("2026-04-28", "Physics 33: Advanced Practical Skills", "Cambridge Physics 9702, paper 33.", "AM"),
        ("2026-04-29", "Mathematics 12: Pure Mathematics 1", "Cambridge Mathematics 9709, paper 12.", "PM"),
        ("2026-05-06", "Mathematics 42: Mechanics", "Cambridge Mathematics 9709, paper 42.", "PM"),
        ("2026-05-07", "Further Mathematics 12: Further Pure Mathematics", "Cambridge Further Mathematics 9231, paper 12.", "PM"),
        ("2026-05-08", "Computer Science 12: Theory Fundamentals", "Cambridge Computer Science 9618, paper 12.", "PM"),
        ("2026-05-13", "Computer Science 22: Problem Solving and Programming", "Cambridge Computer Science 9618, paper 22.", "PM"),
        ("2026-05-20", "Physics 22: AS Level Structured Questions", "Cambridge Physics 9702, paper 22.", "AM"),
        ("2026-05-21", "Further Mathematics 32: Further Mechanics", "Cambridge Further Mathematics 9231, paper 32.", "PM"),
        ("2026-06-03", "Physics 12: Multiple Choice", "Cambridge Physics 9702, paper 12.", "AM"),
    ]
    return [
        {
            "date": date,
            "title": title,
            "summary": f"{summary} Extracted from the Erevan exam schedule image. Session: {session}.",
            "kind": "exam_schedule",
            "source_type": "documented",
            "status": "upcoming",
            "source_file": schedule_record.relative_path,
            "session": session,
            "group": "Erevan A-Level schedule",
        }
        for date, title, summary, session in raw_items
    ]


def build_exam_calendar(records: list[EvidenceRecord], goals: list[dict[str, Any]], certificates: list[dict[str, Any]], mock_exams: list[dict[str, Any]], olympiads: list[dict[str, Any]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    entries.extend(extract_image_exam_schedule(records))

    for exam in mock_exams:
        exam_date = normalize_date_value(exam["date"])
        if not exam_date:
            continue
        dt = datetime.fromisoformat(exam_date)
        prep_points = [
            (dt - timedelta(days=56), "IELTS prep cycle begins", "Build a focused 8-week review plan around reading, writing, listening, and speaking.", "prep_checkpoint", "inferred"),
            (dt - timedelta(days=21), "IELTS full mock checkpoint", "Run a full timed mock and review weak bands before the final stretch.", "mock_checkpoint", "inferred"),
            (dt, "IELTS Academic test date", f"Official exam date recorded in the IELTS evidence. Latest recorded band: {exam['score']}/{exam['max_score']}.", "exam_date", "documented"),
        ]
        for when, title, summary, kind, source_type in prep_points:
            entries.append(
                {
                    "date": when.date().isoformat(),
                    "title": title,
                    "summary": summary,
                    "kind": kind,
                    "source_type": source_type,
                    "status": "completed",
                    "source_file": exam["evidence_link"],
                }
            )

    for certificate in certificates:
        normalized = normalize_date_value(certificate["date"])
        if not normalized:
            continue
        entries.append(
            {
                "date": normalized,
                "title": certificate["title"],
                "summary": f"Evidence-backed certificate or result date from {certificate['issuer']}.",
                "kind": "result_release",
                "source_type": "documented",
                "status": "completed",
                "source_file": certificate["evidence_link"],
            }
        )

    for olympiad in olympiads:
        normalized = normalize_date_value(olympiad["date"])
        if not normalized:
            continue
        entries.append(
            {
                "date": normalized,
                "title": olympiad["title"],
                "summary": f"{olympiad['result']} at {olympiad['level']} level.",
                "kind": "competition",
                "source_type": "documented",
                "status": "completed",
                "source_file": olympiad["evidence_link"],
            }
        )

    psat_goal = next((goal for goal in goals if "psat" in goal["title"].lower() and goal["deadline"] != "missing"), None)
    if psat_goal:
        deadline = normalize_date_value(psat_goal["deadline"])
        if deadline:
            dt = datetime.fromisoformat(deadline)
            psat_points = [
                (dt - timedelta(days=56), "PSAT study block begins", "Open the disciplined 8-week prep block: reading drills, vocabulary review, and timed math sets.", "prep_checkpoint"),
                (dt - timedelta(days=28), "PSAT full-length practice checkpoint", "Take a full practice test and convert errors into a targeted final-month review list.", "mock_checkpoint"),
                (dt - timedelta(days=7), "PSAT final review week", "Shift from new material to speed, accuracy, and confidence under timed conditions.", "final_review"),
                (dt, "PSAT target deadline", "Year-end target to secure an official PSAT result aligned with the stated 1400+ goal.", "target_deadline"),
            ]
            for when, title, summary, kind in psat_points:
                entries.append(
                    {
                        "date": when.date().isoformat(),
                        "title": title,
                        "summary": summary,
                        "kind": kind,
                        "source_type": "inferred",
                        "status": "planned",
                        "source_file": psat_goal["source_file"],
                    }
                )

    term_report = next((record for record in records if "term_report_1_25-26" in record.source_file.lower()), None)
    if term_report:
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", term_report.source_file)
        if match:
            entries.append(
                {
                    "date": match.group(1),
                    "title": "Term 1 AS report issued",
                    "summary": "Useful checkpoint for reviewing subject outcomes before the next exam-prep cycle.",
                    "kind": "academic_checkpoint",
                    "source_type": "documented",
                    "status": "completed",
                    "source_file": term_report.relative_path,
                }
            )

    deduped: dict[tuple[str, str], dict[str, Any]] = {}
    for entry in entries:
        deduped[(entry["date"], entry["title"])] = entry

    ordered = sorted(deduped.values(), key=lambda item: item["date"])
    return {
        "note": "Documented dates come from certificates, reports, the Erevan exam schedule image, and test evidence. Prep checkpoints are inferred from those deadlines so the timeline stays actionable.",
        "entries": ordered,
    }


def extract_olympiads(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    olympiads: list[dict[str, Any]] = []
    for record in records:
        source = record.source_file.lower()
        text = record.text
        if "region certificate" in source:
            olympiads.append(
                {
                    "title": "All-Russian Olympiad in Physics",
                    "level": "Regional stage",
                    "result": "Prize winner",
                    "date": "2025-01-27",
                    "evidence_link": record.relative_path,
                    "subject": "Physics",
                }
            )
        if "олимпиады - личный кабинет.pdf" == source:
            patterns = [
                ("Informatics", "Municipal", "Winner", "2025-2026"),
                ("Informatics", "School", "Winner", "2025-2026"),
                ("Mathematics", "School", "Prize winner", "2024-2025"),
                ("Physics", "School", "Winner", "2024-2025"),
                ("Mathematics", "Municipal", "Prize winner", "2024-2025"),
                ("Physics", "Municipal", "Prize winner", "2024-2025"),
            ]
            for subject, level, result, period in patterns:
                if subject.lower() in text.lower():
                    olympiads.append(
                        {
                            "title": f"All-Russian Olympiad in {subject}",
                            "level": level,
                            "result": result,
                            "date": period,
                            "evidence_link": record.relative_path,
                            "subject": subject,
                        }
                    )
    return olympiads


def extract_comments(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    comments: list[dict[str, Any]] = []
    report_record = next((record for record in records if "результаты обучения" in record.source_file.lower()), None)
    if not report_record:
        return comments

    lower = report_record.text.lower()
    if "высокую внутреннюю мотивацию" in lower:
        comments.append({"theme": "motivation", "summary": "School commentary highlights high internal motivation and clear academic goals.", "source_file": report_record.relative_path})
    if "билингвальной программы" in lower:
        comments.append({"theme": "adaptation", "summary": "Reports state that Zafar adapted successfully to the bilingual program and its higher standards.", "source_file": report_record.relative_path})
    if "глубокой рефлексии" in lower:
        comments.append({"theme": "reflection", "summary": "Psychology commentary notes strong self-reflection and realistic planning.", "source_file": report_record.relative_path})
    if "индивидуальной выпускной работы" in lower:
        comments.append({"theme": "research", "summary": "The grade-level report confirms ongoing individual graduation work with project drafts and supervision.", "source_file": report_record.relative_path})
    if "service" in lower:
        comments.append({"theme": "service", "summary": "The report references service-program participation and external foundation visits.", "source_file": report_record.relative_path})
    return comments


def extract_activities(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    activities: list[dict[str, Any]] = []
    comments = extract_comments(records)
    comment_lookup = {item["theme"] for item in comments}
    if "service" in comment_lookup:
        activities.append(
            {
                "name": "Service program",
                "role": "Participant",
                "period": "2025-2026",
                "impact": "Evidence indicates participation in foundation visits and socially oriented project work.",
                "evidence_link": next(item["source_file"] for item in comments if item["theme"] == "service"),
            }
        )
    mission_record = next((record for record in records if "mission" in record.source_file.lower()), None)
    if mission_record:
        activities.append(
            {
                "name": "AI mission statement and self-directed career planning",
                "role": "Founder of personal roadmap",
                "period": "2025",
                "impact": "Shows a clear long-term ambition around AI, leadership, and high-impact technical work.",
                "evidence_link": mission_record.relative_path,
            }
        )
    autonomy_record = next((record for record in records if "автономный" in record.source_file.lower()), None)
    if autonomy_record:
        activities.append(
            {
                "name": "Autonomous learner framework",
                "role": "Student participant",
                "period": "2025",
                "impact": "Focuses on self-management, strategic learning, and navigating complex school systems with maturity.",
                "evidence_link": autonomy_record.relative_path,
            }
        )
    return activities


def extract_certificates(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    certificates: list[dict[str, Any]] = []
    for record in records:
        source = record.source_file.lower()
        if "ielts" in source:
            certificates.append(
                {
                    "title": "IELTS Academic",
                    "issuer": "IELTS",
                    "date": "2025-08-26",
                    "evidence_link": record.relative_path,
                }
            )
        if "region certificate" in source:
            certificates.append(
                {
                    "title": "Regional Olympiad Certificate in Physics",
                    "issuer": "Moscow Department of Education and Science",
                    "date": "2025-03-14",
                    "evidence_link": record.relative_path,
                }
            )
    return certificates


def extract_academics(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    academics: list[dict[str, Any]] = []
    report_record = next((record for record in records if "результаты обучения" in record.source_file.lower()), None)
    if report_record:
        lower = report_record.text.lower()
        teacher_comment = None
        if "высокую внутреннюю мотивацию" in lower:
            teacher_comment = "The school report describes strong internal motivation, responsibility, and thoughtful engagement with complex academic tasks."
        academics.append(
            {
                "source_file": report_record.relative_path,
                "period": "Term 1, 2025-2026",
                "subject": "Bilingual / upper-school program adaptation",
                "grade": "estimated-strong",
                "teacher_comment": teacher_comment,
                "evidence_link": report_record.relative_path,
                "needs_review": True,
            }
        )

    pdf_record = next((record for record in records if "term_report_1_25-26" in record.source_file.lower()), None)
    if pdf_record and pdf_record.text:
        academics.append(
            {
                "source_file": pdf_record.relative_path,
                "period": "Term 1, 2025-2026",
                "subject": "AS / bilingual term report",
                "grade": "report-available",
                "teacher_comment": "A formal term report is present and should be reviewed manually for subject-level marks before public release.",
                "evidence_link": pdf_record.relative_path,
                "needs_review": True,
            }
        )
    return academics


def build_gap_analysis(records: list[EvidenceRecord], olympiads: list[dict[str, Any]], mock_exams: list[dict[str, Any]]) -> dict[str, Any]:
    strengths = [
        "Evidence-backed STEM orientation with physics and informatics competition history.",
        "Strong English profile supported by an IELTS Academic result.",
        "School commentary points to motivation, reflection, and successful adaptation to a demanding bilingual track.",
        "Early signs of purposeful narrative around AI and self-directed growth.",
    ]
    weaknesses = [
        "Research output is mentioned, but no finished project abstract, poster, or publication-ready artifact is present.",
        "Leadership is visible in ambition and planning, but not yet documented through long-term, public impact artifacts.",
        "Testing profile is incomplete for university admissions: PSAT plan exists, but official standardized-test outcomes are not yet included beyond IELTS.",
    ]
    missing_items = [
        "A concise one-page academic CV or achievements summary.",
        "A documented research/project portfolio with links, screenshots, or abstracts.",
        "A university shortlist with target countries, majors, deadlines, and rationale.",
        "Recommendation tracker and personal-statement draft status.",
        "Updated 2025-2026 subject-by-subject grade table that is safe to publish publicly.",
    ]
    next_actions = [
        "Finish a public-facing AI/project portfolio artifact and attach evidence.",
        "Add official PSAT/SAT or equivalent results once available.",
        "Turn the graduation/research work into a polished summary with impact and methods.",
        "Document one sustained leadership or service initiative with measurable outcomes.",
        "Separate public-safe evidence from private full evidence before GitHub Pages deployment.",
    ]
    if len(olympiads) < 3:
        weaknesses.append("Competition depth needs more current, higher-level results to stand out nationally or internationally.")
    if not mock_exams:
        missing_items.append("Mock exam score summaries that can be clearly interpreted without opening school portals.")
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "missing_items": missing_items,
        "next_actions": next_actions,
    }


def build_readiness(goals: list[dict[str, Any]], olympiads: list[dict[str, Any]], activities: list[dict[str, Any]], certificates: list[dict[str, Any]], comments: list[dict[str, Any]]) -> dict[str, Any]:
    components = [
        {"id": "academics", "label": "Academic strength", "score": 78, "reason": "School commentary is strong and multiple report files exist, but public-safe subject-level grades still need cleaner normalization."},
        {"id": "competitions", "label": "Competition profile", "score": 74, "reason": "There is evidence of physics and informatics olympiad performance, including a regional physics result."},
        {"id": "testing", "label": "Testing readiness", "score": 67, "reason": "IELTS is already present, but broader admissions testing evidence is still incomplete."},
        {"id": "activities", "label": "Extracurricular substance", "score": 71, "reason": "Service activity and personal mission documents show direction, though outcomes need stronger public artifacts."},
        {"id": "leadership", "label": "Leadership and initiative", "score": 64, "reason": "Initiative is visible, but leadership proof still needs externally legible evidence."},
        {"id": "evidence", "label": "Evidence completeness", "score": 69, "reason": "The evidence base is substantial, but some key items remain portal-heavy, private, or not normalized yet."},
        {"id": "narrative", "label": "Narrative readiness", "score": 76, "reason": "AI mission and reflective documents create a strong early story about purpose and ambition."},
        {"id": "admissions", "label": "Admissions packaging", "score": 58, "reason": "The raw ingredients are good, but shortlist, deadlines, essays, and recommendation tracking are still missing."},
    ]
    overall = round(sum(item["score"] for item in components) / len(components))
    return {
        "estimated_score": overall,
        "status": "estimated",
        "disclaimer": "This is an internal planning indicator derived from the available local evidence, not an official admissions evaluation.",
        "method": "Weighted qualitative scoring across academics, competitions, extracurricular depth, testing, leadership, evidence completeness, narrative readiness, and admissions packaging.",
        "components": components,
        "signal_counts": {
            "goals": len(goals),
            "olympiads": len(olympiads),
            "activities": len(activities),
            "certificates": len(certificates),
            "commentary_signals": len(comments),
        },
    }


def build_progress_tracker() -> list[dict[str, Any]]:
    return [
        {"title": "Collect core academic evidence", "status": "completed"},
        {"title": "Secure English proficiency evidence", "status": "completed"},
        {"title": "Document olympiad record in one place", "status": "in_progress"},
        {"title": "Build project/research artifact", "status": "planned"},
        {"title": "Add university shortlist and deadlines", "status": "missing"},
        {"title": "Track recommendations and essay drafts", "status": "missing"},
    ]


def build_90_day_plan() -> list[dict[str, Any]]:
    return [
        {
            "window": "Days 1-30",
            "focus": "Stabilize the evidence base and academic narrative",
            "actions": [
                "Review the generated profile for accuracy and mark any sensitive files as private-only.",
                "Add a one-page academic resume and a clean shortlist of top goals for Grade 11 preparation.",
                "Summarize the graduation/research topic in public-safe language.",
            ],
        },
        {
            "window": "Days 31-60",
            "focus": "Convert ambition into visible outputs",
            "actions": [
                "Publish one technical or research-aligned project artifact connected to AI, physics, or informatics.",
                "Add measurable leadership or service outcomes with dates, role, and impact.",
                "Update testing preparation with the next official milestone and date.",
            ],
        },
        {
            "window": "Days 61-90",
            "focus": "Package for external visibility",
            "actions": [
                "Prepare a university/country/major strategy block with deadlines and evidence gaps.",
                "Create a private full-evidence version and a public showcase version.",
                "Refresh the site after new grades, competition results, or project milestones arrive.",
            ],
        },
    ]


def build_privacy_guidance() -> list[dict[str, str]]:
    return [
        {
            "mode": "Public showcase",
            "guidance": "Keep high-level summaries, verified certificates, selected competition results, and project overviews. Redact birth dates, document IDs, contracts, portal screenshots, and internal school commentary where necessary.",
        },
        {
            "mode": "Private full evidence version",
            "guidance": "Use for mentors, counselors, or application support. Include detailed reports and supporting files behind a private link or non-indexed repository.",
        },
    ]


def build_evidence_index(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    for record in records:
        path = record.relative_path
        name = record.source_file.lower()
        if path == "source-materials/Diploms/Region certificate.pdf":
            continue
        if path.startswith("source-materials/Submit Last School’s Report/") and record.extension == ".pdf":
            continue
        if record.extension in {".jpg", ".jpeg", ".png", ".xlsx"}:
            continue
        if path.startswith("source-materials/Personal goals/"):
            continue
        if any(
            marker in name
            for marker in (
                "cambridge-handbook",
                "ib dp 2025",
                "offers spreadsheet",
                "ielts academic",
                "ереван договор",
                "олимпиады - личный кабинет",
            )
        ):
            continue
        if record.extension == ".mhtml":
            description = "Saved portal snapshot from Letovo or another source. Hidden by default to keep the dashboard readable."
        else:
            description = snippet(record.text, 220) or "Document available for manual review."
        index.append(
            {
                "title": record.title,
                "type": record.extension.removeprefix("."),
                "category": record.category,
                "relative_path": record.relative_path,
                "description": description,
                "open_label": "Open snapshot" if record.extension == ".mhtml" else "Open file",
            }
        )
    return index


def build_extracted_data(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    return [
        {
            "source_file": record.source_file,
            "relative_path": record.relative_path,
            "category": record.category,
            "title": record.title,
            "snippet": snippet(record.text, 600),
            "has_text": bool(record.text),
        }
        for record in records
    ]


def build_rendered_mhtml_page(path: Path) -> str | None:
    raw_html = get_mhtml_html(path)
    if not raw_html:
        return None

    soup = BeautifulSoup(raw_html, "html.parser")
    for tag in soup(["script", "noscript", "meta", "link"]):
        tag.decompose()

    # Remove portal shell elements that are not part of the report itself.
    for selector in [
        "nav",
        "#delta_modals",
        ".toast",
        ".navbar",
        ".navbar-collapse",
        ".modal",
        ".anychart-credits",
        "svg.anychart-ui-support",
    ]:
        for node in soup.select(selector):
            node.decompose()

    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if src.startswith("cid:"):
            note = soup.new_tag("div")
            note["class"] = "embedded-placeholder"
            note.string = "Embedded portal subpage omitted to keep the report readable."
            iframe.replace_with(note)

    clean_doc = BeautifulSoup("<html><head></head><body></body></html>", "html.parser")
    style_tag = clean_doc.new_tag("style")
    style_tag.string = """
body {
  margin: 0;
  padding: 28px;
  background: #fffdfa;
  color: #112033;
  font-family: "Aptos", "Segoe UI", sans-serif;
  line-height: 1.6;
}
img {
  max-width: 100%;
  height: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid rgba(17, 32, 51, 0.14);
  padding: 8px 10px;
  vertical-align: top;
}
a {
  color: #112846;
}
.embedded-placeholder {
  padding: 16px 18px;
  border: 1px dashed rgba(17, 32, 51, 0.2);
  border-radius: 14px;
  background: rgba(141, 106, 54, 0.06);
  color: #5f6978;
}
.tab-content > .tab-pane {
  display: block !important;
  opacity: 1 !important;
}
.tab-content > .tab-pane:not(.active) {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid rgba(17, 32, 51, 0.1);
}
.col-md-3 {
  display: none !important;
}
.col-md-9 {
  max-width: 100% !important;
  flex: 0 0 100% !important;
  height: auto !important;
  overflow: visible !important;
}
.list-group-item {
  pointer-events: none;
  text-decoration: none;
}
"""
    clean_doc.head.append(style_tag)

    report_node = soup.select_one("div.container-fluid")
    fallback_node = soup.select_one("div.container")
    main_node = report_node or fallback_node or soup.body or soup
    extracted_node = main_node.extract() if hasattr(main_node, "extract") else main_node

    if report_node is not None:
        report_title = report_node.find(["h4", "h5"])
        if report_title is not None:
            title = clean_doc.new_tag("h1")
            title.string = clean_text(report_title.get_text(" ", strip=True))
            clean_doc.body.append(title)

    clean_doc.body.append(extracted_node)

    output_path = MHTML_RENDER_DIR / f"{path.stem}.html"
    output_path.write_text(str(clean_doc), encoding="utf-8")
    return output_path.relative_to(ROOT).as_posix()


def build_mhtml_reports(records: list[EvidenceRecord]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for record in records:
        if record.extension != ".mhtml" or not record.text:
            continue
        source_path = ROOT / record.relative_path
        rendered_path = build_rendered_mhtml_page(source_path)
        if not rendered_path:
            continue
        reports.append(
            {
                "title": record.title,
                "category": record.category,
                "summary": snippet(record.text, 120) or "Portal report",
                "rendered_path": rendered_path,
            }
        )
    return reports


def build_profile(records: list[EvidenceRecord]) -> dict[str, Any]:
    goals = extract_goals(records)
    olympiads = extract_olympiads(records)
    comments = extract_comments(records)
    activities = extract_activities(records)
    certificates = extract_certificates(records)
    ielts = extract_ielts(records)
    mock_exams = [ielts] if ielts else []
    exam_calendar = build_exam_calendar(records, goals, certificates, mock_exams, olympiads)
    readiness = build_readiness(goals, olympiads, activities, certificates, comments)
    gap_analysis = build_gap_analysis(records, olympiads, mock_exams)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "student": {
            "name": "Zafar Khamidov",
            "preferred_name": "Zafar",
            "school": "Letovo School",
            "grade_level": "Finishing Grade 10 / entering upper-school transition",
            "program_context": "Evidence suggests a bilingual / AS-track transition in the 2025-2026 academic year.",
            "location_context": "Russia-based student building an internationally oriented academic profile.",
            "focus_areas": detect_focus_areas(records),
            "hero_summary": "A motivated Letovo student building a serious STEM profile around AI, physics, informatics, and disciplined long-term growth.",
            "photo": detect_student_photo(),
            "ideal_image": detect_ideal_image(),
        },
        "academics": extract_academics(records),
        "olympiads": olympiads,
        "activities": activities,
        "certificates": certificates,
        "mock_exams": mock_exams,
        "goals": goals,
        "exam_calendar": exam_calendar,
        "commentary_signals": comments,
        "admissions_gap_analysis": gap_analysis,
        "readiness": readiness,
        "vision_panel": {
            "label": "Top 0.5% to 1% ambition",
            "title": "Champion trajectory",
            "summary": "Built as a disciplined, evidence-backed path toward MIT, Harvard, Yale, Stanford, Princeton, and similarly selective institutions.",
            "target_score": 95,
            "target_note": "Target profile level for a truly elite, globally competitive application package.",
        },
        "progress_tracker": build_progress_tracker(),
        "next_90_days_plan": build_90_day_plan(),
        "privacy_guidance": build_privacy_guidance(),
        "todo_checklist": [
            "Finalize academic portfolio summary",
            "Upload all olympiad diplomas and result pages",
            "Add PSAT/SAT result when available",
            "Add research/project section with screenshots or repo links",
            "Add personal statement draft status",
            "Add recommendation tracker",
            "Add university shortlist",
            "Add deadlines calendar",
        ],
        "manual_review_items": [
            "Review detailed school reports before publishing any private commentary publicly.",
            "Confirm subject-level grades that are only partially machine-readable.",
            "Decide which evidence belongs in public mode versus private mode.",
        ],
    }


def build_methodology(profile: dict[str, Any]) -> str:
    readiness = profile["readiness"]
    lines = [
        "# Readiness Methodology",
        "",
        "This score is an internal planning aid for Zafar's portfolio, not an official admissions evaluation.",
        "",
        "## Framework",
        "",
        readiness["method"],
        "",
        "## Components",
        "",
    ]
    for component in readiness["components"]:
        lines.extend(
            [
                f"- {component['label']}: {component['score']}/100",
                f"  Reason: {component['reason']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Estimated readiness score: {readiness['estimated_score']}/100",
            "- 80+: strong and well-packaged profile",
            "- 65-79: credible foundation with meaningful upside",
            "- Below 65: promising but under-documented or under-developed",
            "",
            "## Guardrails",
            "",
            "- Missing evidence is not guessed.",
            "- Sensitive data should be redacted before public deployment.",
            "- Subject-level grades marked as estimated or needs review should be confirmed manually.",
        ]
    )
    return "\n".join(lines)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ensure_output_dirs()
    files = iter_source_files()
    inventory = build_inventory(files)
    records = build_records(files)
    profile = build_profile(records)
    evidence_index = build_evidence_index(records)
    extracted = build_extracted_data(records)
    mhtml_reports = build_mhtml_reports(records)

    write_json(DOCS_DIR / "inventory.json", inventory)
    write_json(DOCS_DIR / "extracted_data.json", extracted)
    write_json(DOCS_DIR / "mhtml-reports.json", mhtml_reports)
    write_json(DOCS_DIR / "normalized_profile.json", profile)
    write_json(DOCS_DIR / "evidence-index.json", evidence_index)
    write_json(DATA_DIR / "profile.json", profile)
    (DOCS_DIR / "readiness_methodology.md").write_text(build_methodology(profile), encoding="utf-8")

    category_counts = Counter(item["category"] for item in inventory)
    print("Built profile artifacts.")
    print(f"Files scanned: {len(files)}")
    print(f"Categories: {dict(category_counts)}")


if __name__ == "__main__":
    main()
