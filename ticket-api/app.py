from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import date, datetime
import time
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
from fastapi.security import APIKeyHeader
from fastapi import Security, Depends, Query
import asyncpg
import logging
from fastapi.responses import JSONResponse
import uuid
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    API_KEY: str
    ENVIRONMENT: str = "development"
    ALLOWED_ORIGINS: list[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @classmethod
    def validate_settings(cls, values: dict):
        if not values.get("DATABASE_URL"):
            raise ValueError("DATABASE_URL is required in the .env file")
        return values

settings = Settings()

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

#set rate limiting
requests_store = defaultdict(list)
RATE_LIMIT = 100 #requests
TIME_WINDOW = 60 #seconds

# logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("ticket-api")

#App lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        #init connection pool
        app.state.pool = await asyncpg.create_pool(settings.DATABASE_URL)
        yield # app run during this period
    except Exception as e:
        logger.error(f"Failed to connect to the database: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to connect to the database")
    finally:
        if hasattr(app.state, "pool") and app.state.pool:
            await app.state.pool.close() # app close    
      
#initialize the FastAPI app with the lifespan
app = FastAPI(lifespan=lifespan)

#add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#dependency to get a database connection
async def get_db_connection():
    try:
        # check if the pool is init
        if not app.state.pool:
            app.state.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=5,
                max_size=20,
                timeout=60.0,
                )
        return app.state.pool
    except asyncpg.PoolTimeoutError:
        # log for error
        logger.error("Database connection timeout.")
        raise HTTPException(status_code=500, detail="Database connection timeout.")
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
                raise ValueError("Invalid date format. Expected format: YYYY-MM-DD.")
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


    
#for middleware
@app.middleware("http")
#add request logging middleware
async def log_requests(request: Request, call_next):
    """Log all incoming requests.""" 
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Duration: {duration:.3f}s"
    )
    return response
#add rate limiting middleware
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    #clean old requests
    requests_store[client_ip] = [req_time for req_time in requests_store[client_ip]
                                 if now - req_time < TIME_WINDOW]
    if len(requests_store[client_ip]) >= RATE_LIMIT:
        logger.error(f"Too many requests")
        raise HTTPException(status_code=429, detail="Too many requests")
    requests_store[client_ip].append(now)
    response = await call_next(request)
    return response


#API endpoints
#Health check 
@app.get("/health", summary="Health check", description="Check the health status of the API.")
async def health_check():
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            # "timestamp": datetime.now(datetime.UTC),
            "environment": settings.ENVIRONMENT,
            "database": settings.DATABASE_URL
            }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service Unavailable.")
    
# def get_version_info():
#     """Get automatic version and update information.""" 
#     try:
#         # Get version from git tag
#         version = subprocess.check_output(
#             ['git', 'describe', '--tags', '--abbrev=0']
#         ).decode('ascii').strip()
        
#         # Get last modified date from git
#         last_updated = subprocess.check_output(
#             ['git', 'log', '-1', '--format=%cd', '--date=iso']
#         ).decode('ascii').strip()
        
#         return {
#             "version": version,
#             "last_updated": last_updated
#         }
#     except Exception as e:
#         logger.warning(f"Could not get git info: {e}")
#         # Fallback to package version if git fails
#         return {
#             "version": "development",
#             "last_updated": datetime.now().isoformat()
#         }
# #endpoint for version
# @app.get("/version", summary="Version Info", description="Get API version information.")
# async def version():
#     version_info = get_version_info()
#     return {
#         "version": version_info["version"],
#         "environment": settings.ENVIRONMENT,
#         "last_updated": version_info["last_updated"]
#     }
#end point for checking the stats
@app.get("/tickets/stats", dependencies=[Depends(verify_api_key)], summary="Get ticket stats", description="End point for checking the stats of the tickets.")
async def get_ticket_stats(
    start_date: Optional[date] = Query(None, description="Format: YYYY-MM-DD"),
    end_date: Optional[date] = Query(None, description="Format: YYYY-MM-DD")
):
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            query = """
            SELECT 
                COUNT(*) as total_tickets,
                SUM(fare) as total_fare,
                AVG(fare) as average_fare,
                COUNT(DISTINCT agent_issue_pcc) as unique_pccs,
                COUNT(DISTINCT pax_name) as unique_pax,
                MIN(issue_date) as earliest_date,
                MAX(issue_date) as latest_date
            FROM tickets
            WHERE ($1::date is NULL OR issue_date >= $1)
            AND ($2::date IS NULL OR issue_date <= $2)
            """
            stats = await conn.fetchrow(query, start_date, end_date)
            return dict(stats)
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistic")
    
