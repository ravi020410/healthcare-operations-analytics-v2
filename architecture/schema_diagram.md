# Data Model — Hospital Operations Analytics

Star-schema layout: `admissions` is the central fact table. Rendered natively by
GitHub — no image export needed.

The diagram reflects the intended relational model. The local SQLite mirror is built
from the canonical cleaned admissions CSV plus raw supporting extracts; its CSV key
relationships are checked by `scripts/validate_project.py`.

```mermaid
erDiagram
    DEPARTMENTS ||--o{ DOCTORS : employs
    DEPARTMENTS ||--o{ ADMISSIONS : hosts
    DOCTORS ||--o{ ADMISSIONS : treats
    PATIENTS ||--o{ ADMISSIONS : has
    ADMISSIONS ||--o| BILLING : generates
    ADMISSIONS ||--o{ TREATMENTS : includes
    ADMISSIONS ||--o| SATISFACTION_SURVEYS : receives

    DEPARTMENTS {
        smallint department_id PK
        text department
        smallint staffed_beds
    }
    DOCTORS {
        int doctor_id PK
        text doctor_name
        smallint department_id FK
        text employment_status
        smallint years_experience
    }
    PATIENTS {
        int patient_id PK
        text patient_name
        date date_of_birth
        text gender
        text state "2% NULL"
        text insurance_type "4% NULL"
    }
    ADMISSIONS {
        int admission_id PK
        int patient_id FK
        int doctor_id FK
        smallint department_id FK
        timestamp admission_date
        timestamp discharge_date
        text admission_type
        numeric severity_score
        numeric length_of_stay_days
        int wait_minutes
        numeric discharge_efficiency
        smallint readmitted_30d
    }
    BILLING {
        int billing_id PK
        int admission_id FK
        numeric gross_charge
        numeric insurance_payment
        numeric patient_out_of_pocket
        numeric direct_operating_cost
    }
    TREATMENTS {
        int treatment_id PK
        int admission_id FK
        text procedure
        numeric treatment_cost
    }
    SATISFACTION_SURVEYS {
        int survey_id PK
        int admission_id FK
        numeric satisfaction_score
        smallint response_days_after_discharge
    }
```

**Why this shape:** `admissions` is deliberately the hub, not `patients`, because
the unit of analysis for every operational question in this project (LOS, wait time,
readmission, discharge efficiency) is a single hospital stay, not a person. A patient
with 4 admissions across the 3-year window contributes 4 independent rows to every
downstream query — which is the correct behavior for operational analytics, but worth
stating explicitly since it's a modeling decision, not a default.
