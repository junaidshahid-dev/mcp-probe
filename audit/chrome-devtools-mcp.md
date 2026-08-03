# MCP audit - `node audit/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js --isolated`

**Score: 100/100 (grade A)** · 29 tools · 0 fail / 0 warn / 13 info / 240 ok

| Tool | Check | Severity | Detail |
|---|---|---|---|
| `click` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `drag` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `evaluate_script` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `fill` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `get_console_message` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `handle_dialog` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `hover` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `lighthouse_audit` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `navigate_page` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `press_key` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `take_heapsnapshot` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `upload_file` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `wait_for` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |

## Tools discovered

- **`click`** - Clicks on the provided element (3 params, 1 required)
- **`close_page`** - Closes the page by its index. The last open page cannot be closed. (1 params, 1 required)
- **`drag`** - Drag an element onto another element (3 params, 2 required)
- **`emulate`** - Emulates various features on the selected page. (7 params, 0 required)
- **`evaluate_script`** - Evaluate a JavaScript function inside the currently selected page. Returns the response as JSON, so returned values have to be JSON-serializable. (4 params, 1 required)
- **`fill`** - Type text into an input, text area or select an option from a <select> element. (3 params, 2 required)
- **`fill_form`** - Fill out multiple form elements (inputs, selects, checkboxes, radios) at once. ALWAYS prefer this tool over multiple individual 'fill' or 'click' calls when interacting with forms. It is significantly faster, more reliable, and reduces turn count. Example: Fill username, password, and check "Remember Me" in one call. (2 params, 1 required)
- **`get_console_message`** - Gets a console message by its ID. You can get all messages by calling list_console_messages. (1 params, 1 required)
- **`get_network_request`** - Gets a network request by an optional reqid, if omitted returns the currently selected request in the DevTools Network panel. (3 params, 0 required)
- **`handle_dialog`** - If a browser dialog was opened, use this command to handle it (2 params, 1 required)
- **`hover`** - Hover over the provided element (2 params, 1 required)
- **`lighthouse_audit`** - Get Lighthouse score and reports for accessibility, SEO, best practices, and agentic browsing. This excludes performance. For performance audits, run performance_start_trace (3 params, 0 required)
- **`list_console_messages`** - List all console messages for the currently selected page since the last navigation. (5 params, 0 required)
- **`list_network_requests`** - List all requests for the currently selected page since the last navigation. (4 params, 0 required)
- **`list_pages`** - Get a list of pages open in the browser. (0 params, 0 required)
- **`navigate_page`** - Go to a URL, or back, forward, or reload. Use project URL if not specified otherwise. (6 params, 0 required)
- **`new_page`** - Open a new tab and load a URL. Use project URL if not specified otherwise. (4 params, 1 required)
- **`performance_analyze_insight`** - Provides more detailed information on a specific Performance Insight of an insight set that was highlighted in the results of a trace recording. (2 params, 2 required)
- **`performance_start_trace`** - Start a performance trace on the selected webpage. Use to find frontend performance issues, Core Web Vitals (LCP, INP, CLS), and improve page load speed. (3 params, 0 required)
- **`performance_stop_trace`** - Stop the active performance trace recording on the selected webpage. (1 params, 0 required)
- **`press_key`** - Press a key or key combination. Use this when other input methods like fill() cannot be used (e.g., keyboard shortcuts, navigation keys, or special key combinations). (2 params, 1 required)
- **`resize_page`** - Resizes the selected page's window so that the page has specified dimension (2 params, 2 required)
- **`select_page`** - Select a page as a context for future tool calls. (2 params, 1 required)
- **`take_heapsnapshot`** - Capture a heap snapshot of the currently selected page. Use to analyze the memory distribution of JavaScript objects and debug memory leaks. (1 params, 1 required)
- **`take_screenshot`** - Take a screenshot of the page or element. (5 params, 0 required)
- **`take_snapshot`** - Take a text snapshot of the currently selected page based on the a11y tree. The snapshot lists page elements along with a unique
identifier (uid). Always use the latest snapshot. Prefer taking a snapshot over taking a screenshot. The snapshot indicates the element selected
in the DevTools Elements panel (if any). (2 params, 0 required)
- **`type_text`** - Type text using keyboard into a previously focused input (2 params, 1 required)
- **`upload_file`** - Upload a file through a provided element. (3 params, 2 required)
- **`wait_for`** - Wait for the specified text to appear on the selected page. (2 params, 1 required)

---
_Generated by [mcp-probe](https://github.com/junaidshahid-dev/mcp-probe)._