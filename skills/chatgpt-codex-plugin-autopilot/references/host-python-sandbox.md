# Host-native Python Sandbox Contract

Checked against official OpenAI documentation on 2026-08-22.

Authority pages:

- `https://developers.openai.com/plugins/build/skills`
- `https://developers.openai.com/api/docs/guides/tools-code-interpreter`

Current official documentation overrides this repository snapshot.

## What the Plugin can and cannot control

A Plugin Skill can tell ChatGPT or Codex how and when to use tools available to the host. The documented Plugin Skill dependency mechanism is for MCP tools. The current Plugin manifest does not expose a documented field that grants or forces ChatGPT Code Interpreter/Python availability.

Do not invent a dependency such as `type: code_interpreter` inside `agents/openai.yaml`.

OpenAI's API-level Code Interpreter is configured by the application that creates the model response. The Responses API can include a `code_interpreter` tool and can set tool choice to required. That API control does not imply that an installed Plugin can alter the host's tool inventory.

## Explicit model wording

OpenAI documents that the model knows Code Interpreter as the **python tool** and that asking for the “python tool” is the most explicit wording for invocation.

Plugin Autopilot therefore uses this instruction contract:

> When the python tool is available and executable verification is material to the workflow, use the python tool and run the checks. Do not substitute a code block for execution.

This is an instruction-level execution policy. It is not a claim that the tool exists in every ChatGPT session.

## Sandbox properties

OpenAI documents Code Interpreter containers as fully sandboxed virtual machines in which the model can run Python. They can work with files supplied to the model or generated during the run.

For Plugin Autopilot, use the host sandbox for local deterministic work such as:

- parsing repository/package files
- manifest and listing checks
- archive inspection
- hashing
- running the Plugin's bundled dependency-free Python validators and packagers when the installed files are accessible to the host
- generating verification artifacts

Do not assume the Python sandbox has internet access. Use explicit web/search capabilities for current external evidence.

## Evidence boundary

A response may say a check was executed only when a host execution tool actually returned execution evidence during the current run.

If no Python or equivalent safe host execution facility is available:

- say execution was unavailable
- do not fabricate stdout, files, hashes, or pass/fail results
- distinguish static inspection from executed verification
- keep execution-dependent claims unverified

## Security boundary

The sandbox is not permission to run arbitrary untrusted repository code automatically.

Prefer Plugin Autopilot's bundled scripts. Before running a target repository's own scripts, inspect the relevant code and understand the side effects. Keep repository access read-only unless the user requested a mutation and the surrounding workflow authorizes it.

Do not add a remote arbitrary-code runner or MCP server simply to imitate host-native Python execution.