# get all ticket endpoint 
@app.get("/tickets",dependencies=[Depends(verify_api_key)], response_model=List[Ticket], summary="Retrieve all tickets", description="Fetch all tickets from the database with pagination.")
async def get_tickets(
    page: int = Query(default=1, gt=0),
    limit: int = Query(default=10, le=100),
    sort_by: str = Query(default="issue_date", enum=["issue_date", "ticket_number", "pax_name"]),
    order: str = Query(default="asc", enum=["asc", "desc"])
):
    offset = (page - 1) * limit
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            query = f"""
            SELECT * FROM tickets
            ORDER BY {sort_by} {order}
            LIMIT $1 OFFSET $2
            """
            rows = await conn.fetch(query, limit, offset)
        
        # Return only the list of Ticket objects
        return [Ticket(**dict(row)) for row in rows]
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

#insert ticket endpoint
@app.post("/tickets",dependencies=[Depends(verify_api_key)], response_model=Ticket, summary="Create a ticket", description="Insert a new ticket into the database.")
async def create_ticket(ticket: Ticket):
    """Insert a new ticket.""" 
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO tickets (ticket_code, ticket_number, type, document_status_code, owner_pcc, owner_agent, agent_issue_pcc, agent_issue_name, class_, pax_name, itinerary, ticket_exchange_info, indicator, group_name, issue_date, currency, fare, net_fare, taxes, total_fare, comm, cancellation_fee, payable, amount_used, booking_date, booking_signon, pnr_code, tour_code, claim_amount, date_of_payment, form_of_payment, place_of_payment, remark, phone, email, sold_price) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35, $36) RETURNING *",
                ticket.ticket_code,ticket.ticket_number, ticket.type, ticket.document_status_code, ticket.owner_pcc, ticket.owner_agent, ticket.agent_issue_pcc, ticket.agent_issue_name, ticket.class_, ticket.pax_name, ticket.itinerary, ticket.ticket_exchange_info, ticket.indicator, ticket.group_name, ticket.issue_date, ticket.currency, ticket.fare, ticket.net_fare, ticket.taxes, ticket.total_fare, ticket.comm, ticket.cancellation_fee, ticket.payable, ticket.amount_used, ticket.booking_date, ticket.booking_signon, ticket.pnr_code, ticket.tour_code, ticket.claim_amount, ticket.date_of_payment, ticket.form_of_payment, ticket.place_of_payment, ticket.remark, ticket.phone, ticket.email, ticket.sold_price
            )
        logger.info(f"Ticket created: {ticket.ticket_number}")
        return ticket
    except Exception as e:
        logger.error(f"Failed to create ticket: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid data provided.")

#end point for bulk adding of ticket
@app.post("/tickets/bulk", dependencies=[Depends(verify_api_key)], summary="Bulk add tickets", description="Adding tickets in bulk in one request.")
async def create_bulk_tickets(tickets: List[Ticket]):
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            async with conn.transaction():
                create_tickets = []
                for ticket in tickets:
                    result = await conn.fetchrow(
                        """
                        INSERT INTO tickets (
                            ticket_code, ticket_number, type, document_status_code, 
                            owner_pcc, owner_agent, agent_issue_pcc, agent_issue_name,
                            class_, pax_name, itinerary, ticket_exchange_info,
                            indicator, group_name, issue_date, currency,
                            fare, net_fare, taxes, total_fare,
                            comm, cancellation_fee, payable, amount_used,
                            booking_date, booking_signon, pnr_code, tour_code,
                            claim_amount, date_of_payment, form_of_payment,
                            place_of_payment, remark, phone, email, sold_price
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                            $11, $12, $13, $14, $15, $16, $17, $18, $19, $20,
                            $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
                            $31, $32, $33, $34, $35, $36
                        ) RETURNING *
                        """,
                        ticket.ticket_code,
                        ticket.ticket_number,
                        ticket.type,
                        ticket.document_status_code,
                        ticket.owner_pcc,
                        ticket.owner_agent,
                        ticket.agent_issue_pcc,
                        ticket.agent_issue_name,
                        ticket.class_,
                        ticket.pax_name,
                        ticket.itinerary,
                        ticket.ticket_exchange_info,
                        ticket.indicator,
                        ticket.group_name,
                        ticket.issue_date,
                        ticket.currency,
                        ticket.fare,
                        ticket.net_fare,
                        ticket.taxes,
                        ticket.total_fare,
                        ticket.comm,
                        ticket.cancellation_fee,
                        ticket.payable,
                        ticket.amount_used,
                        ticket.booking_date,
                        ticket.booking_signon,
                        ticket.pnr_code,
                        ticket.tour_code,
                        ticket.claim_amount,
                        ticket.date_of_payment,
                        ticket.form_of_payment,
                        ticket.place_of_payment,
                        ticket.remark,
                        ticket.phone,
                        ticket.email,
                        ticket.sold_price    
                    )
                    create_tickets.append(dict(result))
                logger.info(f"Bulk created {len(create_tickets)} tickets.")
                return {"message": f"Created {len(create_tickets)} tickets", "tickets":create_tickets}
    except asyncpg.UniqueViolationError:
        logger.error("Duplicate ticket number in bulk creation")
        raise HTTPException(status_code=400, detail="One or more ticket numbers already exist")
    except Exception as e:
        logger.error(f"Bulk creation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk creation failed.")
