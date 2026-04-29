from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import sqlalchemy as sa
from sqlalchemy import Engine, create_engine

from civicgrants.compliance_calendar import build_compliance_calendar
from civicgrants.opportunity_triage import OpportunityTriage, triage_opportunity


metadata = sa.MetaData()

grant_opportunity_records = sa.Table(
    "grant_opportunity_records",
    metadata,
    sa.Column("opportunity_key", sa.String(255), primary_key=True),
    sa.Column("opportunity_title", sa.String(500), nullable=False),
    sa.Column("funding_area", sa.String(255), nullable=False),
    sa.Column("deadline", sa.String(120), nullable=False),
    sa.Column("priority", sa.String(120), nullable=False),
    sa.Column("recommended_owner", sa.String(255), nullable=False),
    sa.Column("triage_notes", sa.JSON(), nullable=False),
    sa.Column("disclaimer", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    schema="civicgrants",
)

grant_compliance_records = sa.Table(
    "grant_compliance_records",
    metadata,
    sa.Column("compliance_id", sa.String(36), primary_key=True),
    sa.Column("award_name", sa.String(500), nullable=False),
    sa.Column("reporting_frequency", sa.String(120), nullable=False),
    sa.Column("calendar_items", sa.JSON(), nullable=False),
    sa.Column("staff_note", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    schema="civicgrants",
)


@dataclass(frozen=True)
class StoredComplianceCalendar:
    compliance_id: str
    award_name: str
    reporting_frequency: str
    calendar_items: tuple[str, ...]
    staff_note: str
    created_at: datetime


class GrantRecordsRepository:
    """SQLAlchemy-backed grant opportunity and compliance-calendar records."""

    def __init__(self, *, db_url: str | None = None, engine: Engine | None = None, seed_defaults: bool = True) -> None:
        base_engine = engine or create_engine(db_url or "sqlite+pysqlite:///:memory:", future=True)
        if base_engine.dialect.name == "sqlite":
            self.engine = base_engine.execution_options(schema_translate_map={"civicgrants": None})
        else:
            self.engine = base_engine
            with self.engine.begin() as connection:
                connection.execute(sa.text("CREATE SCHEMA IF NOT EXISTS civicgrants"))
        metadata.create_all(self.engine)
        if seed_defaults:
            self.seed_sample_opportunities()

    def seed_sample_opportunities(self) -> None:
        now = datetime.now(UTC)
        samples = (
            {
                "opportunity_key": "water-infrastructure-grant",
                "opportunity_title": "Water infrastructure grant",
                "funding_area": "stormwater",
                "deadline": "2026-06-01",
            },
            {
                "opportunity_key": "parks-access-grant",
                "opportunity_title": "Parks access grant",
                "funding_area": "parks and trails",
                "deadline": "confirm in source notice",
            },
        )
        with self.engine.begin() as connection:
            for sample in samples:
                exists = connection.execute(
                    sa.select(grant_opportunity_records.c.opportunity_key).where(
                        grant_opportunity_records.c.opportunity_key == sample["opportunity_key"]
                    )
                ).first()
                if exists is not None:
                    continue
                triage = triage_opportunity(
                    opportunity_title=sample["opportunity_title"],
                    funding_area=sample["funding_area"],
                    deadline=sample["deadline"],
                )
                connection.execute(
                    grant_opportunity_records.insert().values(
                        opportunity_key=sample["opportunity_key"],
                        opportunity_title=triage.opportunity_title,
                        funding_area=triage.funding_area,
                        deadline=sample["deadline"],
                        priority=triage.priority,
                        recommended_owner=triage.recommended_owner,
                        triage_notes=list(triage.triage_notes),
                        disclaimer=triage.disclaimer,
                        created_at=now,
                        updated_at=now,
                    )
                )

    def triage_opportunity(
        self, *, opportunity_title: str, funding_area: str, deadline: str = ""
    ) -> OpportunityTriage:
        normalized_title = _normalize_key(opportunity_title)
        normalized_area = funding_area.strip().casefold()
        with self.engine.begin() as connection:
            rows = connection.execute(sa.select(grant_opportunity_records)).mappings().all()
        for row in rows:
            if row["opportunity_key"] == normalized_title or (
                normalized_title and normalized_title in _normalize_key(row["opportunity_title"])
            ):
                return _row_to_opportunity_triage(row, fallback_title=opportunity_title)
            if normalized_area and normalized_area in row["funding_area"].casefold():
                return _row_to_opportunity_triage(row, fallback_title=opportunity_title)
        return triage_opportunity(
            opportunity_title=opportunity_title,
            funding_area=funding_area,
            deadline=deadline,
        )

    def create_compliance_calendar(
        self, *, award_name: str, reporting_frequency: str = "quarterly"
    ) -> StoredComplianceCalendar:
        calendar = build_compliance_calendar(
            award_name=award_name,
            reporting_frequency=reporting_frequency,
        )
        stored = StoredComplianceCalendar(
            compliance_id=str(uuid4()),
            award_name=calendar.award_name,
            reporting_frequency=calendar.reporting_frequency,
            calendar_items=calendar.calendar_items,
            staff_note=calendar.staff_note,
            created_at=datetime.now(UTC),
        )
        with self.engine.begin() as connection:
            connection.execute(
                grant_compliance_records.insert().values(
                    compliance_id=stored.compliance_id,
                    award_name=stored.award_name,
                    reporting_frequency=stored.reporting_frequency,
                    calendar_items=list(stored.calendar_items),
                    staff_note=stored.staff_note,
                    created_at=stored.created_at,
                )
            )
        return stored

    def get_compliance_calendar(self, compliance_id: str) -> StoredComplianceCalendar | None:
        with self.engine.begin() as connection:
            row = connection.execute(
                sa.select(grant_compliance_records).where(
                    grant_compliance_records.c.compliance_id == compliance_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_compliance_calendar(row)


def _normalize_key(value: str) -> str:
    return "-".join(value.strip().casefold().split())


def _row_to_opportunity_triage(row: object, *, fallback_title: str) -> OpportunityTriage:
    data = dict(row)
    return OpportunityTriage(
        opportunity_title=fallback_title.strip() or data["opportunity_title"],
        funding_area=data["funding_area"],
        priority=data["priority"],
        recommended_owner=data["recommended_owner"],
        triage_notes=tuple(data["triage_notes"]),
        disclaimer=data["disclaimer"],
    )


def _row_to_compliance_calendar(row: object) -> StoredComplianceCalendar:
    data = dict(row)
    return StoredComplianceCalendar(
        compliance_id=data["compliance_id"],
        award_name=data["award_name"],
        reporting_frequency=data["reporting_frequency"],
        calendar_items=tuple(data["calendar_items"]),
        staff_note=data["staff_note"],
        created_at=data["created_at"],
    )
