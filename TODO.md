# TODO: Git Resolution Performance Improvements

This document outlines recommended performance improvements for the dependency resolution
process, specifically targeting git-related operations that are currently bottlenecks.

## Summary of Current Issues

The resolution process makes numerous git subprocess calls without caching, leading to:
- Repeated network requests to the same remote repositories
- Redundant cloning operations when manifests need to be fetched
- Sequential processing where parallel operations could be used

## High Priority Improvements

### 1. ~~Add LRU Cache to `get_remote_refs()`~~ ✓ COMPLETED

**File:** `src/fastsandpm/_git_utils.py:295`

**Status:** Implemented. Added `@lru_cache(maxsize=128)` decorator and changed return
type to use `frozenset` for hashability. Updated `candidates.py` to use compatible types.

---

### 2. ~~Cache `GitCandidate.get_manifest()` Results~~ ✓ COMPLETED

**File:** `src/fastsandpm/dependencies/candidates.py:173-215`

**Status:** Implemented. Created `_fetch_git_manifest_cached()` function with
`@lru_cache(maxsize=256)` decorator. The `GitCandidate.get_manifest()` method now
delegates to this cached function. Updated test fixture to clear cache between tests.

---

### 3. ~~Use GitHub/GitLab REST APIs Instead of Clone Fallback~~ ✓ COMPLETED

**File:** `src/fastsandpm/dependencies/candidates.py:173-320`

**Status:** Implemented. Added the following functions:
- `_parse_github_url()` - Parses GitHub URLs (HTTPS, SSH, SSH protocol formats)
- `_parse_gitlab_url()` - Parses GitLab URLs including self-hosted instances
- `_fetch_file_from_github()` - Fetches files via `raw.githubusercontent.com`
- `_fetch_file_from_gitlab()` - Fetches files via GitLab's repository files API
- `_fetch_manifest_from_hosting_api()` - Orchestrates the API fetching

The `_fetch_git_manifest_cached()` function now tries methods in this order:
1. `git archive --remote` (fastest, but not supported by GitHub)
2. Hosting provider REST APIs (GitHub/GitLab)
3. Full git clone (slowest, but universal fallback)

Added 14 new tests covering URL parsing and API integration.

---

## Medium Priority Improvements

### 4. Batch Local Git Operations in `PathCandidate.satisfies()`

**File:** `src/fastsandpm/dependencies/candidates.py:130-165`

**Problem:** Multiple sequential git subprocess calls during validation:
- `is_git_repo()` - 1 call
- `get_head_commit()` or `get_current_branch()` or `get_tags_at_head()` - additional calls

**Solution:** Create a single function that retrieves all needed git state in one
subprocess call using `git show` or a custom format string:

```python
def get_repo_state(repo: pathlib.Path) -> dict:
    """Get comprehensive repo state in a single git call."""
    result = subprocess.run(
        ["git", "rev-parse", "HEAD", "--abbrev-ref", "HEAD"],
        cwd=repo,
        capture_output=True
    )
    # Parse and return dict with commit, branch, etc.
```

**Estimated Impact:** Medium - reduces subprocess overhead for local validation.

---

### 5. Parallel Remote Checking for Unqualified Git Requirements

**File:** `src/fastsandpm/dependencies/candidates.py:379-389`

**Problem:** When a GitRequirement doesn't have a fully qualified URL, remotes are
tried sequentially. Failed attempts still incur network latency.

**Solution:** Use `concurrent.futures.ThreadPoolExecutor` to check multiple remotes
in parallel:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _find_accessible_remote(remotes: list[str]) -> tuple[str, dict] | None:
    """Find first accessible remote in parallel."""
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_git_utils.get_remote_refs, r): r for r in remotes}
        for future in as_completed(futures):
            try:
                refs = future.result()
                return (futures[future], refs)
            except ValueError:
                continue
    return None
```

**Estimated Impact:** Medium - improves resolution time when registry search is needed.

---

### 6. Add `remote_exists()` Result Caching

**File:** `src/fastsandpm/_git_utils.py:101-113`

**Problem:** `remote_exists()` makes a `git ls-remote` call that could be cached.

**Solution:** Add `@lru_cache` decorator:

```python
@lru_cache(maxsize=256)
def remote_exists(remote: str) -> bool:
    ...
```

**Estimated Impact:** Low-Medium - prevents repeated accessibility checks.

---

## Low Priority Improvements

### 7. Replace `shell=True` in `get_remote_file()`

**File:** `src/fastsandpm/_git_utils.py:282-286`

**Problem:** Uses `shell=True` with piping, which has slight overhead and security
implications.

**Solution:** Use Python's `subprocess.PIPE` to chain processes without shell:

```python
def get_remote_file(remote: str, treeish: str, path: str) -> bytes:
    git_proc = subprocess.Popen(
        ["git", "archive", f"--remote={remote}", treeish, "--", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    tar_proc = subprocess.Popen(
        ["tar", "-xO"],
        stdin=git_proc.stdout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    git_proc.stdout.close()
    output, _ = tar_proc.communicate()
    ...
```

**Estimated Impact:** Low - minor security and performance improvement.

---

### 8. Implement Persistent Disk Cache for Manifests

**Problem:** In-memory caches are lost between runs. For large projects with many
dependencies, re-fetching manifests on every `fspm install` is wasteful.

**Solution:** Implement a disk-based cache in `~/.cache/fspm/` or `.fspm-cache/`:

```
~/.cache/fspm/
  manifests/
    {commit_hash}.toml    # Cached manifest files
  refs/
    {remote_hash}.json    # Cached remote refs with TTL
```

**Estimated Impact:** Medium for repeated runs - significant for CI/CD workflows.

---

### 9. Add Cache Invalidation Strategy

Consider adding:
- TTL (time-to-live) for remote refs cache (e.g., 5 minutes)
- Manual cache clear command (`fspm cache clear`)
- Automatic invalidation when `--fresh` flag is used

---

## Implementation Order Recommendation

1. **Quick wins (1-2 hours each):**
   - Item 1: `@lru_cache` on `get_remote_refs()`
   - Item 6: `@lru_cache` on `remote_exists()`

2. **Medium effort (4-8 hours):**
   - Item 3: GitHub/GitLab API fallback for manifest fetching
   - Item 2: In-memory manifest caching

3. **Larger effort (1-2 days):**
   - Item 5: Parallel remote checking
   - Item 4: Batched local git operations
   - Item 8: Persistent disk cache

---

## Metrics to Track

Before implementing, consider adding timing instrumentation to measure:
- Total time spent in git subprocess calls
- Number of `git ls-remote` calls per resolution
- Number of full clones performed
- Cache hit/miss rates (once caching is implemented)