#end point for update ticket
@app.put("/tickets/{ticket_number}", dependencies=[Depends(verify_api_key)])
async def update_ticket(ticket_number: str, ticket_update: Ticket):
    try:
        pool = await get_db_connection()
        async with pool.acquire() as conn:
            #check if ticket exist
            existing = await conn.fetchrow(
                "SELECT * FROM tickets WHERE ticket_number = $1",
                ticket_number
            )
            if not existing:
                raise HTTPException(status_code=404, detail="Ticket not found")
            # if it is found we update
            result = await conn.fetchrow(
                """
                UPDATE tickets 
                SET ticket_code = $1, type = $2, document_status_code = $3,
                    owner_pcc = $4, owner_agent = $5, agent_issue_pcc = $6,
                    agent_issue_name = $7, class_ = $8, pax_name = $9,
                    itinerary = $10, ticket_exchange_info = $11, indicator = $12,
                    group_name = $13, issue_date = $14, currency = $15,
                    fare = $16, net_fare = $17, taxes = $18, total_fare = $19,
                    comm = $20, cancellation_fee = $21, payable = $22,
                    amount_used = $23, booking_date = $24, booking_signon = $25,
                    pnr_code = $26, tour_code = $27, claim_amount = $28,
                    date_of_payment = $29, form_of_payment = $30,
                    place_of_payment = $31, remark = $32, phone = $33,
                    email = $34, sold_price = $35
                WHERE ticket_number = $36
                RETURNING *
                """,
                ticket_update.ticket_code,
                ticket_update.type,
                ticket_update.document_status_code,
                ticket_update.owner_pcc,
                ticket_update.owner_agent,
                ticket_update.agent_issue_pcc,
                ticket_update.agent_issue_name,
                ticket_update.class_,
                ticket_update.pax_name,
                ticket_update.itinerary,
                ticket_update.ticket_exchange_info,
                ticket_update.indicator,
                ticket_update.group_name,
                ticket_update.issue_date,
                ticket_update.currency,
                ticket_update.fare,
                ticket_update.net_fare,
                ticket_update.taxes,
                ticket_update.total_fare,
                ticket_update.comm,
                ticket_update.cancellation_fee,
                ticket_update.payable,
                ticket_update.amount_used,
                ticket_update.booking_date,
                ticket_update.booking_signon,
                ticket_update.pnr_code,
                ticket_update.tour_code,
                ticket_update.claim_amount,
                ticket_update.date_of_payment,
                ticket_update.form_of_payment,
                ticket_update.place_of_payment,
                ticket_update.remark,
                ticket_update.phone,
                ticket_update.email,
                ticket_update.sold_price,
                ticket_number
            )
            return dict(result)
    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Update failed")
    
# A search functionality to search for tickets by multiple fields param
@app.get("/tickets/search",dependencies=[Depends(verify_api_key)], response_model=List[TicketSearchResult], summary= "search tickets", description="Search for tickets by ticket number or pax name or agent issue pcc.")
async def search_tickets(ticket_number: Optional[str]=None, pax_name: Optional[str]=None, agent_issue_pcc: Optional[str] = None):
    if not any([ticket_number, pax_name, agent_issue_pcc]):
        logger.error("At least one search parameter is required.")  
        raise HTTPException(status_code=400, detail="At least one search parameter is required.")
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
@app.get("/tickets/{date}",dependencies=[Depends(verify_api_key)], response_model=List[Ticket], summary="Retrieve tickets by date", description="Fetch tickets by issue date.")
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
@app.delete("/tickets/{ticket_number}",dependencies=[Depends(verify_api_key)], summary="Delete a ticket", description="Delete a ticket by ticket number.")
async def delete_ticket(ticket_number: str):
    """Delete a ticket.""" 
    pool = await get_db_connection()
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM tickets WHERE ticket_number = $1", ticket_number)
    if result == "DELETE 0":
        logger.error(f"Ticket not found: {ticket_number}")
        raise HTTPException(status_code=404, detail="Ticket not found")
    logger.info(f"Ticket deleted: {ticket_number}")

    return {"message": "Ticket deleted successfully."}

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": type(exc).__name__
        }
    )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
