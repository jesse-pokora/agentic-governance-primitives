# argv-not-shell-invocation

**Atomic claim:** A child process is launched from an absolute program path
and a list of argument values, so a shell metacharacter inside an argument
arrives as literal text — never as a second command.

**Inspired by:** no-shell launch contracts in governed agent hosts (named for
context; this app does not import or depend on any other source). Tier 1,
v1.3.

**Enforcement class:** deterministic — a shape check on the invocation, and
`shell=False` with no exceptions.

## How it works

The check is not "does this argument look dangerous". It is "is this argument
ever interpreted", and the answer is no, by construction. Sanitizing a shell
string is a guess about a grammar — quoting rules, escaping, locale, which
shell — and every such guess has been wrong at least once. Not building a
string is a fact about the grammar instead of a guess.

`build_invocation` refuses the two shapes that reintroduce a shell:

- **`relative_program`** — a bare name resolves through `PATH`, so it names a
  different file depending on where and how the process was started. There is
  a test that prepends a temp directory to `PATH` and shows an absolute path
  cannot be redirected that way. (Pinning *which* absolute file is
  [hash-pinned-identity](../hash-pinned-identity)'s job; this app pins the
  *shape* of the launch.)
- **`shell_string_argument`** — a single string standing in for the whole
  command line. Something has to parse that back into a process, and that
  something is a shell.

The demonstration is a real child process: this interpreter, echoing its own
`argv` back as JSON. An argument containing
`toy; rm -rf /tmp/nothing && echo pwned | cat > /tmp/out` comes back as one
argument, unsplit, because nothing ever parsed it.

**The no-shell property is tested by parsing this module, not grepping it.**
The prose above mentions `shell=True` in order to say it is never used, and a
substring search cannot tell the difference between describing a thing and
doing it — so the test walks the AST looking for a `shell=True` keyword and
for `os.system` / `os.popen` calls. Same lesson as
[generated-code-admission-gate](../generated-code-admission-gate): parse,
don't grep.

## Run it

```bash
cd apps/argv-not-shell-invocation
python -m unittest test_invocation.py -v
```

All ten tests launch real child processes: arguments arriving intact, shell
metacharacters as literal text, a flag-shaped argument, a relative program, a
command-line string, an empty program, a non-string argument, a `PATH`
lookalike, the AST check, and a child exit code proving it really ran.
