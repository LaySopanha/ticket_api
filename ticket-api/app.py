from fastapi import FastAPI, HTTPException
from typing import List
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
import asyncpg
from dotenv import load_dotenv
import os

# Load the enviroment vaiables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

#initialize the FastAPI app
app = FastAPI()

#pydantic model for ticket
class Ticket(BaseModel):
    ticket_code: str
    ticket_number: str
    type: Optional[str] = None
    document_status_code: Optional[str] = None
    owner_pcc: Optional[str] = None
    owner_agent: Optional[str] = None
    agent_issue_pcc: Optional[str] = None
    agent_issue_name: Optional[str] = None
    class_: Optional[str] = None
    pax_name: Optional[str] = None
    itinerary: Optional[str] = None
    ticket_exchange_info: Optional[str] = None
    indicator: Optional[str] = None
    group_name: Optional[str] = None
    issue_date: Optional[date] = None
    currency: Optional[str] = None
    fare: Optional[float] = None
    net_fare: Optional[float] = None
    taxes: Optional[float] = None
    total_fare: Optional[float] = None
    comm: Optional[float] = None
    cancellation_fee: Optional[float] = None
    payable: Optional[float] = None
    amount_used: Optional[float] = None
    booking_date: Optional[date] = None
    booking_signon: Optional[str] = None
    pnr_code: Optional[str] = None
    tour_code: Optional[str] = None
    claim_amount: Optional[float] = None
    date_of_payment: Optional[date] = None
    form_of_payment: Optional[str] = None
    place_of_payment: Optional[str] = None
    remark: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    sold_price: Optional[float] = None

    @field_validator("issue_date", mode="before")
    def parse_issue_date(cls, value):
        """Convert 'DD-MM-YYYY' to datetime.date."""
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%b-%Y").date()
            except ValueError:
                raise ValueError("Invalid date format. Expected format: DD-MMM-YYYY.")
        return value
#database connection 

async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)

#API endpoints
@app.get("/tickets", response_model=List[Ticket])
async def get_tickets():
    """Fetch all tickets."""
    try:
        conn = await get_db_connection()
        rows = await conn.fetch("SELECT * FROM tickets")
        await conn.close()
        return [Ticket(**dict(row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/tickets", response_model=Ticket)
async def create_ticket(ticket: Ticket):
    """Insert a new ticket."""
    conn = await get_db_connection()
    try:

        await conn.execute(
            "INSERT INTO tickets (ticket_code, ticket_number, type, document_status_code, owner_pcc, owner_agent, agent_issue_pcc, agent_issue_name, class_, pax_name, itinerary, ticket_exchange_info, indicator, group_name, issue_date, currency, fare, net_fare, taxes, total_fare, comm, cancellation_fee, payable, amount_used, booking_date, booking_signon, pnr_code, tour_code, claim_amount, date_of_payment, form_of_payment, place_of_payment, remark, phone, email, sold_price) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36) RETURNING *",
            ticket.ticket_code,ticket.ticket_number, ticket.type, ticket.document_status_code, ticket.owner_pcc, ticket.owner_agent, ticket.agent_issue_pcc, ticket.agent_issue_name, ticket.class_, ticket.pax_name, ticket.itinerary, ticket.ticket_exchange_info, ticket.indicator, ticket.group_name, ticket.issue_date, ticket.currency, ticket.fare, ticket.net_fare, ticket.taxes, ticket.total_fare, ticket.comm, ticket.cancellation_fee, ticket.payable, ticket.amount_used, ticket.booking_date, ticket.booking_signon, ticket.pnr_code, ticket.tour_code, ticket.claim_amount, ticket.date_of_payment, ticket.form_of_payment, ticket.place_of_payment, ticket.remark, ticket.phone, ticket.email, ticket.sold_price
        )
        await conn.close()
        return ticket
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=400, detail=str(e))
    
# Fetch tickets by date through the use of issue date 
@app.get("/tickets/{date}", response_model=List[Ticket])
async def get_tickets_by_date(date: str):
    """Fetch tickets by date."""
    try:
        # convert date string to proper format
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        conn = await get_db_connection()
        rows = await conn.fetch("SELECT * FROM tickets WHERE issue_date = $1", parsed_date)
        await conn.close()
        return [Ticket(**dict(row)) for row in rows]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# delete ticket by ticket_id 
@app.delete("/tickets/{ticket_number}")
async def delete_ticket(ticket_number: str):
    """Delete a ticket."""
    conn = await get_db_connection()
    result = await conn.execute("DELETE FROM tickets WHERE ticket_number = $1", ticket_number)
    await conn.close()
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted successfully"}