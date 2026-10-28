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
