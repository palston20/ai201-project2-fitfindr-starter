# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- The search_listings tool is a database that has listings for different types of apparel that are for sale on different online thrift stores like Depop, Threadup, and Poshmark. The apparel will match the user's description, size, and maximum price. -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Gives a keywords describing the apparel item the user is looking for.
- `size` (str): Provides what size the item is in (which includes global sizes and shoe sizes). 
- `max_price` (float): This shows the maximum price a buyer is selling the item for. 

**What it returns:**
<!-- Returns a list of matchin glisting dictionaries, sorted by relevance. Each listing contains id, title, description, category, style_tags, size, condition, price, colors, brand, and platform.
-->

**What happens if it fails or returns nothing:**
<!--  If there are no listings that match the user's query, the tool returns an empty list. The agent should communicate that no matching listings were found and either ask the user for different search criteria or use a fallback if one is available. -->

---

### Tool 2: suggest_outfit

**What it does:**
<!-- The suggest_outfit tool uses a thrifted item and the user's wardrobe to suggesr 1-2 complete outfit. If the wardrobe is empty, it provides general styling advice for the new item instead.
 -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): The list dictionary for the thrifted item the user is considering.
- `wardrobe` (dict): A dictionary containing the user's wardrobe, with an items key containng a list of wardrobe item dicitonaries. The wardrobe may be empty.

**What it returns:**
<!-- Returns a non-empty string contaiing one or more outfit suggestions.
-->

**What happens if it fails or returns nothing:**
<!-- If the wardrobe is empty, the tool provides general styling suggestions for the new item instead of returning an empty result. If the tool encounters another failure, the agent should communicate the issue to the user and ask for additional information or try an appropriate fallback. -->

---

### Tool 3: create_fit_card

**What it does:**
<!-- The create_fit_card tool generates a short, shareable outfit caption based on the thrifted item and the suggested outfit. -->

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str): The outfit suggestion returned by suggest_outfit
- `new_item` (dict): The listing dictionary for the thrifted item.

**What it returns:**
<!-- Returns a 2–4 sentence string that can be used as an Instagram or TikTok-style outfit caption. The caption includes the item name, price, platform, and the overall outfit vibe. -->

**What happens if it fails or returns nothing:**
<!-- If the outfit is empty or missing, the tool returns a descriptive error message instead of raising an exception. The agent can then ask the user for the missing outfit information before trying again. -->

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done?

The agent decides which tool to call based on the user's request and the results returned by previous tools. If the user is looking for a secondhand item, the agent calls search_listings. If listings are found, the selected item can be passed to suggest_outfit along with the user's wardrobe. If an outfit is successfully generated, the agent can then call create_fit_card. If a tool returns an empty result or encounters an error, the agent communicates the issue to the user and either asks for more information or uses an appropriate fallback. The loop ends when the user's request has been fulfilled or when additional information is needed. 

**Query Parsing:** The agent uses Python regular expressions (`re`) to extract the item's description, size, and maximum price from the user's natural-language query. The parsed values are stored in the session state and passed to `search_listings`.

-->

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? 

The agent stores information from each tool call in the session state so it can be accessed by later tools. The state tracks information such as the user's original request, wardrobe, search results, selected new item, and suggested outfit. When search_listings finds an item, the selected listing is stored in the state and passed to suggest_outfit. The outfit suggestion is then stored in the state and passed along with the new item to create_fit_card. This allows information from previous tool calls to be reused without requiring the user to enter the same information again.
-->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |Inform user that no listings were found and ask them to try different search criteria, like different description, size, or price.|
| suggest_outfit | Wardrobe is empty | Provide general styling advice for th enew item instead of trying to create an outfit from specific wardrobe pieces.|
| create_fit_card | Outfit input is missing or incomplete | Return a descriptive error message and ask for the missing information instead of generating a caption.|

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card) -->

     ```mermaid
flowchart TD
    U[User] -->|Natural language request| P[Planning Loop]

    P -->|Needs item search| S[search_listings]
    S -->|Matching listings| ST[(Session State)]
    S -->|No matches / error| E1[Error: Inform user or request new criteria]

    ST -->|Selected new_item| P

    P -->|Item found + wardrobe available| O[suggest_outfit]
    ST -->|new_item + wardrobe| O
    O -->|Outfit suggestions| ST
    O -->|Empty wardrobe / tool error| E2[Error: General styling advice or request more information]

    ST -->|new_item + outfit| P
    P -->|Outfit successfully generated| F[create_fit_card]
    F -->|Fit card caption| ST
    F -->|Missing outfit / tool error| E3[Error: Request missing outfit information]

    ST -->|Final fit card| U

    E1 -->|Terminate early| END[End]
    E2 -->|Terminate early| END
    E3 -->|Terminate early| END
```


