CREATE TABLE IF NOT EXISTS candidates (
    id SERIAL PRIMARY KEY,
    
    titel TEXT,
    status TEXT,
    datum TIMESTAMPTZ,
    update_datum TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    durchschnittsbewertung NUMERIC(3, 2),
    gerundete_durchschnittsbewertung NUMERIC(3, 2),
    
    stellenbeschreibung TEXT,
    verbesserungsvorschlaege TEXT,
    
    sternebewertung_erklaerung_der_weiteren_schritte NUMERIC(3, 2),
    sternebewertung_zufriedenstellende_reaktion NUMERIC(3, 2),
    sternebewertung_vollstaendigkeit_der_infos NUMERIC(3, 2),
    sternebewertung_zufriedenstellende_antworten NUMERIC(3, 2),
    sternebewertung_angenehme_atmosphaere NUMERIC(3, 2),
    sternebewertung_professionalitaet_des_gespraechs NUMERIC(3, 2),
    sternebewertung_wertschaetzende_behandlung NUMERIC(3, 2),
    sternebewertung_erwartbarkeit_des_prozesses NUMERIC(3, 2),
    sternebewertung_zeitgerechte_zu_oder_absage NUMERIC(3, 2),
    sternebewertung_schnelle_antwort NUMERIC(3, 2),
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);

CREATE INDEX IF NOT EXISTS idx_candidates_datum ON candidates(datum);

COMMENT ON TABLE candidates IS 'Stores candidate feedback and ratings from interviews';

CREATE TABLE IF NOT EXISTS employee (
    id SERIAL PRIMARY KEY,
    
    titel TEXT,
    status TEXT,
    datum TIMESTAMPTZ,
    update_datum TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    durchschnittsbewertung NUMERIC(3, 2),
    gerundete_durchschnittsbewertung NUMERIC(3, 2),
    
    jobbeschreibung TEXT,
    gut_am_arbeitgeber_finde_ich TEXT,
    schlecht_am_arbeitgeber_finde_ich TEXT,
    verbesserungsvorschlaege TEXT,
    
    sternebewertung_arbeitsatmosphaere NUMERIC(3, 2),
    sternebewertung_image NUMERIC(3, 2),
    sternebewertung_work_life_balance NUMERIC(3, 2),
    sternebewertung_karriere_weiterbildung NUMERIC(3, 2),
    sternebewertung_gehalt_sozialleistungen NUMERIC(3, 2),
    sternebewertung_kollegenzusammenhalt NUMERIC(3, 2),
    sternebewertung_umwelt_sozialbewusstsein NUMERIC(3, 2),
    sternebewertung_vorgesetztenverhalten NUMERIC(3, 2),
    sternebewertung_kommunikation NUMERIC(3, 2),
    sternebewertung_interessante_aufgaben NUMERIC(3, 2),
    sternebewertung_umgang_mit_aelteren_kollegen NUMERIC(3, 2),
    sternebewertung_arbeitsbedingungen NUMERIC(3, 2),
    sternebewertung_gleichberechtigung NUMERIC(3, 2),
    
    arbeitsatmosphaere TEXT,
    image TEXT,
    work_life_balance TEXT,
    karriere_weiterbildung TEXT,
    gehalt_sozialleistungen TEXT,
    kollegenzusammenhalt TEXT,
    umwelt_sozialbewusstsein TEXT,
    vorgesetztenverhalten TEXT,
    kommunikation TEXT,
    interessante_aufgaben TEXT,
    umgang_mit_aelteren_kollegen TEXT,
    arbeitsbedingungen TEXT,
    gleichberechtigung TEXT,

    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_employee_status ON employee(status);

CREATE INDEX IF NOT EXISTS idx_employee_datum ON employee(datum);

COMMENT ON TABLE employee IS 'Stores employee feedback and ratings about their workplace experience';

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);

COMMENT ON TABLE companies IS 'Stores company information that candidates and employees belong to';

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

ALTER TABLE companies
ADD COLUMN IF NOT EXISTS ticker TEXT;

ALTER TABLE companies
ADD COLUMN IF NOT EXISTS isin TEXT;

ALTER TABLE companies
ADD COLUMN IF NOT EXISTS sector TEXT;

ALTER TABLE companies
ADD COLUMN IF NOT EXISTS peer_group TEXT;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_companies_peer_group'
    ) THEN
        ALTER TABLE companies
        ADD CONSTRAINT chk_companies_peer_group
        CHECK (
            peer_group IS NULL
            OR peer_group IN (
                'Börsennotiert DE',
                'Börsennotiert Ausland',
                'Nicht börsennotiert',
                'Demo'
            )
        );
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_companies_peer_group ON companies(peer_group);

COMMENT ON COLUMN companies.ticker IS
    'Börsenticker in Yahoo-Finance-Notation (z. B. TKA.DE für Xetra, 9432.T für Tokio). NULL, wenn das Unternehmen nicht börsennotiert ist oder kein verifizierter Ticker vorliegt.';

COMMENT ON COLUMN companies.isin IS
    'International Securities Identification Number (ISIN) der Aktie, z. B. DE0007500001. NULL, wenn nicht börsennotiert oder nicht verifiziert.';

COMMENT ON COLUMN companies.sector IS
    'Branche des Unternehmens als deutscher Freitext (z. B. Stahl/Industrie, Energie, Gasnetz, IT-Dienstleistung, Software, Halbleiter, Telekommunikation, Medizintechnik, Biotechnologie, Hochschule).';

COMMENT ON COLUMN companies.peer_group IS
    'Vergleichsgruppe für Zyklus 2 (Abgleich von Bewertungsänderungen mit Kursdaten). Erlaubte Werte: ''Börsennotiert DE'' (deutsche Börse, Kursdaten verfügbar), ''Börsennotiert Ausland'' (ausländische Börse bzw. börsennotierte Muttergesellschaft), ''Nicht börsennotiert'' (keine Kursdaten), ''Demo'' (synthetische Demo-Unternehmen, von allen Analysen ausgeschlossen).';
