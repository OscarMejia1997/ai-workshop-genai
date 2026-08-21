from pydantic import BaseModel, Field


class Medication(BaseModel):
    name: str | None = None
    concentration: str | None = None
    pharmaceutical_form: str | None = None
    dose_per_administration: str | None = None
    frequency: str | None = None
    duration: str | None = None
    prescribed_quantity: str | None = None
    instructions: str | None = None


class Physician(BaseModel):
    name: str | None = None
    license_number: str | None = None
    specialty: str | None = None


class Prescription(BaseModel):
    document_type: str | None = None
    recipe_id: str | None = None
    issue_date: str | None = None
    patient: str | None = None
    diagnosis: str | None = None
    medications: list[Medication] = Field(default_factory=list)
    physician: Physician | None = None
    missing_fields: list[str] = Field(default_factory=list)
    ambiguous_fields: list[str] = Field(default_factory=list)
    extraction_issues: list[str] = Field(default_factory=list)
    requires_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
