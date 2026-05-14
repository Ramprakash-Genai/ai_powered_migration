from pydantic import BaseModel


class MigrationExecutionOutput(BaseModel):
    status: str  # SUCCESS | REJECTED | DENIED
    updated_code: str | None = None
    justification: str | None = None
