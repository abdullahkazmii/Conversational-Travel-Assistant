# Sample Queries and Expected Behavior

Use these for manual testing and as a reference for expected behavior.

## Flight search (case study)

**Query:** Find me a round-trip to Tokyo in August with Star Alliance airlines only. I want to avoid overnight layovers.

**Expected:** At least one result; Dubai–Tokyo with Star Alliance (e.g. Turkish Airlines, ANA, Lufthansa); no overnight layovers; dates in August 2024.

## Flight search – other examples

- **Cheap direct flights to Paris under $700** – One-way or round-trip to Paris, price ≤ 700.
- **Show me refundable tickets to London** – Only refundable flights to London.

## Visa (RAG)

**Query:** Do UAE passport holders need a visa for Japan?

**Expected:** Answer should include: visa-free, 30 days, tourism, passport valid at least 6 months.

## Policy (RAG)

**Query:** What's the refund policy for tickets? / Can I cancel my booking 48 hours before departure?

**Expected:** Answer should include: refundable tickets, cancel up to 48 hours before departure, 10% processing fee.

## Clarification

**Query:** I want to travel. / Help me with flights.

**Expected:** Assistant asks for destination (or other missing details) in a friendly way.
