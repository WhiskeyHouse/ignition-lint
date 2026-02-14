---
sidebar_position: 3
title: Editor Integration
---

# Editor Integration

Integrate ignition-lint directly into your editor for real-time feedback and faster development. This guide covers VS Code, Neovim, and LSP-compatible editors.

## VS Code

### JSON Schema Validation

Add schema-based validation for `view.json` files to get real-time error detection and autocomplete.

#### Option 1: Workspace settings

Create or edit `.vscode/settings.json` in your project root:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/perspective/views/**/view.json"],
      "url": "./schemas/core-ia-components-schema-robust.json"
    }
  ]
}
```

If you installed ignition-lint via pip, find the schema path:

```bash
python -c "from ignition_lint.schemas import schema_path_for; print(schema_path_for('robust'))"
```

Then use the absolute path as the `url`:

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/perspective/views/**/view.json"],
      "url": "/absolute/path/to/core-ia-components-schema-robust.json"
    }
  ]
}
```

#### Option 2: User settings

For global configuration across all projects, add to User Settings (Cmd+Shift+P → "Preferences: Open User Settings (JSON)"):

```json
{
  "json.schemas": [
    {
      "fileMatch": ["**/perspective/views/**/view.json"],
      "url": "/Users/yourname/.local/lib/python3.11/site-packages/ignition_lint/schemas/core-ia-components-schema-robust.json"
    }
  ]
}
```

### Linting on Save

Run ignition-lint automatically when you save a file:

