ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_companies"
    ON companies FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "service_role_all_companies"
    ON companies FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_candidates"
    ON candidates FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "service_role_all_candidates"
    ON candidates FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

ALTER TABLE employee ENABLE ROW LEVEL SECURITY;

CREATE POLICY "public_read_employee"
    ON employee FOR SELECT
    TO anon, authenticated
    USING (true);

CREATE POLICY "service_role_all_employee"
    ON employee FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
