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

staff_review_queue_records = sa.Table(
    "staff_review_queue_records",
    metadata,
    sa.Column("review_id", sa.String(36), primary_key=True),
    sa.Column("grant_id", sa.String(255), nullable=True),
    sa.Column("opportunity_title", sa.String(500), nullable=False),
    sa.Column("status", sa.String(120), nullable=False),
    sa.Column("reason", sa.Text(), nullable=False),
    sa.Column("assigned_to", sa.String(255), nullable=True),
    sa.Column("resolution", sa.Text(), nullable=True),
    sa.Column("created_by", sa.String(120), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("visibility", sa.String(120), nullable=False),
    schema="civicgrants",
)

OPEN_STAFF_REVIEW_STATUSES = {"open", "in_review"}
RESOLVED_STAFF_REVIEW_STATUSES = {"resolved", "closed"}
STAFF_REVIEW_STATUSES = OPEN_STAFF_REVIEW_STATUSES | RESOLVED_STAFF_REVIEW_STATUSES


@dataclass(frozen=True)
class StoredComplianceCalendar:
    compliance_id: str
    award_name: str
    reporting_frequency: str
    calendar_items: tuple[str, ...]
    staff_note: str
    created_at: datetime


@dataclass(frozen=True)
class StaffReviewQueueItem:
    review_id: str
    grant_id: str | None
    opportunity_title: str
    status: str
    reason: str
    assigned_to: str | None
    resolution: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime
    visibility: str = "staff_only"


@dataclass(frozen=True)
class StaffReviewSummary:
    total_items: int
    by_status: dict[str, int]
    open_items: int
    generated_at: datetime
    visibility: str = "staff_only"


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

    def create_staff_review_queue_item(
        self,
        *,
        opportunity_title: str,
        reason: str,
        grant_id: str | None = None,
        created_by: str = "staff",
    ) -> StaffReviewQueueItem:
        now = datetime.now(UTC)
        item = StaffReviewQueueItem(
            review_id=str(uuid4()),
            grant_id=grant_id,
            opportunity_title=opportunity_title.strip() or "Untitled grant opportunity",
            status="open",
            reason=reason.strip() or "Grant support output requires staff review.",
            assigned_to=None,
            resolution=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )
        with self.engine.begin() as connection:
            connection.execute(staff_review_queue_records.insert().values(**_staff_queue_values(item)))
        return item

    def list_staff_review_queue_items(self, *, status: str | None = None) -> tuple[StaffReviewQueueItem, ...]:
        with self.engine.begin() as connection:
            statement = sa.select(staff_review_queue_records).order_by(
                staff_review_queue_records.c.created_at
            )
            if status is not None:
                statement = statement.where(staff_review_queue_records.c.status == status)
            rows = connection.execute(statement).mappings().all()
        return tuple(_row_to_staff_queue_item(row) for row in rows)

    def update_staff_review_queue_item(
        self,
        *,
        review_id: str,
        status: str,
        assigned_to: str | None = None,
        resolution: str | None = None,
    ) -> StaffReviewQueueItem | None:
        if status not in STAFF_REVIEW_STATUSES:
            raise ValueError("status must be one of: closed, in_review, open, resolved.")
        if status in RESOLVED_STAFF_REVIEW_STATUSES and not resolution:
            raise ValueError("resolution is required when resolving or closing a staff review item.")
        current = self.get_staff_review_queue_item(review_id)
        if current is None:
            return None
        updated = StaffReviewQueueItem(
            review_id=current.review_id,
            grant_id=current.grant_id,
            opportunity_title=current.opportunity_title,
            status=status,
            reason=current.reason,
            assigned_to=assigned_to,
            resolution=resolution,
            created_by=current.created_by,
            created_at=current.created_at,
            updated_at=datetime.now(UTC),
        )
        with self.engine.begin() as connection:
            connection.execute(
                staff_review_queue_records.update()
                .where(staff_review_queue_records.c.review_id == review_id)
                .values(**_staff_queue_values(updated))
            )
        return updated

    def get_staff_review_queue_item(self, review_id: str) -> StaffReviewQueueItem | None:
        with self.engine.begin() as connection:
            row = connection.execute(
                sa.select(staff_review_queue_records).where(
                    staff_review_queue_records.c.review_id == review_id
                )
            ).mappings().first()
        if row is None:
            return None
        return _row_to_staff_queue_item(row)

    def staff_review_summary(self) -> StaffReviewSummary:
        items = self.list_staff_review_queue_items()
        by_status = {status: sum(1 for item in items if item.status == status) for status in STAFF_REVIEW_STATUSES}
        return StaffReviewSummary(
            total_items=len(items),
            by_status=by_status,
            open_items=sum(1 for item in items if item.status in OPEN_STAFF_REVIEW_STATUSES),
            generated_at=datetime.now(UTC),
        )


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


def _staff_queue_values(item: StaffReviewQueueItem) -> dict[str, object]:
    return {
        "review_id": item.review_id,
        "grant_id": item.grant_id,
        "opportunity_title": item.opportunity_title,
        "status": item.status,
        "reason": item.reason,
        "assigned_to": item.assigned_to,
        "resolution": item.resolution,
        "created_by": item.created_by,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "visibility": item.visibility,
    }


def _row_to_staff_queue_item(row: object) -> StaffReviewQueueItem:
    data = dict(row)
    return StaffReviewQueueItem(
        review_id=data["review_id"],
        grant_id=data["grant_id"],
        opportunity_title=data["opportunity_title"],
        status=data["status"],
        reason=data["reason"],
        assigned_to=data["assigned_to"],
        resolution=data["resolution"],
        created_by=data["created_by"],
        created_at=data["created_at"],
        updated_at=data["updated_at"],
        visibility=data["visibility"],
    )
