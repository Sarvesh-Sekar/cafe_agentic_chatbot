
# Bean & Brew — MCP-powered coffee shop chatbot

Bean & Brew is a **two-process** Python app:

1. **Chat API (FastAPI)** in `mcp_client/`: exposes an HTTP endpoint (`/api/chat`) for a UI or any client.
2. **Tool Server (FastMCP)** in `mcp_server/`: exposes **MCP tools, prompts, and resources** over **Streamable HTTP**.

The FastAPI app runs a LangChain agent backed by **AWS Bedrock** (`ChatBedrock`). When the agent needs live data (menu, inventory, order status, placing orders), it calls tools hosted by the MCP server. Conversation state is persisted using **LangGraph Postgres checkpointer**.


---

## 🧱 High-level architecture

### Components

- **`mcp_client` (FastAPI)**
	- Accepts user messages and returns a structured response.
	- Orchestrates LLM calls, tool calls, prompt/resource selection, and memory.

- **`mcp_server` (FastMCP)**
	- Hosts MCP **tools** (functions), **prompts**, and **resources**.
	- Reads/writes data from a PostgreSQL database via SQLAlchemy.
	- On startup, creates tables and seeds menu items.

- **PostgreSQL**
	- Used twice:
		1) by the MCP server for **domain data** (menu, customers, orders)
		2) by the chat agent for **conversation memory** (LangGraph checkpoints)

### Runtime diagram

```text
┌──────────────┐   HTTP POST /api/chat     ┌────────────────────────┐
│ Any Client   │ ───────────────────────▶  │ mcp_client (FastAPI)   │
│ (UI/curl)    │                          │  ChatService + Agent   │
└──────────────┘                          └───────────┬────────────┘
																											│
																											│ MCP (streamable HTTP)
																											▼
																						┌────────────────────────┐
																						│ mcp_server (FastMCP)   │
																						│ tools/prompts/resources│
																						└───────────┬────────────┘
																												│
																												▼
																									 ┌──────────┐
																									 │PostgreSQL│
																									 └──────────┘

FastAPI also connects to PostgreSQL for LangGraph checkpoints (agent memory).
```

---

## 📁 Repository layout

```text
.
├─ main.py                      # Placeholder entrypoint (prints hello)
├─ mcp_client/
│  ├─ main.py                   # FastAPI app entrypoint
│  ├─ settings.py               # .env configuration for client (Bedrock/MCP/DB)
│  └─ src/
│     ├─ routers/router.py      # POST /api/chat
│     ├─ services/chat_service.py
│     ├─ agents/agent.py        # LangChain agent + MCP client + memory/HITL
│     ├─ models/chat_model.py   # Pydantic request/response schemas
│     └─ utils/custom_app_exception.py
└─ mcp_server/
	 ├─ main.py                   # FastMCP server entrypoint (HTTP transport)
	 ├─ settings.py               # .env configuration for server (DB)
	 └─ src/
			├─ routers/mcp_router.py  # Mounts tools/prompts/resources
			├─ tools/mcp_tool.py      # MCP tools: menu/inventory/orders
			├─ prompts/mcp_prompts.py # MCP prompt registry (system instructions)
			├─ resources/mcp_resource.py # MCP resources: tips/policy context
			├─ repositories/
			│  ├─ database.py         # SQLAlchemy engine/session
			│  ├─ mcp_repository.py   # DB operations + ErrorRepository
			│  └─ schemas/mcp_schema.py
			└─ migrations/create_tables.py # create_all + seed menu
```

---

## 🔌 Public APIs

### 1) Chat API (FastAPI)

- **Endpoint**: `POST /api/chat`
- **Router**: `mcp_client/src/routers/router.py`
- **Request schema**: `ChatRequest` in `mcp_client/src/models/chat_model.py`
	- `user_query: str`
	- `session_id?: str` (LangGraph thread id)
	- `customer_id?: str`
	- `interrupt?: List[InterruptModel]` (resume data for HITL flow)
- **Response schema**: `APIResponse`
	- `structured_content` is one of:
		- `OrderDetails` (order status / order created)
		- `MenuResponse` (menu listing)
		- `ChatResponse` (free-form answer)
		- `NeedContextResponse` (asks user for missing info)

### 2) MCP server (FastMCP)

Started via `mcp_server/main.py` over **Streamable HTTP**.

#### Tools (in `mcp_server/src/tools/mcp_tool.py`)

