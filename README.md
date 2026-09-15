# FitFindr 

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

1. search_listings
Function signature:
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
Inputs:
description: str — The type, style, or description of the item the user wants.
size: str | None — The requested clothing size. Optional.
max_price: float | None — The maximum price the user is willing to pay. Optional.
Return value:
list[dict] — A list of matching listing dictionaries, ranked by relevance. Returns an empty list when no listings match.
Purpose:
Searches the mock secondhand listings dataset using the user's requested item, size, and maximum price, then ranks matching results by relevance.
2. suggest_outfit
Function signature:
def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
Inputs:
new_item: dict — The selected secondhand listing returned by search_listings.
wardrobe: dict — The user's existing wardrobe data.
Return value:
str — A generated outfit suggestion using the selected item and available wardrobe pieces. If the wardrobe is empty, the tool provides general styling advice instead.
Purpose:
Creates outfit suggestions based on the selected new item and the user's existing wardrobe.
3. create_fit_card
Function signature:
def create_fit_card(outfit: str, new_item: dict) -> str:
Inputs:
outfit: str — The outfit suggestion returned by suggest_outfit.
new_item: dict — The same selected secondhand listing used by suggest_outfit.
Return value:
str — A short, shareable fit-card caption describing the selected item and outfit. If the outfit is missing, the tool returns a descriptive error message.
Purpose:
Turns the generated outfit and selected item into a concise fit-card caption for the user.



## Planning Loop
The agent uses a conditional multi-step workflow rather than calling every tool unconditionally.
The agent receives the user's natural-language clothing request.
The query is parsed to extract the item description, requested size, and maximum price.
search_listings is called using those parsed values.
If no listings are found, the agent stops and returns an actionable message asking the user to change their description, size, or price range.
If listings are found, the agent selects the highest-ranked result and stores it in session state.
The selected item and the user's wardrobe are passed to suggest_outfit.
The generated outfit suggestion is stored in session state.
The outfit suggestion and the same selected item are passed to create_fit_card.
The resulting fit card is returned to the user.
This means the next tool depends on the result of the previous tool. For example, the agent does not attempt to create a fit card when search_listings finds no item.


## Query Parsing 
The agent uses Python regular expressions (re) to extract structured information from the user's natural-language query.
The parser looks for:
A requested size, such as size M
A maximum price using phrases such as under $20 or below $20
The remaining text as the clothing/style description
The parsed values are stored in the session state and passed to search_listings.


## State Management
The agent maintains a session state dictionary throughout the interaction. This allows information returned by one tool to be reused by later tools without requiring the user to enter it again.
The session state contains:
{
    "query": ...,
    "parsed": ...,
    "search_results": ...,
    "selected_item": ...,
    "wardrobe": ...,
    "outfit_suggestion": ...,
    "fit_card": ...,
    "error": ...
}
The main state transitions are:
User query
    ↓
Parsed search criteria
    ↓
Search results
    ↓
Selected item
    ↓
Outfit suggestion
    ↓
Fit card
The selected listing returned by search_listings is stored as session["selected_item"] and passed to suggest_outfit. The string returned by suggest_outfit is stored as session["outfit_suggestion"] and passed to create_fit_card.


---

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:** 
"I'm looking for a top that has a Y2K feel that's under $20. I love the color pink, and like to wear bright colors that reflect the Y2K style. I am also a size M."

**Step 1 — Tool called:**
- Tool: search_listings

- Input: 
description: "I'm looking for a top that has a Y2K feel that's under $20. I love the color pink, and like to wear bright colors that reflect the Y2K style. I am also a size M."
size: M
max_price: 20.0

- Why this tool: The user is looking for a secondhand item and provides a size and price limit, so the agent first searches the listings dataset for matching items.

- Output: The search returned matching listings. The top result was:
Y2K Baby Tee — Butterfly Print
Price: $18.00
Listing size: S/M
Platform: Depop
Colors: white, pink, purple
Style tags include Y2K, vintage, graphic tee, and cottagecore

The selected listing is stored in:
session["selected_item"]


**Step 2 — Tool called:**
 - Tool: suggest_outfit

- Input: new_item: the Y2K Baby Tee — Butterfly Print listing from Step 1
wardrobe: the example wardrobe

