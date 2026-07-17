import json
import logging
import requests
import time
import re

logger = logging.getLogger(__name__)

LIST_PARSER_PROMPT = """You are an AI Shopping Assistant for PricePilot.

Your job is to read raw, unstructured shopping lists (from WhatsApp, Notes app, handwriting OCR, etc.) and convert them into a structured JSON array of grocery items.

For each item, identify the standard product name and the quantity if specified.

Rules:
1. Standardize names (e.g., "milk" -> "Milk", "1 kg sugar" -> "Sugar").
2. Extract quantities into a separate field (e.g., "2L", "1 kg", "500g"). If no quantity is specified, return an empty string "".
3. Ignore bullet points, checkboxes, emojis, or conversational filler.
4. ONLY return a valid JSON array. Do not include markdown code blocks or conversational text.

Example Input:
- 2 litres milk
- a loaf of bread
- eggs (dozen)
- 1 kg basmati rice
- some curd 500g

Example Output:
[
  {"name": "Milk", "quantity": "2L"},
  {"name": "Bread", "quantity": "1 loaf"},
  {"name": "Eggs", "quantity": "1 dozen"},
  {"name": "Basmati Rice", "quantity": "1kg"},
  {"name": "Curd", "quantity": "500g"}
]
"""

PLANNER_PROMPT = """You are PricePilot's specialized grocery planning sub-agent.
Your ONLY job is to take a user's natural language goal and return a raw, structured JSON array of grocery items needed to fulfill that goal.
Do NOT include markdown formatting or conversational text. Return ONLY a valid JSON array.
If the goal is "Feed 4 people for 1500 this week", generate essentials (rice, atta, milk, veggies, dal).
Include realistic quantities (e.g., "5kg", "2L", "500g", "1 dozen").

Example Output:
[
  {"name": "Milk", "quantity": "2L"},
  {"name": "Toor Dal", "quantity": "1kg"},
  {"name": "Onion", "quantity": "1kg"}
]
"""

def parse_shopping_list(raw_text: str) -> list[dict]:
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "mistral",
                "system": LIST_PARSER_PROMPT,
                "prompt": raw_text,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=30
        )
        response.raise_for_status()
        content = response.json().get("response", "")
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)
    except Exception as e:
        logger.error(f"Shopping list parsing failed: {e}")
        return []

def generate_shopping_plan(goal: str) -> list[dict]:
    try:
        response = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={
                "model": "mistral",
                "system": PLANNER_PROMPT,
                "prompt": goal,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=45
        )
        response.raise_for_status()
        content = response.json().get("response", "")
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
            
        return json.loads(content)
    except Exception as e:
        logger.error(f"Shopping plan generation failed: {e}")
        return []

CHATBOT_PROMPT = """You are PricePilot, an elite AI Grocery Copilot.
WARNING: YOU ARE STRICTLY FORBIDDEN FROM WRITING ANY CODE OR JAVASCRIPT.

Your capabilities:
- You help users plan meals, generate grocery lists, compare prices, optimize carts, and automate shopping.
- You have access to real-time context provided below.

Rules:
1. Be concise, friendly, and helpful. Use markdown.
2. If the user wants a shopping plan, you MUST use the generate_shopping_plan tool.
3. If you need to optimize a cart, you MUST use the optimize_cart tool. The active shopping list is automatically provided.
4. TO USE A TOOL, YOU MUST OUTPUT A JSON CODEBLOCK WITH THE TOOL NAME AND ARGS. For example:
```json
{
  "tool": "generate_shopping_plan",
  "goal": "vegetarian groceries for 7 days"
}
```
OR
```json
{
  "tool": "optimize_cart"
}
```

5. DO NOT invent prices or availability. Rely strictly on the tools.
6. When explaining a shopping plan, mention the total cost, savings, and why a provider was chosen based on the tool results.

Context:
{context}
"""

