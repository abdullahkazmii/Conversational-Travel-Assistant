# Conversational Travel Assistant

A conversational AI assistant for international travel planning. It supports natural-language flight search, visa and policy Q&A over a knowledge base, and multi-turn clarification — built with LangGraph, Gemini, and ChromaDB.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Setup Instructions](#setup-instructions)
- [Running the Application](#running-the-application)
- [System Overview](#system-overview)
- [Agent Logic & Graph](#agent-logic--graph)
- [Prompt Strategies](#prompt-strategies)
- [Sample Inputs & Outputs](#sample-inputs--outputs)
- [Configuration](#configuration)

---

## Features

- **Natural-language flight search** — e.g. “Find me a round-trip to Tokyo in August with Star Alliance only, avoid overnight layovers.”
- **Multi-criteria filtering** — Destination, origin, dates, alliance, layovers, price, refundability.
- **Visa and policy Q&A** — RAG over a knowledge base (visa rules, refund policies, baggage, travel tips).
- **Conversational flow** — Intent routing, clarification when details are missing, conversation context across turns.

---

## Tech Stack

| Layer        | Technology                          |
|-------------|--------------------------------------|
| Language    | Python 3.10+                         |
| Orchestration | LangGraph (state machine / agent graph) |
| LLM & Embeddings | LangChain + Google Gemini (chat + embeddings) |
| Vector Store | ChromaDB                            |
| UI          | Streamlit |

---

## Repository Structure

```
Conversational-Travel-Assistant/
├── main.py                    # CLI entry point
├── streamlit_app.py           # Streamlit chat UI
├── config/
│   ├── __init__.py
│   ├── settings.py            # Env-based settings (Gemini, ChromaDB, RAG)
│   └── prompts.py             # All LLM prompts (intent, criteria, RAG, clarification)
├── src/
│   ├── agents/
│   │   ├── state.py           # TravelAssistantState
│   │   ├── nodes.py           # Graph nodes: router, criteria, flight_search, RAG, response, clarification
│   │   └── graph.py           # LangGraph workflow definition and conditional edges
│   ├── tools/
│   │   ├── criteria_extractor.py  # NL → FlightCriteria (LLM + JSON)
│   │   ├── flight_search.py       # Filter/rank data/flights.json
│   │   └── rag_retrieval.py       # ChromaDB retrieval + Gemini answer
│   ├── services/
│   │   ├── llm_service.py     # Gemini invoke/embed
│   │   └── vector_store.py    # ChromaDB client
│   ├── models/
│   │   ├── schemas.py         # Flight, FlightCriteria, RAGResult, etc.
│   │   └── enums.py           # IntentType, Alliance, NodeName
│   └── utils/
│       ├── logger.py
│       ├── init_knowledge_base.py  # Chunk KB, embed, persist to ChromaDB
│       ├── validators.py
│       └── formatters.py
├── data/
│   ├── flights.json           # Mock flight data
│   ├── visa_rules.md          # Visa rules (ingested into RAG)
│   └── knowledge_base/        # Markdown docs for RAG
│       ├── visa_requirements.md
│       ├── refund_policies.md
│       ├── baggage_policies.md
│       └── travel_tips.md
├── tests/
│   └── sample_queries.md      # Manual test cases and expected behavior
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup Instructions

### 1. Clone and create virtual environment

```bash
cd Conversational-Travel-Assistant
python -m venv .venv

#Mac:
source .venv/bin/activate   
# Windows: 
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env`

- **`GOOGLE_API_KEY`** — Required for Gemini (chat and embeddings).

### 4. Mock data

- **Flights:** `data/flights.json` is included.
- **Knowledge base:** `data/knowledge_base/*.md` and `data/visa_rules.md` are included.

### 5. Initialize RAG (required for visa/policy questions)

This chunks the markdown files, embeds them with Gemini, and stores them in ChromaDB:

```bash
python -m src.utils.init_knowledge_base
```

Run from the **project root** so that `config` and `src` are importable.

---

## Running the Application

### CLI

From the project root:

```bash
python main.py
```

### Streamlit UI

From the project root:

```bash
streamlit run streamlit_app.py
```

- Browser opens to the Streamlit app (default: `http://localhost:8501`).
- Use the chat input at the bottom to ask about flights, visas, or policies.
- Messages are stored in `st.session_state.messages` for the session.

---

## System Overview

1. **Router** — Classifies intent into: `FLIGHT_SEARCH`, `VISA_QUERY`, `POLICY_QUERY`, `GENERAL_TRAVEL`, or `CLARIFICATION_NEEDED`. Uses the latest user message and recent conversation context.
2. **Criteria extraction** — For flight search: extracts structured `FlightCriteria` (destination, origin, dates, alliance, layovers, price, refundability, etc.) from natural language, with conversation context for references (e.g. “london” after “I want to travel”).
3. **Flight search** — Filters and ranks `data/flights.json` by the extracted criteria (date ranges, overnight layover, alliance, price, etc.) and returns a list of `Flight` objects.
4. **RAG** — For visa/policy/general: retrieves relevant chunks from ChromaDB, optionally reranks, then generates an answer with Gemini using a “context only” prompt; if the answer isn’t in context, it responds with a fixed “no information” message.
5. **Response generation** — Formats flight results (or a “no results” message) into a user-friendly reply via an LLM.
6. **Clarification** — When required fields (e.g. destination) are missing, asks a short follow-up question using conversation context so it doesn’t repeat what the user already said.

---

## Agent Logic & Graph

The assistant is implemented as a **LangGraph** state machine with a single entry point and conditional edges.

- **State:** `TravelAssistantState` (TypedDict) holds `messages`, `user_query`, `intent`, `extracted_criteria`, `search_results`, `rag_context`, `final_response`, `needs_clarification`, `error`.

**Nodes:**

| Node                   | Role |
|------------------------|------|
| `router`               | Intent classification → next node |
| `criteria_extraction`  | Parse NL to `FlightCriteria`; set `needs_clarification` if e.g. no destination |
| `flight_search`        | Filter/rank flights; write `search_results` |
| `rag_query`            | Retrieve + generate answer; write `final_response` |
| `response_generation`  | Format flight results or no-results message → `final_response` |
| `clarification`        | Generate clarification question → `final_response` |

**Edges:**

- **Entry:** `router`.
- **From router:**  
  - `FLIGHT_SEARCH` → `criteria_extraction`  
  - `VISA_QUERY` / `POLICY_QUERY` / `GENERAL_TRAVEL` → `rag_query` → **END**  
  - `CLARIFICATION_NEEDED` → `clarification` → **END**
- **From criteria_extraction:**  
  - `needs_clarification` → `clarification` → **END**  
  - else → `flight_search` → `response_generation` → **END**

So: every request goes through the router; flight-search requests may go through criteria → (optional clarification) → flight_search → response_generation; RAG and clarification branches go straight to END after one node.

---

## Prompt Strategies

Defined in `config/prompts.py`.

| Purpose | Strategy |
|--------|----------|
| **Intent** | Single-label classification. Prompt lists the five categories with short examples. Instruction: respond with **only** the category name. Parser matches the response to `IntentType`. |
| **Criteria** | JSON extraction with a fixed schema and few-shot examples (e.g. Tokyo + Star Alliance + avoid overnight). Instruction to use full conversation to resolve references (e.g. “london” as destination). Missing/null dates normalized to `"flexible"` or null before validation. |
| **RAG** | System prompt: answer **only** from context; if not in context, say “I don’t have that information in my knowledge base.” Friendly tone, cite details; for visa, mention passport validity if in context. Follow-up prompt supports “what do you mean?” style questions using previous answer + new context. |
| **No flight results** | Dedicated prompt: politely say no matches, suggest relaxing constraints (dates, alliance, layovers, price), offer to search again. |
| **Clarification** | Prompt includes conversation context and list of missing fields. Instruction: don’t ask again for something the user already gave; ask for the next missing piece only; keep it short and conversational. |

---

## Sample Inputs & Outputs

From `tests/sample_queries.md` and expected behavior:

### Flight search (case study)

**Input:**  
“Find me a round-trip to Tokyo in August with Star Alliance airlines only. I want to avoid overnight layovers.”

**Expected:** At least one result: Dubai–Tokyo, Star Alliance (e.g. Turkish Airlines, ANA, Lufthansa); no overnight layovers; dates in August 2024.

---

### Flight search — other examples

- **“Cheap direct flights to Paris under $700”** — One-way or round-trip to Paris, price ≤ 700.
- **“Show me refundable tickets to London”** — Only refundable flights to London.

---

### Visa (RAG)

**Input:**  
“Do UAE passport holders need a visa for Japan?”

**Expected:** Answer includes: visa-free, 30 days, tourism, passport valid at least 6 months (from knowledge base).

---

### Policy (RAG)

**Input:**  
“What’s the refund policy for tickets?” / “Can I cancel my booking 48 hours before departure?”

**Expected:** Answer includes: refundable tickets, cancel up to 48 hours before departure, 10% processing fee (from knowledge base).

---

### Clarification

**Input:**  
“I want to travel.” / “Help me with flights.”

**Expected:** Assistant asks for destination (or another missing detail) in a friendly, single-question way without repeating already provided info.

---

## Configuration

| Variable | Description | Default (if any) |
|----------|-------------|-------------------|
| `GOOGLE_API_KEY` | Gemini API key | (required) |
| `GEMINI_MODEL` | Chat model | `gemini-2.5-flash` |
| `GEMINI_EMBEDDING_MODEL` | Embedding model | `gemini-embedding-001` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB persistence path | `./data/vectorstore` |
| `CHROMA_COLLECTION_NAME` | Collection name | `travel_knowledge_base` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_SEARCH_RESULTS` | Max flights returned | `5` |
| `RAG_TOP_K` | Top-k chunks for RAG | `3` |
| `RAG_CHUNK_SIZE` | Chunk size for KB ingestion | `600` |
---