---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**

<!-- I will use Claude to help implement the three individual tools. I will give it the corresponding tool specifications from the Tools section of planning.md, including each tool's inputs, return value, and failure mode. For search_listings, I will also provide the requirement to use load_listings() from the data loader. For suggest_outfit and create_fit_card, I will provide the requirements for their LLM prompts and expected outputs. 
Claude will implement each tool separately rather than generating the entire project at once. Before using each implementation, I will compare the code against the tool specification and check that the inputs, outputs, and failure handling match the plan. I will also test each tool with normal inputs and its specific failure case. For example, I will test search_listings with matching and non-matching queries, suggest_outfit with both a populated and empty wardrobe, and create_fit_card with both a valid and missing outfit. -->

**Milestone 4 — Planning loop and state management:**

<!--I'll use Claude to help implement the planning loop and session state. I will give it the Planning Loop, State Management, and Architecture sections of planning.md, including the agent diagram showing how the user, planning loop, three tools, session state, and error branches interact. 
Then, Claude will implement a loop that decides which tool to call based on the user's request and the results returned by previous tools, rather than calling every tool in a fixed sequence. I will also ask it to use session state to pass information such as the selected new_item and generated outfit between tools.
Before using the implementation, I will trace through the complete interaction from the example in planning.md and verify that the agent makes the correct tool calls in the correct order. I will also test an error case, such as a search with no matching listings, to make sure the agent stops or asks for new information instead of continuing with missing data.


-->

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

"I'm looking for a top that has a Y2K feel that's under $20. I love the color pink, and like to wear bright colors that reflect the Y2K style. I am also a size M."

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input?
First, the agent will use the search_listings tool to see what options are available based on the user's query. It will return "search_listings(Y2K Baby Tee, size, S/M,$18)".


The agent identifies that the user is looking for a secondhand item and needs to search the listings first. It calls:
search_listings(description="pink Y2K top", size="M", max_price=20)
The tool searches the mock listings dataset and returns a list of matching listing dictionaries. The agent stores the search results and selected new_item in session state.
  -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? 
After a top that matches the user's  style is chosen, then the next tool, which is suggest_outfit would be called. This tool will use the new suggested item and talk about how it complements what's already in the user's wardrobe.

The agent identifies that the user is looking for a secondhand item and needs to search the listings first. It calls:
search_listings(description="pink Y2K top", size="M", max_price=20)
The tool searches the mock listings dataset and returns a list of matching listing dictionaries. The agent stores the search results and selected new_item in session state.


 -->

**Step 3:**
<!-- Because an outfit was successfully generated, the agent passes the stored outfit and selected listing to the final tool. It calls:
create_fit_card(outfit=<outfit suggestion>, new_item=<selected listing>)
The tool generates a short, casual 2–4 sentence caption that mentions the item, price, platform, and overall Y2K outfit vibe. The loop will continue until it's complete.
 -->

**Final output to user:**
<!-- What does the user actually see at the end?
The user at the end will see a shortt description of the complete outfit, something that the user can post with on their social media. 

The user sees a short, shareable fit card describing the complete Y2K outfit, including the thrifted item and the styling details. The output is written like a social media caption rather than a product description.
 -->