def execute_tool(name: str, arguments: dict, context: dict = None) -> tuple[str, dict]:
    from comparison.service import PriceComparisonService
    service = PriceComparisonService()
    
    try:
        if name == "generate_shopping_plan":
            goal = arguments.get("goal")
            if not goal: return "Error: goal is required.", None
            
            items = generate_shopping_plan(goal)
            if not items:
                return "Failed to generate plan.", None
                
            lines = ["Generated Grocery List:"]
            for item in items:
                lines.append(f"- {item.get('name')} ({item.get('quantity')})")
            
            state_update = {"type": "shopping_plan_generated", "items": items}
            return "\n".join(lines), state_update

        elif name == "search_products":
            query = arguments.get("query")
            if not query: return "Error: query is required.", None
            
            search_history = service.search(query=query)
            lines = [f"Search Results for '{query}':"]
            for comp in search_history.results.select_related("platform").all():
                if comp.product_name and not comp.error_message:
                    platform_name = comp.platform.name if comp.platform else "Unknown Platform"
                    lines.append(f" - {comp.product_name} at {platform_name}: ₹{comp.total_price} (Price: ₹{comp.price} + Delivery: ₹{comp.delivery_charge})")
            
            if len(lines) == 1:
                return "No products found or all providers failed.", None
                
            return "\n".join(lines), None
            
        elif name == "optimize_cart":
            # Just use the active shopping list directly from the frontend's context!
            items = context.get("activeShoppingList") if context else None
            
            if not items:
                return "Error: No active shopping list found to optimize. Ensure you have generated a plan first.", None
            
            # Extract names and quantities for the optimizer
            search_items = []
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    search_items.append({"name": item["name"], "quantity": item.get("quantity", "")})
            
            cart_result = service.optimize_cart(search_items, strategy="cheapest")
            lines = [f"Cart Optimization Results (Grand Total: {cart_result['grand_total']}):"]
            for split in cart_result.get("splits", []):
                lines.append(f"\nPlatform: {split['platform']} (Subtotal: {split['subtotal']})")
                for item in split.get("items", []):
                    url = item.get("product_url")
                    url_str = f" [Link]({url})" if url else ""
                    lines.append(f" - {item['matched_name']}: {item['price']}{url_str}")
            
            if cart_result.get("unavailable"):
                lines.append("\nUnavailable items: " + ", ".join([i["original_query"] for i in cart_result["unavailable"]]))
                
            state_update = {"type": "cart_optimized", "result": cart_result}
            return "\n".join(lines), state_update
            
        return f"Unknown tool: {name}", None
    except Exception as e:
        logger.exception(f"Tool {name} failed.")
        return f"Tool execution failed: {str(e)}", None

