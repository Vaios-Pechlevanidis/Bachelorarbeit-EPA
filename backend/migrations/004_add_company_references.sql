ALTER TABLE candidates
ADD COLUMN IF NOT EXISTS company_id INTEGER;

ALTER TABLE candidates
ADD CONSTRAINT fk_candidates_company
FOREIGN KEY (company_id) REFERENCES companies(id)
ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_candidates_company_id ON candidates(company_id);

ALTER TABLE employee
ADD COLUMN IF NOT EXISTS company_id INTEGER;

ALTER TABLE employee
ADD CONSTRAINT fk_employee_company
FOREIGN KEY (company_id) REFERENCES companies(id)
ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_employee_company_id ON employee(company_id);