1. Install the [Run on Save](https://marketplace.visualstudio.com/items?itemName=emeraldwalk.RunOnSave) extension

2. Add to `.vscode/settings.json`:

```json
{
  "emeraldwalk.runonsave": {
    "commands": [
      {
        "match": "view\\.json$",
        "cmd": "ignition-lint --target ${file} --report-format text"
      }
    ]
  }
}
```

Now every time you save a `view.json`, ignition-lint runs in the terminal.

### Tasks Integration

Add ignition-lint as a VS Code task for quick access.

Create or edit `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Lint Ignition Project",
      "type": "shell",
      "command": "ignition-lint",
      "args": [
        "--project",
        "${workspaceFolder}",
        "--profile",
        "full"
      ],
      "problemMatcher": [],
      "group": {
        "kind": "test",
        "isDefault": true
      }
    },
    {
      "label": "Lint Current View",
      "type": "shell",
      "command": "ignition-lint",
      "args": [
        "--target",
        "${file}"
      ],
      "problemMatcher": []
    }
  ]
}
```

Run with:
- **Cmd+Shift+B** (or **Ctrl+Shift+B**) to lint the full project
- **Tasks: Run Task** → **Lint Current View** to lint the active file

### Snippets for Suppression

Add snippets for quick suppression comments in Python files.

Create `.vscode/python.code-snippets`:

```json
{
  "Ignition Lint Disable": {
    "prefix": "igdisable",
    "body": [
      "# ignition-lint: disable=$1"
    ],
    "description": "Disable ignition-lint for the next line"
  },
  "Ignition Lint Disable Next": {
    "prefix": "igdisablenext",
    "body": [
      "# ignition-lint: disable-next=$1"
    ],
    "description": "Disable ignition-lint rule for next line"
  },
  "Ignition Lint Disable File": {
    "prefix": "igdisablefile",
    "body": [
      "# ignition-lint: disable-file"
    ],
    "description": "Disable ignition-lint for entire file"
  }
}
```

Now type `igdisable` and press **Tab** to insert a suppression comment.

---

## Neovim + ignition-nvim

[ignition-nvim](https://github.com/thePeras/ignition-nvim) is a Neovim plugin for Ignition development. Integrate ignition-lint for enhanced diagnostics.

### Prerequisites

- Neovim 0.9+
- [ignition-nvim](https://github.com/thePeras/ignition-nvim) plugin
- ignition-lint-toolkit installed globally or in project venv

### Setup with lazy.nvim

Add to your `plugins.lua` or `init.lua`:

```lua
return {
  -- ignition-nvim for Ignition project support
  {
    'thePeras/ignition-nvim',
    ft = { 'python', 'json' },
    config = function()
      require('ignition').setup({
        -- Enable ignition-lint integration
        linter = {
          enabled = true,
          cmd = 'ignition-lint',
          args = {
            '--target',
            vim.fn.getcwd(),
            '--report-format',
            'json'
          }
        }
      })
    end
  },

  -- Optionally add diagnostics integration
  {
    'jose-elias-alvarez/null-ls.nvim',
    dependencies = { 'nvim-lua/plenary.nvim' },
    config = function()
      local null_ls = require('null-ls')

      null_ls.setup({
        sources = {
          -- Add ignition-lint as a diagnostics source
          null_ls.builtins.diagnostics.ignition_lint.with({
            command = 'ignition-lint',
            args = { '--target', '$FILENAME', '--report-format', 'json' },
            filetypes = { 'json' },
            -- Only run on view.json files
            runtime_condition = function(params)
              return params.bufname:match('view%.json$')
            end
          })
        }
      })
    end
  }
}
```

### Manual Lint Command

Add a custom command to lint the current buffer or project:

```lua
-- Add to your init.lua or ftplugin/json.lua

-- Lint current file
vim.api.nvim_create_user_command('IgnitionLintFile', function()
  local file = vim.fn.expand('%:p')
  if file:match('view%.json$') then
    vim.cmd('!ignition-lint --target ' .. file)
  else
    print('Not a view.json file')
  end
end, {})

-- Lint entire project
vim.api.nvim_create_user_command('IgnitionLintProject', function()
  vim.cmd('!ignition-lint --project ' .. vim.fn.getcwd() .. ' --profile full')
end, {})

-- Keybindings
vim.keymap.set('n', '<leader>lf', ':IgnitionLintFile<CR>', { desc = 'Lint current Ignition view' })
vim.keymap.set('n', '<leader>lp', ':IgnitionLintProject<CR>', { desc = 'Lint Ignition project' })
```

Now use:
- `<leader>lf` to lint the current view
- `<leader>lp` to lint the entire project

### Lint on Save (Neovim)

Automatically lint Perspective views when you save:

```lua
-- Add to ftplugin/json.lua or autocmd
vim.api.nvim_create_autocmd('BufWritePost', {
  pattern = '*view.json',
  callback = function()
    local file = vim.fn.expand('%:p')
    vim.fn.jobstart({'ignition-lint', '--target', file}, {
      on_exit = function(_, code)
        if code == 0 then
          print('✓ ignition-lint passed')
        else
          print('✗ ignition-lint found issues')
        end
      end
    })
  end
})
```

---

## LSP Integration

For editors with LSP support (VS Code, Neovim, Sublime, Emacs), you can create a custom LSP server wrapper around ignition-lint.

### Custom LSP Server (Proof of Concept)

Create `ignition-lint-lsp.py`:

```python
#!/usr/bin/env python3
"""
Minimal LSP server wrapping ignition-lint.
Provides diagnostics for view.json files.
"""
import json
import subprocess
from pathlib import Path

from pygls.server import LanguageServer
from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
    TEXT_DOCUMENT_DID_SAVE,
)

server = LanguageServer('ignition-lint-lsp', 'v0.1')

SEVERITY_MAP = {
    'ERROR': DiagnosticSeverity.Error,
    'WARNING': DiagnosticSeverity.Warning,
    'INFO': DiagnosticSeverity.Information,
    'STYLE': DiagnosticSeverity.Hint,
}


def lint_file(file_path: str) -> list[Diagnostic]:
    """Run ignition-lint and convert to LSP diagnostics."""
    try:
        result = subprocess.run(
            ['ignition-lint', '--target', file_path, '--report-format', 'json'],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode not in (0, 1):  # 0 = no issues, 1 = issues found
            return []

        report = json.loads(result.stdout)
        diagnostics = []

        for issue in report.get('issues', []):
            line = issue.get('line', 1) - 1  # LSP uses 0-based indexing
            severity = SEVERITY_MAP.get(issue['severity'], DiagnosticSeverity.Information)

            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=line, character=0),
                    end=Position(line=line, character=100)
                ),
                message=f"[{issue['code']}] {issue['message']}",
                severity=severity,
                source='ignition-lint'
            ))

        return diagnostics
    except Exception as e:
        server.show_message_log(f'ignition-lint error: {e}')
        return []


@server.feature(TEXT_DOCUMENT_DID_SAVE)
def did_save(ls: LanguageServer, params):
    """Lint file on save."""
    uri = params.text_document.uri
    file_path = uri.replace('file://', '')

    if not file_path.endswith('view.json'):
        return

    diagnostics = lint_file(file_path)
    ls.publish_diagnostics(uri, diagnostics)


if __name__ == '__main__':
    server.start_io()
```

Install dependencies:
```bash
pip install pygls lsprotocol
```

Make executable:
```bash
chmod +x ignition-lint-lsp.py
```

### Neovim LSP Configuration

Add to your Neovim config:

```lua
-- Add to ~/.config/nvim/lua/lsp/ignition.lua

local lspconfig = require('lspconfig')
local configs = require('lspconfig.configs')

-- Define custom ignition-lint LSP
if not configs.ignition_lint then
  configs.ignition_lint = {
    default_config = {
      cmd = { '/path/to/ignition-lint-lsp.py' },
      filetypes = { 'json' },
      root_dir = lspconfig.util.root_pattern('.git', 'ignition.project'),
      settings = {},
    },
  }
end

-- Enable for view.json files
vim.api.nvim_create_autocmd('FileType', {
  pattern = 'json',
  callback = function()
    local bufname = vim.api.nvim_buf_get_name(0)
    if bufname:match('view%.json$') then
      lspconfig.ignition_lint.setup({
        on_attach = function(client, bufnr)
          -- Enable diagnostics
          vim.diagnostic.enable(bufnr)
        end
      })
    end
  end
})
```

Now you get real-time diagnostics in Neovim!

---

## Other Editors

### Sublime Text

Use [LSP package](https://packagecontrol.io/packages/LSP) with the custom LSP server above.

Add to LSP settings:

```json
{
  "clients": {
    "ignition-lint": {
      "enabled": true,
      "command": ["/path/to/ignition-lint-lsp.py"],
      "selector": "source.json",
      "schemes": ["file"]
    }
  }
}
```

### Emacs

Use `lsp-mode` with the custom LSP server.

Add to your Emacs config:

```elisp
(with-eval-after-load 'lsp-mode
  (add-to-list 'lsp-language-id-configuration '(json-mode . "ignition-lint"))

  (lsp-register-client
   (make-lsp-client
    :new-connection (lsp-stdio-connection "/path/to/ignition-lint-lsp.py")
    :major-modes '(json-mode)
    :server-id 'ignition-lint
    :activation-fn (lambda (filename &optional _)
                    (string-match "view\\.json$" filename)))))
```

---

## Tips

### Schema Modes

Choose the right schema mode for your needs:

- **`strict`** — Only core IA components, strictest validation
- **`robust`** (default) — Production-tested components from real projects
- **`permissive`** — Allow any component type, minimal validation

Set in CLI:
```bash
ignition-lint --target ./views --schema-mode permissive
```

Or in editor integrations, pass as argument.

### Performance

For large projects with thousands of files:

- Use `--component` filter to lint specific component types
- Enable linting on save only (not on every keystroke)
- Consider running full project lints in CI only, not locally

### Troubleshooting

**"Schema file not found"**
- Ensure ignition-lint-toolkit is installed in the same Python environment
- Check schema path with: `python -c "from ignition_lint.schemas import schema_path_for; print(schema_path_for('robust'))"`

**"LSP server not starting"**
- Verify Python path in LSP command
- Check LSP server logs (location varies by editor)
- Test manually: `/path/to/ignition-lint-lsp.py` should not exit immediately

**"Diagnostics not showing"**
- Ensure file matches `**/view.json` pattern
- Check that ignition-lint is in PATH or use absolute path in config

---

## Next Steps

- **[CLI Reference](../guides/cli-reference)** — Full command-line options
- **[Rule Codes](../guides/rule-codes)** — Understanding what gets flagged
- **[Suppression](../guides/suppression)** — Control which rules fire where

---

**Have a cool editor integration?** [Share it with the community!](https://github.com/TheThoughtagen/ignition-lint/discussions)
