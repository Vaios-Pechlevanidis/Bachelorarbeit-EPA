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
