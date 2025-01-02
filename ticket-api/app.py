from fastapi import FastAPI, HTTPException
from typing import list 
from typing import Optional
from datetime import date
from pydantic import BaseModel
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
    ticket_code: Optional[str]  # Serial Primary key
    ticket_number: str
    type: Optional[str]
    document_status_code: Optional[str]
    owner_pcc: Optional[str]
    owner_agent: Optional[str]
    agent_issue_pcc: Optional[str]
    agent_issue_name: Optional[str]
    class_: Optional[str]  # 'class' is a reserved keyword in Python
    pax_name: Optional[str]
    itinerary: Optional[str]
    ticket_exchange_info: Optional[str]
    indicator: Optional[str]
    group_name: Optional[str]
    issue_date: Optional[date]
    currency: Optional[str]
    fare: Optional[float]
    net_fare: Optional[float]
    taxes: Optional[float]
    total_fare: Optional[float]
    comm: Optional[float]
    cancellation_fee: Optional[float]
    payable: Optional[float]
    amount_used: Optional[float]
    booking_date: Optional[date]
    booking_signon: Optional[str]
    pnr_code: Optional[str]
    tour_code: Optional[str]
    claim_amount: Optional[float]
    date_of_payment: Optional[date]
    form_of_payment: Optional[str]
    place_of_payment: Optional[str]
    remark: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    sold_price: Optional[float]

#database connection 

async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)