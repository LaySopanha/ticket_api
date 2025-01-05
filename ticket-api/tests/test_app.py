import pytest
from httpx import AsyncClient
from app import app, database

@pytest.fixture(autouse=True)
async def setup_and_cleanup():
    # Setup - clear database before each test
    await database.execute("DELETE FROM tickets")
    yield
    # Cleanup - clear database after each test
    await database.execute("DELETE FROM tickets")

#test fetching all tickets
@pytest.mark.asyncio
async def test_get_tickets():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/tickets")
    assert response.status_code == 200
    assert isinstance(response.json(), list) # expected list of ticket

# test creating ticket
@pytest.mark.asyncio
async def test_create_ticket():
    ticket_data = {
        "ticket_code": "T12345",
        "ticket_number": "12345",
        "type": "Economy",
        "document_status_code": "Issued",
        "owner_pcc": "PCC001",
        "owner_agent": "Agent01",
        "agent_issue_pcc": "PCC002",
        "agent_issue_name": "John Doe",
        "class_": "Economy",
        "pax_name": "Jane Doe",
        "itinerary": "NYC-LAX",
        "issue_date": "2024-01-01",
        "currency": "USD",
        "fare": 500.0,
        "net_fare": 450.0,
        "taxes": 50.0,
        "total_fare": 550.0,
        "comm": 10.0,
        "cancellation_fee": 25.0,
        "payable": 525.0,
        "amount_used": 0.0,
        "booking_date": "2023-12-25",
        "booking_signon": "Agent01",
        "pnr_code": "PNR001",
        "tour_code": "TOUR01",
        "claim_amount": 0.0,
        "date_of_payment": "2023-12-30",
        "form_of_payment": "Credit Card",
        "place_of_payment": "New York",
        "remark": "No remarks",
        "phone": "1234567890",
        "email": "jane.doe@example.com",
        "sold_price": 550.0
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/tickets", json=ticket_data)
    assert response.status_code == 201
    data = response.json()
    assert data["ticket_code"] == ticket_data["ticket_code"]
    assert data["ticket_number"] == ticket_data["ticket_number"]

# test search functionality 
@pytest.mark.asyncio
async def test_search_ticket():
    # First create a ticket to search for
    ticket_data = {
        "ticket_code": "T12345",
        "ticket_number": "12345",
        # ... add other required fields ...
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create the ticket first
        await client.post("/tickets", json=ticket_data)
        # Then search for it
        response = await client.get("/tickets/search", params={"ticket_number": "12345"})
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["ticket_number"] == "12345"

# test deleting ticket
@pytest.mark.asyncio
async def test_delete_ticket():
    # First create a ticket to delete
    ticket_data = {
        "ticket_code": "T12345",
        "ticket_number": "12345",
        # ... add other required fields ...
    }
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create the ticket first
        await client.post("/tickets", json=ticket_data)
        # Then delete it
        response = await client.delete("/tickets/12345")
    
    assert response.status_code == 204
    # Don't check for response.json() as 204 means no content
    