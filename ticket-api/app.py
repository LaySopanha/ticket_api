from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from typing import List
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator
import asyncpg
import logging
from dotenv import load_dotenv
import os

# Load the enviroment vaiables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

#App lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    #init connection pool
    app.state.pool = await asyncpg.create_pool(DATABASE_URL)
    yield # app run during this period
    await app.state.pool.close() # app close
    
#initialize the FastAPI app with the lifespan
app = FastAPI(lifespan=lifespan)

#dependency to get a database connection
async def get_db_connection():
    try:
        # check if the pool is init
        if not app.state.pool:
            app.state.pool = await asyncpg.create_pool(
                DATABASE_URL,
                min_size=5,
                max_size=20,
                timeout=60.0,
                )
        return app.state.pool
    except Exception as e:
        # log for error
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")

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
        if value is None or isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%d-%b-%Y").date()
            except ValueError:
                raise ValueError("Invalid date format. Expected format: DD-MMM-YYYY.")
        return value
    
class TicketSearchResult(BaseModel):
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

#API endpoints
#Health check 
@app.get("/health", summary="Health check", description="Check the health status of the API.")
async def health_check():
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Service Unavailable.")

# get all ticket endpoint 
@app.get("/tickets", response_model=List[Ticket], summary="Retrieve all tickets", description="Fetch all tickets from the database.")
async def get_tickets():
    """Fetch all tickets."""
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tickets")
        return [Ticket(**dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")

#insert ticket endpoint
@app.post("/tickets", response_model=Ticket)
async def create_ticket(ticket: Ticket):
    """Insert a new ticket."""
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO tickets (ticket_code, ticket_number, type, document_status_code, owner_pcc, owner_agent, agent_issue_pcc, agent_issue_name, class_, pax_name, itinerary, ticket_exchange_info, indicator, group_name, issue_date, currency, fare, net_fare, taxes, total_fare, comm, cancellation_fee, payable, amount_used, booking_date, booking_signon, pnr_code, tour_code, claim_amount, date_of_payment, form_of_payment, place_of_payment, remark, phone, email, sold_price) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36) RETURNING *",
                ticket.ticket_code,ticket.ticket_number, ticket.type, ticket.document_status_code, ticket.owner_pcc, ticket.owner_agent, ticket.agent_issue_pcc, ticket.agent_issue_name, ticket.class_, ticket.pax_name, ticket.itinerary, ticket.ticket_exchange_info, ticket.indicator, ticket.group_name, ticket.issue_date, ticket.currency, ticket.fare, ticket.net_fare, ticket.taxes, ticket.total_fare, ticket.comm, ticket.cancellation_fee, ticket.payable, ticket.amount_used, ticket.booking_date, ticket.booking_signon, ticket.pnr_code, ticket.tour_code, ticket.claim_amount, ticket.date_of_payment, ticket.form_of_payment, ticket.place_of_payment, ticket.remark, ticket.phone, ticket.email, ticket.sold_price
            )
        return ticket
    except Exception as e:
        logger.error(f"Databse error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid data provided.")
    
# A search functionality to search for tickets by multiple fields param
@app.get("/tickets/search", response_model=List[TicketSearchResult], summary= "search tickets", description="Search for tickets by ticket number or pax name or agent issue pcc.")
async def search_tickets(ticket_number: Optional[str]=None, pax_name: Optional[str]=None, agent_issue_pcc: Optional[str] = None):
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        query = "SELECT * FROM tickets WHERE 1=1"
        params = []
        if ticket_number:
            query += " AND ticket_number = $1"
            params.append(ticket_number)
        if pax_name:
            query += f" AND pax_name ILIKE ${len(params) + 1}"
            params.append(f"%{pax_name}%")
        if agent_issue_pcc:
            query += f" AND agent_issue_pcc = ${len(params) + 1}"
            params.append(agent_issue_pcc)   
             
        rows = await conn.fetch(query, *params)
    return [TicketSearchResult(**dict(row)) for row in rows]

# Fetch tickets by date through the use of issue date 
@app.get("/tickets/{date}", response_model=List[Ticket], summary="Retrieve tickets by date", description="Fetch tickets by issue date.")
async def get_tickets_by_date(date: str):
    """Fetch tickets by date."""
    try:
        # convert date string to proper format
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tickets WHERE issue_date = $1", parsed_date)
        return [Ticket(**dict(row)) for row in rows]
    except ValueError:
        logger.error(f"Invalid date format. Use YYYY-MM-DD")
        raise HTTPException(status_code=400, detail="Invalid date format. Use DD-MM-YYYY")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error.")



# delete ticket by ticket_id 
@app.delete("/tickets/{ticket_number}",summary="Delete a ticket", description="Delete a ticket by ticket number.")
async def delete_ticket(ticket_number: str):
    """Delete a ticket."""
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM tickets WHERE ticket_number = $1", ticket_number)
    if result == "DELETE 0":
        logger.error(f"Ticket not found: {ticket_number}")
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": "Ticket deleted successfully."}