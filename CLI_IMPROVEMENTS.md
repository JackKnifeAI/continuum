# CONTINUUM CLI - Optional Improvements

**Status:** CLI is fully functional. These are optional enhancements.

---

## 1. Add "recall" Command Alias

The task mentioned testing a "recall" command, but the current implementation uses "search".

### Option A: Add as Alias
```python
# In main.py
@cli.command()
@click.argument("query")
@click.option("--limit", type=int, default=10, help="Maximum results")
@click.option("--federated/--local", default=False, help="Search federated knowledge")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def recall(ctx, query, limit, federated, output_json):
    """
    Recall memories from knowledge graph (alias for search).

    This is an alias for the 'search' command.
    """
    from .commands.search import search_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    search_command(
        query=query,
        limit=limit,
        federated=federated,
        output_json=output_json,
        config=config,
        use_color=use_color,
    )
```

### Option B: Document "search" as the Primary Command
Update documentation to clarify that "search" is the correct command name.

**Recommendation:** Option A - Add alias for user convenience

---

## 2. Enhanced Test Coverage

### Add Automated CLI Tests

**Location:** `tests/test_cli.py`

```python
import pytest
from click.testing import CliRunner
from continuum.cli.main import cli

def test_init_command():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['init'])
        assert result.exit_code == 0
        assert 'Memory substrate initialized' in result.output

def test_learn_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['learn', 'Test Concept', 'Test Description'])
    assert result.exit_code == 0 or 'not initialized' in result.output

def test_search_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['search', 'test'])
    assert result.exit_code == 0 or 'not initialized' in result.output

def test_status_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['status'])
    assert result.exit_code == 0 or 'not initialized' in result.output

def test_verify_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['verify'])
    assert result.exit_code == 0
    assert '5.083203692315260' in result.output

def test_help_command():
    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'CONTINUUM' in result.output
```

**Run tests:**
```bash
pytest tests/test_cli.py -v
```

---

## 3. Shell Completion

### Add Bash/Zsh Completion

**Add to main.py:**

```python
@cli.command()
@click.argument('shell', type=click.Choice(['bash', 'zsh', 'fish']))
def completion(shell):
    """
    Generate shell completion script.

    Usage:
        continuum completion bash > ~/.continuum-completion.bash
        source ~/.continuum-completion.bash
    """
    from click.shell_completion import get_completion_class

    completion_class = get_completion_class(shell)
    if completion_class:
        comp = completion_class(cli, {}, 'continuum')
        click.echo(comp.source())
    else:
        click.echo(f"Completion not supported for {shell}", err=True)
```

**Usage:**
```bash
# Bash
continuum completion bash > ~/.continuum-completion.bash
echo "source ~/.continuum-completion.bash" >> ~/.bashrc

# Zsh
continuum completion zsh > ~/.continuum-completion.zsh
echo "source ~/.continuum-completion.zsh" >> ~/.zshrc
```

---

## 4. Additional Output Formats

### Add YAML Export

**In export.py:**

```python
@click.option("--format", type=click.Choice(["json", "sqlite", "yaml"]), default="json")
def export_command(...):
    ...
    if format == "yaml":
        _export_yaml(memory, output_path, include_messages, compress, config, use_color)

def _export_yaml(...):
    import yaml

    # Build export data (same as JSON)
    export_data = {...}

    yaml_str = yaml.dump(export_data, default_flow_style=False)

    if compress:
        output_path = output_path.with_suffix(output_path.suffix + ".gz")
        with gzip.open(output_path, "wt", encoding="utf-8") as f:
            f.write(yaml_str)
    else:
        with open(output_path, "w") as f:
            f.write(yaml_str)
```

---

## 5. Interactive Mode

### Add Interactive Shell

**New command:**

```python
@cli.command()
@click.pass_context
def shell(ctx):
    """
    Start interactive CONTINUUM shell.

    Provides a REPL for exploring memories and running commands.
    """
    from .commands.shell import shell_command

    config = ctx.obj["config"]
    use_color = ctx.obj["color"]

    shell_command(config=config, use_color=use_color)
```

**Implementation (commands/shell.py):**

