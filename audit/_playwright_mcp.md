# MCP audit - `node audit/node_modules/@playwright/mcp/cli.js`

**Score: 97/100 (grade A)** · 24 tools · 0 fail / 4 warn / 14 info / 197 ok

| Tool | Check | Severity | Detail |
|---|---|---|---|
| `browser_console_messages` | missing-required | **warn** | accepted clearly-invalid input (omit required 'level') - not validating |
| `browser_handle_dialog` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_evaluate` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_file_upload` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_drop` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_find` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_press_key` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_type` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_navigate_back` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_network_requests` | missing-required | **warn** | accepted clearly-invalid input (omit required 'static') - not validating |
| `browser_run_code_unsafe` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_take_screenshot` | missing-required | **warn** | accepted clearly-invalid input (omit required 'type') - not validating |
| `browser_take_screenshot` | missing-required | **warn** | accepted clearly-invalid input (omit required 'scale') - not validating |
| `browser_click` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_drag` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_hover` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_select_option` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |
| `browser_wait_for` | valid-baseline | **info** | declined minimal valid input - likely needs semantically real values (e.g. an existing path/id), not a defect |

## Tools discovered

- **`browser_close`** - Close the page (0 params, 0 required)
- **`browser_resize`** - Resize the browser window (2 params, 2 required)
- **`browser_console_messages`** - Returns all console messages (3 params, 1 required)
- **`browser_handle_dialog`** - Handle a dialog (2 params, 1 required)
- **`browser_evaluate`** - Evaluate JavaScript expression on page or element (4 params, 1 required)
- **`browser_file_upload`** - Upload one or multiple files (1 params, 0 required)
- **`browser_drop`** - Drop files or MIME-typed data onto an element, as if dragged from outside the page. At least one of "paths" or "data" must be provided. (4 params, 1 required)
- **`browser_find`** - Search the accessibility snapshot of the current page for text or a regular expression. Returns matching snapshot nodes with a few lines of surrounding context (like search snippets), each shown under its path from the root of the tree, which is cheaper than capturing the whole snapshot when you only need to locate an element and its ref. (2 params, 0 required)
- **`browser_fill_form`** - Fill multiple form fields (1 params, 1 required)
- **`browser_press_key`** - Press a key on the keyboard (1 params, 1 required)
- **`browser_type`** - Type text into editable element (5 params, 2 required)
- **`browser_navigate`** - Navigate to a URL (1 params, 1 required)
- **`browser_navigate_back`** - Go back to the previous page in the history (0 params, 0 required)
- **`browser_network_requests`** - Returns a numbered list of network requests since loading the page. Use browser_network_request with the number to get full details. (3 params, 1 required)
- **`browser_network_request`** - Returns full details (headers and body) of a single network request, or a single part if `part` is set. Use the number from browser_network_requests. (3 params, 1 required)
- **`browser_run_code_unsafe`** - Run a Playwright code snippet. Unsafe: executes arbitrary JavaScript in the Playwright server process and is RCE-equivalent. (2 params, 0 required)
- **`browser_take_screenshot`** - Take a screenshot of the current page. You can't perform actions based on the screenshot, use browser_snapshot for actions. (6 params, 2 required)
- **`browser_snapshot`** - Capture accessibility snapshot of the current page, this is better than screenshot (4 params, 0 required)
- **`browser_click`** - Perform click on a web page (5 params, 1 required)
- **`browser_drag`** - Perform drag and drop between two elements (4 params, 2 required)
- **`browser_hover`** - Hover over element on page (2 params, 1 required)
- **`browser_select_option`** - Select an option in a dropdown (3 params, 2 required)
- **`browser_tabs`** - List, create, close, or select a browser tab. (3 params, 1 required)
- **`browser_wait_for`** - Wait for text to appear or disappear or a specified time to pass (3 params, 0 required)

---
_Generated by [mcp-probe](https://github.com/junaidshahid-dev/mcp-probe)._