- Why this tool: new_item: A matching listing was found, so the agent uses that exact selected item together with the user's wardrobe to generate outfit ideas. 

- Output: The tool generated outfit suggestions including:
Cottagecore Pop: The butterfly tee is paired with the white ribbed tank top, baggy straight-leg jeans, brown leather belt, vintage black denim jacket, chunky white sneakers, and black crossbody bag.
Grunge Garden: The butterfly tee is paired with wide-leg khaki trousers, the black cropped zip hoodie, brown leather belt, black combat boots, and black crossbody bag.
The returned string is stored as:
session["outfit_suggestion"]



**Step 3 — Tool called:**
- Tool: create_fit_card

- Input: outfit: the string returned by suggest_outfit
new_item: the same selected listing from Step 1


- Why this tool: An outfit suggestion is available, so the agent can turn it into a short, shareable fit-card caption.

- Output: Snagged the Y2K Baby Tee — Butterfly Print, $18 on depop 🌸. Fitted crop, baggy jeans.


**Final output to user:**
The Gradio interface displays the selected listing, outfit suggestion, and generated fit card in three separate output panels.
---

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` | No listings match the description, size, and price constraints.| Tested with designer ballgown size XXS under $5. The agent returned the no-results message and did not continue to the outfit or fit-card steps.|
| `suggest_outfit` |The user's wardrobe is empty. | Tested with the empty wardrobe option in the Gradio interface. The tool returned general styling advice successfully.|
| `create_fit_card` | The outfit string is missing or empty.| The tool returns: "Cannot write a fit card without an outfit suggestion. Run suggest_outfit() first and pass its result in as outfit. It does not raise an exception.|

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**
<!-- planning.md helped turn the agent from a collection of independent tools into a conditional multi-step workflow. The Planning Loop and State Management sections made me explicitly track the selected listing and generated outfit in session state so that each result could become the input to the next tool without requiring the user to re-enter the same information.
The Architecture diagram also helped me visualize where the workflow should terminate early. In particular, it made it clear that an empty result from search_listings should prevent the downstream outfit and fit-card tools from being called.
 -->


**One divergence from your spec, and why:**
<!-- One divergence was that the original planning described the agent in fairly general terms, while the implementation uses Python regular expressions to parse the natural-language query into a description, size, and maximum price. I chose regex parsing because the required query fields follow predictable patterns such as size M and under $30, making it simple, deterministic, and easy to test without using an additional LLM call.
Another implementation detail was making the search tool rank results using weighted keyword relevance rather than simply returning every listing that passed the filters. This makes the selected top result more useful to the downstream styling tools while keeping the search deterministic and easy to verify against the mock dataset.
 -->
---

**AI Ussage Transparency**
- AI Usage 1
I used an AI coding assistant to help translate the project specification into an implementation plan. I provided the specification sections describing the three required tools, the multi-step planning loop, state management, error handling, and the requirement that the architecture be represented as a diagram.
The AI helped produce a proposed planning structure and Mermaid architecture diagram showing the flow from the user query through search_listings, session state, suggest_outfit, and create_fit_card, including failure paths.
I reviewed the proposed architecture against the assignment requirements and changed it to match my actual implementation. I specifically made sure the diagram represented session state, the no-results branch, the empty-wardrobe behavior, and the missing-outfit failure case.



- AI Usage 2 
I used an AI coding assistant while implementing the planning loop in agent.py. I provided the requirements for parsing the user's natural-language query, passing information between tools, and stopping the workflow when no listings were found.
The AI suggested using a regular-expression-based parser to extract the size and maximum price and helped structure the session state used by run_agent.
I reviewed and tested the implementation myself. I verified the parser using the official Y2K example query and confirmed that it extracted size M and a maximum price of $20.00, selected the expected Y2K listing, and successfully passed the results through all three tools.



- AI Usage 3 
I also used the AI coding assistant to identify concrete failure cases for each tool. I deliberately tested an impossible search, an empty wardrobe, and a missing outfit rather than assuming the error handling worked.
I verified the actual responses produced by my implementation. For example, create_fit_card("", new_item) returned a descriptive error string instead of raising an exception, and the no-results agent path stopped before calling the downstream tools.



## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.
