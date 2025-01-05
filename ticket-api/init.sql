-- Create tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    ticket_code VARCHAR(50) NOT NULL,
    ticket_number VARCHAR(50) NOT NULL,
    type VARCHAR(50),
    document_status_code VARCHAR(50),
    owner_pcc VARCHAR(20),
    owner_agent VARCHAR(100),
    agent_issue_pcc VARCHAR(20),
    agent_issue_name VARCHAR(100),
    class_ VARCHAR(20),
    pax_name VARCHAR(100),
    itinerary TEXT,
    ticket_exchange_info TEXT,
    indicator VARCHAR(20),
    group_name VARCHAR(100),
    issue_date DATE,
    currency VARCHAR(10),
    fare NUMERIC(12, 2),
    net_fare NUMERIC(12, 2),
    taxes NUMERIC(12, 2),
    total_fare NUMERIC(12, 2),
    comm NUMERIC(12, 2),
    cancellation_fee NUMERIC(12, 2),
    payable NUMERIC(12, 2),
    amount_used NUMERIC(12, 2),
    booking_date DATE,
    booking_signon VARCHAR(50),
    pnr_code VARCHAR(50),
    tour_code VARCHAR(50),
    claim_amount NUMERIC(12, 2),
    date_of_payment DATE,
    form_of_payment VARCHAR(50),
    place_of_payment VARCHAR(100),
    remark TEXT,
    phone VARCHAR(20),
    email VARCHAR(100),
    sold_price NUMERIC(12, 2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for common searches
CREATE INDEX IF NOT EXISTS idx_ticket_number ON tickets(ticket_number);
CREATE INDEX IF NOT EXISTS idx_pax_name ON tickets(pax_name); 
CREATE INDEX IF NOT EXISTS idx_issue_date ON tickets(issue_date);
CREATE INDEX IF NOT EXISTS idx_agent_issue_pcc ON tickets(agent_issue_pcc);