def chat_with_assistant(messages: list[dict], context: dict = None):
    """
    Generator that streams the response token by token.
    It automatically handles tool calls in a loop.
    """
    context_str = json.dumps(context, indent=2) if context else "No active context."
    system_prompt = CHATBOT_PROMPT.replace("{context}", context_str)
    
    formatted_messages = [{"role": "system", "content": system_prompt}]
    
    last_user_msg = ""
    for m in messages:
        # Aggressively strip any hallucinated loading texts
        content = re.sub(r'[_>*\s]*Fetching live data and planning\.{3}[_>*\s]*', '', m.get("content", ""), flags=re.IGNORECASE).strip()
        if content:
            role = "user" if m.get("role") == "user" else "assistant"
            formatted_messages.append({"role": role, "content": content})
            if role == "user":
                last_user_msg = content

    # UI Button Interceptors - Bypass flaky LLM JSON parsing entirely!
    if "Optimize this cart" in last_user_msg or "Re-optimize this cart" in last_user_msg:
        yield "\n> _Fetching live data and planning..._\n\n"
        # Force flush the WSGI buffer by yielding a large block of whitespace
        yield " " * 1024 + "\n"
        
        tool_result, state_update = execute_tool("optimize_cart", {}, context)
        if state_update:
            yield f"\n<<<STATE_UPDATE>>>{json.dumps(state_update)}<<<END_STATE_UPDATE>>>\n"
        
        # Inject tool result into history so the LLM just summarizes it
        formatted_messages.append({
            "role": "user",
            "content": f"Tool 'optimize_cart' returned:\n{tool_result}\n\nPlease summarize these results for me."
        })

    max_loops = 5
    loop_count = 0
    
    while loop_count < max_loops:
        loop_count += 1
        
        try:
            response = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "mistral",
                    "messages": formatted_messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.1
                    }
                },
                timeout=90
            )
            response.raise_for_status()
            
            msg = response.json().get("message", {})
            assistant_content = msg.get("content", "").strip()
            
            tool_calls = []
            
            # Parse standard ```json tool calls
            matches = re.finditer(r'```json\s*(.*?)\s*```', assistant_content, re.DOTALL)
            for match in matches:
                try:
                    tc = json.loads(match.group(1).strip())
                    if "tool" in tc:
                        tool_calls.append({
                            "name": tc["tool"],
                            "args": {k: v for k, v in tc.items() if k != "tool"}
                        })
                except Exception as e:
                    logger.error(f"Failed to parse TOOL_CALL JSON: {e}")
                    # Fallback if JSON is malformed but we know it's a tool call
                    text_content = match.group(1).strip()
                    if '"optimize_cart"' in text_content or 'optimize_cart' in text_content:
                        tool_calls.append({
                            "name": "optimize_cart",
                            "args": {}
                        })
                    elif '"generate_shopping_plan"' in text_content:
                        # We can't really fallback easily without the goal, but we can try to extract it
                        goal_match = re.search(r'"goal":\s*"([^"]+)"', text_content)
                        if goal_match:
                            tool_calls.append({
                                "name": "generate_shopping_plan",
                                "args": {"goal": goal_match.group(1)}
                            })
                            
            # Global fallback if NO tools were parsed via code blocks (Mistral often forgets backticks)
            if not tool_calls:
                if re.search(r'"tool"\s*:\s*"optimize_cart"', assistant_content, re.IGNORECASE):
                    tool_calls.append({
                        "name": "optimize_cart",
                        "args": {}
                    })
                elif re.search(r'"tool"\s*:\s*"generate_shopping_plan"', assistant_content, re.IGNORECASE):
                    goal_match = re.search(r'"goal":\s*"([^"]+)"', assistant_content)
                    if goal_match:
                        tool_calls.append({
                            "name": "generate_shopping_plan",
                            "args": {"goal": goal_match.group(1)}
                        })
                    
            # Remove tool calls from assistant content so they aren't shown to user
            assistant_content = re.sub(r'```json\s*.*?\s*```', '', assistant_content, flags=re.DOTALL)
            assistant_content = re.sub(r'\{.*"tool":.*\}', '', assistant_content, flags=re.DOTALL | re.IGNORECASE).strip()
            
            # Yield and accumulate text content smoothly
            if assistant_content and not tool_calls:
                chunks = re.split(r'(\s+)', assistant_content)
                for chunk in chunks:
                    if chunk:
                        yield chunk
                        time.sleep(0.01)
            
            # Append the assistant's response to the history
            if assistant_content or tool_calls:
                formatted_messages.append({
                    "role": "assistant",
                    "content": msg.get("content", "").strip() # Original content with tags so model remembers
                })
                
            # If there are tool calls, execute them and continue the loop
            if tool_calls:
                # Give the user a hint that we're thinking
                yield "\n> _Fetching live data and planning..._\n\n"
                
                for tc in tool_calls:
                    name = tc["name"]
                    args = tc["args"]
                    
                    tool_result, state_update = execute_tool(name, args, context)
                    
                    if state_update:
                        # Yield special token for frontend to parse state changes silently
                        yield f"\n<<<STATE_UPDATE>>>{json.dumps(state_update)}<<<END_STATE_UPDATE>>>\n"
                    
                    formatted_messages.append({
                        "role": "user",
                        "content": f"Tool '{name}' returned:\n{tool_result}\n\nNow summarize this information for the user."
                    })
                # Loop continues and sends the tool results back to the model
            else:
                # No tool calls, we are done
                break
                
        except Exception as e:
            logger.error(f"Chatbot failed: {e}")
            yield f"\nI'm having trouble connecting to my brain right now. ({str(e)})"
            break