- `check_menu()` → returns menu items
- `check_inventory(item_name: str)` → availability + stock
- `check_order_status(ord_code: str)` → order snapshot
- `add_order(customer_name: str, phone_no: str, items: List[Dict])` → creates customer/order/items

#### Prompts (in `mcp_server/src/prompts/mcp_prompts.py`)

- `system_prompt()` → long instruction prompt that governs tool usage + response typing
- `menu_assistant()` → prompt that forces an immediate `check_menu` call

#### Resources (in `mcp_server/src/resources/mcp_resource.py`)

- `resource://get_info` → coffee preparation tips/context
- `resource://get_policy_info` → shop policy context

---

## 🧠 Agent orchestration flow (client)

The main orchestration happens in `mcp_client/src/services/chat_service.py` and `mcp_client/src/agents/agent.py`.

### Request lifecycle

1. **FastAPI** accepts `ChatRequest`.
2. `ChatService.process_chat_service(...)`:
	 - validates `user_query`
	 - creates an `Agent`
	 - builds Bedrock LLM (`Agent.get_llm()`)
	 - creates MCP client (`Agent.create_client()`)
	 - runs a simple **PII detection + masking** step (`input_filter()` in `chat_service.py`)
3. Agent loads MCP **prompts** and chooses a **system prompt** (`Agent.load_prompts()`).
4. Agent loads MCP **resources** and may attach a context block (`Agent.load_resources()` + `Agent.load_context()`).
	 - heuristic keyword router:
		 - preparation/tips keywords → `resource://get_info`
		 - policy keywords → `resource://get_policy_info`
5. Agent loads MCP **tools** (`Agent.load_tools()`), unless a resource was selected (then tools are intentionally emptied).
6. Agent initializes **conversation memory** using `AsyncPostgresSaver` (LangGraph)
	 - uses `session_id` as the thread id (`thread_id`) when available
7. Agent creates a LangChain agent with middleware:
	 - `SummarizationMiddleware` (token-triggered)
	 - `HumanInTheLoopMiddleware(interrupt_on={"add_order": True})`
8. Agent invokes the graph:
	 - first turn: `agent.ainvoke({"messages": HumanMessage(...)}, config=...)`
	 - resume turn: `agent.ainvoke(Command(resume={"decisions": ...}))`
9. Result is returned to the API as `APIResponse(structured_content=...)`.

### Human-in-the-loop (HITL) behavior

When the agent attempts `add_order`, the HITL middleware can interrupt. The API supports resuming by passing `interrupt` decisions back in `ChatRequest.interrupt`.

---

## 🗄️ Data layer (server)

### Database tables

Defined in `mcp_server/src/repositories/schemas/mcp_schema.py` and created in `mcp_server/src/migrations/create_tables.py`:

- `customers`
- `menu_items`
- `orders`
- `order_items`
- `err_logs`

### Repository pattern

`mcp_server/src/repositories/mcp_repository.py` contains:

- `MCPRepository`: domain queries and commands (menu, customer, orders)
- `ErrorRepository`: writes to `err_logs`

These are injected into tools using `fastmcp.dependencies.Depends`.

---

## ⚙️ Configuration

Both apps load environment variables via `python-dotenv`.

### `mcp_client/settings.py`

- `MODEL_ID` (AWS Bedrock model id)
- `MCP_SERVER_URL` (e.g. `http://127.0.0.1:8001/mcp`)
- `DB_*` (used by LangGraph checkpointing)
- AWS credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) and `REGION`

### `mcp_server/settings.py`

- `DB_*` (used for menu/order database)

---

## ▶️ Running locally

This repo doesn’t include docker files, so you’ll need a local PostgreSQL.

### 1) Start the MCP server

Run `mcp_server/main.py`. On startup it will create tables and seed menu data.

### 2) Start the chat API

Run `mcp_client/main.py` (it’s a FastAPI app). The `/api/chat` endpoint will use the MCP server URL from `MCP_SERVER_URL`.

### Example request

Send POST JSON with at least `user_query`.

```json
{
	"user_query": "What is on the menu?",
	"session_id": null,
	"customer_id": null,
	"interrupt": null
}
```

---

## 🧩 Notes / gotchas

- **Two ports**: `mcp_client/main.py` defaults to port **8000**; `mcp_server/main.py` runs on **8001** and mounts at `/mcp`.
- **Tools vs context**: when a resource context is selected in `Agent.load_context()`, tools are cleared (`self.tools = []`). That means policy/tips questions answer only from resource context.
- **Dependencies**: `pyproject.toml` and `requirements.txt` overlap but aren’t identical. If you standardize packaging, pick one source of truth.