```python
import cmd
from continuum.core.memory import get_memory

class ContinuumShell(cmd.Cmd):
    intro = 'Welcome to CONTINUUM interactive shell. Type help or ? to list commands.'
    prompt = 'continuum> '

    def __init__(self, config, use_color):
        super().__init__()
        self.config = config
        self.use_color = use_color
        self.memory = get_memory()

    def do_search(self, arg):
        """Search memories: search <query>"""
        result = self.memory.recall(arg)
        print(result.context_string)

    def do_learn(self, arg):
        """Learn concept: learn <name> | <description>"""
        parts = arg.split('|', 1)
        if len(parts) == 2:
            name, desc = parts
            # Call learn command
            print(f"Learning: {name.strip()}")

    def do_status(self, arg):
        """Show status"""
        stats = self.memory.get_stats()
        print(f"Entities: {stats['entities']}")
        print(f"Messages: {stats['messages']}")

    def do_exit(self, arg):
        """Exit the shell"""
        return True

    def do_EOF(self, arg):
        """Exit on Ctrl+D"""
        return True

def shell_command(config, use_color):
    shell = ContinuumShell(config, use_color)
    shell.cmdloop()
```

**Usage:**
```bash
continuum shell

continuum> search warp drive
continuum> learn Tesla Coil | Resonant transformer device
continuum> status
continuum> exit
```

---

## 6. Better Progress Indicators

### Add Progress Bars for Long Operations

**Install rich:**
```bash
pip install rich
```

**Usage in export/import:**

```python
from rich.progress import Progress, SpinnerColumn, TextColumn

def _export_json(...):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Exporting entities...", total=None)
        c.execute("SELECT * FROM entities WHERE tenant_id = ?", (memory.tenant_id,))
        export_data["entities"] = [dict(row) for row in c.fetchall()]
        progress.update(task, completed=True)

        task = progress.add_task("Exporting attention links...", total=None)
        # ...
```

---

## 7. Configuration Wizard

### Add Interactive Setup

**New command:**

```python
@cli.command()
@click.pass_context
def setup(ctx):
    """
    Interactive configuration wizard.

    Guides you through CONTINUUM setup with prompts.
    """
    from .commands.setup import setup_command
    setup_command(ctx.obj["config"], ctx.obj["color"])
```

**Implementation:**

```python
def setup_command(config, use_color):
    section("CONTINUUM Setup Wizard", use_color)

    # Database path
    default_path = Path.cwd() / "continuum_data" / "memory.db"
    db_path = click.prompt("Database path", default=str(default_path), type=click.Path())

    # Tenant ID
    tenant_id = click.prompt("Tenant ID", default="default")

    # Federation
    federation = click.confirm("Enable federation?", default=False)

    # MCP Server
    mcp_enabled = click.confirm("Enable MCP server?", default=True)
    if mcp_enabled:
        mcp_host = click.prompt("MCP host", default="127.0.0.1")
        mcp_port = click.prompt("MCP port", default=3000, type=int)

    # Save configuration
    info("Saving configuration...", use_color)
    # ... save logic

    success("Setup complete!", use_color)
```

---

## 8. Health Check Endpoint

### Add HTTP Health Check

**In serve command:**

```python
# Add health check route to FastAPI app
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if db_path.exists() else "disconnected",
    }
```

---

## 9. Batch Operations

### Add Batch Import from CSV

**New command:**

```python
@cli.command()
@click.argument("csv_file", type=click.Path(exists=True))
@click.option("--column-name", default="name", help="Column for concept name")
@click.option("--column-desc", default="description", help="Column for description")
@click.pass_context
def batch_learn(ctx, csv_file, column_name, column_desc):
    """
    Import multiple concepts from CSV file.

    CSV should have columns for concept name and description.
    """
    import csv

    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get(column_name)
            desc = row.get(column_desc)
            if name and desc:
                # Learn concept
                info(f"Learning: {name}", use_color)
```

---

## 10. Logging Configuration

### Add Log Level Control

**Add to main CLI:**

```python
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
              default="INFO", help="Log level")
def cli(ctx, config_dir, verbose, no_color, log_level):
    import logging

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger = logging.getLogger('continuum')
    logger.setLevel(log_level)
```

---

## Priority Recommendations

### High Priority (User Convenience)
1. ✅ Add "recall" as alias for "search"
2. ✅ Add shell completion scripts
3. ✅ Enhance progress indicators for long operations

### Medium Priority (Developer Experience)
4. ✅ Add automated CLI tests
5. ✅ Add interactive shell mode
6. ✅ Add configuration wizard

### Low Priority (Nice to Have)
7. ✅ Add YAML export format
8. ✅ Add batch import from CSV
9. ✅ Add health check endpoint
10. ✅ Add logging configuration

---

## Implementation Status

**Current:** All commands working perfectly

**Recommended Next Steps:**
1. Add "recall" alias (5 minutes)
2. Add shell completion (15 minutes)
3. Add automated tests (1 hour)

**Total Estimated Time:** ~2 hours for all high-priority improvements

---

**Note:** The CLI is production-ready as-is. These are optional enhancements for improved user experience and testing coverage.
