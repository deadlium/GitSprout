#!/usr/bin/env python3
"""
🌱 Graph-Greener & Activity Engine
Automated Git commit, branch, pull request, and merge automation with modern CLI styling.
Supports:
  - Direct Commit Mode (Linear backdated commits)
  - Proportional Branch & Merge Mode (Customize total commits and number of branches!)
"""

import os
import sys
import time
import random
import subprocess
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# ==========================================
# Terminal Styling & Visual Helpers
# ==========================================
class UI:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"

    # Neon Colors
    CYAN    = "\033[38;5;51m"
    GREEN   = "\033[38;5;48m"
    PURPLE  = "\033[38;5;141m"
    YELLOW  = "\033[38;5;220m"
    RED     = "\033[38;5;196m"
    BLUE    = "\033[38;5;39m"
    MAGENTA = "\033[38;5;201m"
    GRAY    = "\033[38;5;245m"
    WHITE   = "\033[38;5;231m"

    @staticmethod
    def banner():
        banner_art = f"""{UI.PURPLE}
  ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗
 ██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║
 ██║  ███╗██████╔╝███████║██████╔╝███████║
 ██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║
 ╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝{UI.RESET}
   {UI.CYAN}⚡ G I T H U B   A C T I V I T Y   E N G I N E ⚡{UI.RESET}
   {UI.GRAY}Automated Commits • Proportional Branching • PRs • Heatmap{UI.RESET}
"""
        print(banner_art)

    @staticmethod
    def badge(label, color=CYAN):
        return f"{color}{UI.BOLD}[{label}]{UI.RESET}"

    @staticmethod
    def header(title):
        print(f"\n{UI.PURPLE}━━━ {UI.BOLD}{title.upper()}{UI.RESET} {UI.PURPLE}" + "━" * (45 - len(title)) + f"{UI.RESET}")

    @staticmethod
    def card(title, lines):
        width = 64
        print(f"{UI.CYAN}╭─ {UI.BOLD}{title}{UI.RESET}{UI.CYAN} " + "─" * max(0, width - len(title) - 4) + "╮" + UI.RESET)
        for line in lines:
            print(f"{UI.CYAN}│{UI.RESET}  {line:<{width - 4}}  {UI.CYAN}│{UI.RESET}")
        print(f"{UI.CYAN}╰" + "─" * (width - 2) + "╯" + UI.RESET)

    @staticmethod
    def progress_bar(iteration, total, prefix="Progress", suffix="", length=28):
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = f"{UI.GREEN}█{UI.RESET}" * filled_length + f"{UI.GRAY}░{UI.RESET}" * (length - filled_length)
        sys.stdout.write(f"\r  {UI.CYAN}⠋{UI.RESET} {prefix} [{bar}] {UI.BOLD}{percent}%{UI.RESET} {UI.GRAY}({iteration}/{total}){UI.RESET} {suffix} ")
        sys.stdout.flush()
        if iteration == total:
            sys.stdout.write("\n")

    @staticmethod
    def success(msg):
        print(f"  {UI.GREEN}✔ {UI.BOLD}{msg}{UI.RESET}")

    @staticmethod
    def info(msg):
        print(f"  {UI.BLUE}ℹ {msg}{UI.RESET}")

    @staticmethod
    def warn(msg):
        print(f"  {UI.YELLOW}▲ {msg}{UI.RESET}")

    @staticmethod
    def error(msg):
        print(f"  {UI.RED}✖ {UI.BOLD}{msg}{UI.RESET}")


# ==========================================
# Commit Message Generator (Realistic)
# ==========================================
COMMIT_TYPES = ["feat", "fix", "refactor", "perf", "docs", "style", "chore"]
COMMIT_SCOPES = ["core", "auth", "api", "ui", "config", "engine", "utils", "storage", "worker"]
COMMIT_SUBJECTS = [
    "implement asynchronous request pipeline",
    "optimize memory buffer allocation",
    "enhance error recovery mechanism",
    "streamline state reconciliation logic",
    "resolve edge case race condition in event loop",
    "update dependency security audit rules",
    "refactor database query index structure",
    "add telemetry latency tracing support",
    "improve cache invalidation policy",
    "harden input parameter sanitation",
    "speed up serialization bench markers",
    "align internal telemetry events format"
]

def generate_realistic_message():
    t = random.choice(COMMIT_TYPES)
    s = random.choice(COMMIT_SCOPES)
    msg = random.choice(COMMIT_SUBJECTS)
    return f"{t}({s}): {msg}", s

def distribute_commits(total, branches):
    """Proportionally divides total commits across given number of branches."""
    base = total // branches
    rem = total % branches
    return [base + (1 if i < rem else 0) for i in range(branches)]


# ==========================================
# Git Shell Operations
# ==========================================
def run_git(args, cwd=".", env=None, check=True):
    """Executes a git command and returns the stripped stdout."""
    res = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if check and res.returncode != 0:
        raise RuntimeError(f"Git error ({' '.join(args)}): {res.stderr.strip()}")
    return res.stdout.strip()

def get_current_branch(repo_path):
    try:
        return run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_path)
    except Exception:
        return "main"

def git_pull(repo_path, branch):
    """Pulls remote changes safely."""
    try:
        UI.info(f"Synchronizing from remote: {UI.BOLD}origin/{branch}{UI.RESET}...")
        out = run_git(["pull", "origin", branch], cwd=repo_path, check=False)
        UI.success(f"Pull complete ({out.splitlines()[0] if out else 'Up-to-date'})")
        return True
    except Exception as e:
        UI.warn(f"Could not pull from remote: {e}")
        return False

def parse_github_remote(repo_path):
    """Parses origin URL into (owner, repo) if it points to GitHub."""
    try:
        url = run_git(["config", "--get", "remote.origin.url"], cwd=repo_path)
        clean_url = url.rstrip(".git")
        if "github.com/" in clean_url:
            parts = clean_url.split("github.com/")[1].split("/")
            return parts[0], parts[1]
        elif "github.com:" in clean_url:
            parts = clean_url.split("github.com:")[1].split("/")
            return parts[0], parts[1]
    except Exception:
        pass
    return None, None


# ==========================================
# GitHub REST API Integration (PR & Merge)
# ==========================================
def github_create_and_merge_pr(owner, repo, token, head_branch, base_branch, title, body=""):
    """
    Creates and merges a Pull Request directly on GitHub via official REST API.
    Returns (pr_number, pr_html_url, merge_sha)
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GraphGreener-App"
    }

    create_pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
    payload = json.dumps({
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body
    }).encode("utf-8")

    req = urllib.request.Request(create_pr_url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            pr_data = json.loads(resp.read().decode())
            pr_number = pr_data["number"]
            pr_html_url = pr_data["html_url"]
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        raise RuntimeError(f"GitHub API PR creation failed: {e.code} - {err_msg}")

    merge_pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/merge"
    merge_payload = json.dumps({
        "commit_title": f"Merge pull request #{pr_number} from {head_branch}",
        "commit_message": f"Automated feature integration via GraphGreener",
        "merge_method": "merge"
    }).encode("utf-8")

    req_merge = urllib.request.Request(merge_pr_url, data=merge_payload, headers=headers, method="PUT")
    try:
        with urllib.request.urlopen(req_merge) as resp:
            merge_data = json.loads(resp.read().decode())
            merge_sha = merge_data.get("sha", "merged")
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode()
        raise RuntimeError(f"GitHub API PR merge failed: {e.code} - {err_msg}")

    return pr_number, pr_html_url, merge_sha


# ==========================================
# Commit Helpers
# ==========================================
def random_date_in_last_year():
    today = datetime.now()
    start_date = today - timedelta(days=365)
    random_days = random.randint(0, 364)
    random_seconds = random.randint(0, 23 * 3600 + 3599)
    return start_date + timedelta(days=random_days, seconds=random_seconds)

def make_commit(date, repo_path, filename, message):
    filepath = os.path.join(repo_path, filename)
    with open(filepath, "a") as f:
        f.write(f"Commit at {date.isoformat()} - {message}\n")
    run_git(["add", filename], cwd=repo_path)
    env = os.environ.copy()
    date_str = date.strftime("%Y-%m-%dT%H:%M:%S")
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str
    run_git(["commit", "-m", message], cwd=repo_path, env=env)


# ==========================================
# Mode 1: Direct Commits
# ==========================================
def execute_direct_commits(repo_path, base_branch, filename, num_commits, custom_msg=""):
    UI.header("Mode: Direct Commits")
    UI.card("Direct Commit Configuration", [
        f"Target Branch: {UI.CYAN}{base_branch}{UI.RESET}",
        f"Total Commits: {UI.YELLOW}{num_commits}{UI.RESET}",
        f"File Modified: {UI.WHITE}{filename}{UI.RESET}"
    ])

    start_time = time.time()
    dates = sorted([random_date_in_last_year() for _ in range(num_commits)])

    for i in range(num_commits):
        c_date = dates[i]
        msg, _ = generate_realistic_message() if not custom_msg else (custom_msg, "custom")
        make_commit(c_date, repo_path, filename, msg)
        UI.progress_bar(i + 1, num_commits, prefix="Committing", suffix=f"{UI.DIM}{c_date.strftime('%Y-%m-%d')}{UI.RESET}")
        time.sleep(0.01)

    UI.info(f"Pushing {num_commits} commits to {UI.BOLD}origin/{base_branch}{UI.RESET}...")
    run_git(["push", "origin", base_branch], cwd=repo_path)
    UI.success(f"Pushed to remote successfully in {time.time() - start_time:.1f}s!")


# ==========================================
# Mode 2: Proportional Branch & Merge Mode
# ==========================================
def execute_branch_and_merge(repo_path, base_branch, filename, total_commits, num_branches, custom_msg=""):
    UI.header("Mode: Proportional Branch & Merge Workflow")
    
    distribution = distribute_commits(total_commits, num_branches)
    owner, repo_name = parse_github_remote(repo_path)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    
    if not token and owner:
        print(f"\n{UI.YELLOW}⚡ GitHub Token (Optional for native online PRs on github.com){UI.RESET}")
        token_input = input(f"  Enter {UI.CYAN}GITHUB_TOKEN{UI.RESET} (press Enter for local-to-remote merge commits): ").strip()
        if token_input:
            token = token_input

    engine_desc = f"{UI.GREEN}GitHub REST API (Online PRs){UI.RESET}" if token else f"{UI.YELLOW}Git Non-Fast-Forward Merge (--no-ff){UI.RESET}"

    dist_str = ", ".join(f"{cnt} in b{i+1}" for i, cnt in enumerate(distribution[:5]))
    if len(distribution) > 5:
        dist_str += f", ... (+{len(distribution)-5} more)"

    UI.card("Workflow Distribution Plan", [
        f"Base Branch:       {UI.CYAN}{base_branch}{UI.RESET}",
        f"Total Commits:     {UI.YELLOW}{total_commits} commits{UI.RESET}",
        f"Total Branches:    {UI.MAGENTA}{num_branches} branches{UI.RESET}",
        f"Proportion/Branch: {UI.WHITE}{dist_str}{UI.RESET}",
        f"Merge Commits:     {UI.YELLOW}{num_branches} merge nodes{UI.RESET}",
        f"Total Activity:    {UI.GREEN}{total_commits + num_branches} total graph points{UI.RESET}",
        f"Merge Engine:      {engine_desc}"
    ])

    start_time = time.time()
    
    # Sort all dates chronologically across the branches
    all_dates = sorted([random_date_in_last_year() for _ in range(total_commits)])
    created_branches = []
    
    print(f"\n{UI.badge('RUN', UI.CYAN)} Processing {num_branches} branches & {total_commits} commits...\n")

    date_idx = 0
    total_commits_done = 0

    for b_idx, count in enumerate(distribution):
        branch_dates = all_dates[date_idx : date_idx + count]
        date_idx += count
        
        scope = random.choice(COMMIT_SCOPES)
        branch_id = f"{int(time.time()) % 10000}-{b_idx+1}"
        feature_branch = f"feat/{scope}-b{branch_id}"
        created_branches.append(feature_branch)

        # 1. Create and checkout the feature branch from base
        run_git(["checkout", "-b", feature_branch, base_branch], cwd=repo_path)

        # 2. Make proportional commits on this feature branch
        for c_date in branch_dates:
            msg, _ = generate_realistic_message() if not custom_msg else (custom_msg, "custom")
            make_commit(c_date, repo_path, filename, msg)
            total_commits_done += 1
            status_suffix = f"{UI.MAGENTA}{feature_branch}{UI.RESET} {UI.DIM}[{total_commits_done}/{total_commits}]{UI.RESET}"
            UI.progress_bar(total_commits_done, total_commits, prefix="Commits", suffix=status_suffix)
            time.sleep(0.01)

        # 3. Pull Request and Merge handling
        pr_merged_via_api = False
        last_date = branch_dates[-1]
        m_date = last_date + timedelta(minutes=random.randint(15, 60))

        if token and owner and repo_name:
            try:
                run_git(["push", "-u", "origin", feature_branch], cwd=repo_path)
                pr_title = f"feat({scope}): batch updates on {feature_branch} ({count} commits)"
                pr_body = f"Automated feature PR containing `{count}` commits into `{base_branch}`."
                pr_num, pr_url, _ = github_create_and_merge_pr(
                    owner=owner,
                    repo=repo_name,
                    token=token,
                    head_branch=feature_branch,
                    base_branch=base_branch,
                    title=pr_title,
                    body=pr_body
                )
                run_git(["checkout", base_branch], cwd=repo_path)
                run_git(["pull", "origin", base_branch], cwd=repo_path)
                pr_merged_via_api = True
            except Exception:
                pass

        if not pr_merged_via_api:
            # Local non-fast-forward merge commit
            run_git(["checkout", base_branch], cwd=repo_path)
            
            env = os.environ.copy()
            m_date_str = m_date.strftime("%Y-%m-%dT%H:%M:%S")
            env["GIT_AUTHOR_DATE"] = m_date_str
            env["GIT_COMMITTER_DATE"] = m_date_str

            pr_number = random.randint(100, 999)
            merge_msg = f"Merge pull request #{pr_number} from {feature_branch}\n\n* {count} commits: {scope} integration"
            run_git(["merge", "--no-ff", feature_branch, "-m", merge_msg], cwd=repo_path, env=env)

    # Push base branch with all merges to origin
    UI.info(f"\nPushing all {num_branches} branches & {total_commits} commits to {UI.BOLD}origin/{base_branch}{UI.RESET}...")
    run_git(["push", "origin", base_branch], cwd=repo_path)
    UI.success(f"Pushed merged {base_branch} to origin/{base_branch}")

    # Branch cleanup option
    print()
    cleanup_choice = input(f"  Clean up local feature branches? (Y/n, default {UI.GREEN}Y{UI.RESET}): ").strip().lower()
    if cleanup_choice in ("", "y", "yes"):
        for b in created_branches:
            try:
                run_git(["branch", "-D", b], cwd=repo_path)
            except Exception:
                pass
        UI.success(f"Cleaned up {len(created_branches)} local feature branches.")

    # Show live git graph in terminal!
    UI.header("Git Graph Visualizer (Recent Commits)")
    try:
        graph_output = run_git(["log", "--graph", "--oneline", f"-n{min(20, total_commits + num_branches * 2)}"], cwd=repo_path)
        print(f"\n{UI.CYAN}{graph_output}{UI.RESET}\n")
    except Exception:
        pass

    UI.success(f"Completed {num_branches} branches, {total_commits} commits, and {num_branches} merges in {time.time() - start_time:.1f}s!")


# ==========================================
# Main Entry Point
# ==========================================
def main():
    UI.banner()

    repo_path = "."
    if not os.path.isdir(os.path.join(repo_path, ".git")):
        UI.error("Current directory is not a Git repository!")
        sys.exit(1)

    base_branch = get_current_branch(repo_path)
    owner, repo_name = parse_github_remote(repo_path)

    repo_info = [
        f"Repository:     {UI.BOLD}{repo_path}{UI.RESET} ({owner}/{repo_name if owner else 'local'})",
        f"Active Branch:  {UI.CYAN}{base_branch}{UI.RESET}",
        f"Remote Origin:  {UI.GREEN + 'Configured' if owner else UI.YELLOW + 'Not Detected'}{UI.RESET}"
    ]
    UI.card("System Telemetry", repo_info)

    # 1. Synchronize with remote on start
    print(f"\n{UI.badge('SYNC', UI.BLUE)} Checking remote updates...")
    git_pull(repo_path, base_branch)

    # 2. Interactive Mode Selection
    print(f"\n{UI.badge('MODE', UI.PURPLE)} {UI.BOLD}Select Operation Workflow:{UI.RESET}")
    print(f"  {UI.CYAN}[1]{UI.RESET} {UI.BOLD}Direct Commit Mode{UI.RESET}          {UI.GRAY}─ Direct linear commits on '{base_branch}' & push{UI.RESET}")
    print(f"  {UI.MAGENTA}[2]{UI.RESET} {UI.BOLD}Proportional Branch Mode{UI.RESET}    {UI.GRAY}─ Custom commits & branches (proportionally divided!) 🚀{UI.RESET}")
    
    while True:
        mode_choice = input(f"\n  Enter mode choice {UI.CYAN}[1/2]{UI.RESET} (default 2): ").strip()
        if mode_choice in ("2", "merge", "pr", ""):
            selected_mode = "merge"
            break
        elif mode_choice in ("1", "commit"):
            selected_mode = "commit"
            break
        else:
            UI.warn("Invalid choice. Please enter 1 or 2.")

    # 3. Parameters setup
    print(f"\n{UI.badge('PARAMS', UI.CYAN)} {UI.BOLD}Workflow Configuration:{UI.RESET}")
    while True:
        num_str = input(f"  How many total commits to generate? (default {UI.YELLOW}20{UI.RESET}): ").strip()
        if not num_str:
            total_commits = 20
            break
        try:
            total_commits = int(num_str)
            if total_commits > 0:
                break
            UI.warn("Please enter a positive integer.")
        except ValueError:
            UI.warn("Invalid input. Enter a valid number.")

    num_branches = 1
    if selected_mode == "merge":
        while True:
            def_branches = min(4, total_commits)
            b_str = input(f"  How many branches to distribute commits across? (default {UI.MAGENTA}{def_branches}{UI.RESET}): ").strip()
            if not b_str:
                num_branches = def_branches
                break
            try:
                num_branches = int(b_str)
                if num_branches <= 0:
                    UI.warn("Branches must be at least 1.")
                elif num_branches > total_commits:
                    UI.warn(f"Branches cannot exceed total commits ({total_commits}). Setting to {total_commits}.")
                    num_branches = total_commits
                    break
                else:
                    break
            except ValueError:
                UI.warn("Invalid input. Enter a valid number.")

        preview_dist = distribute_commits(total_commits, num_branches)
        print(f"  {UI.BLUE}↳ Plan:{UI.RESET} {UI.YELLOW}{total_commits}{UI.RESET} commits divided across {UI.MAGENTA}{num_branches}{UI.RESET} branches: {UI.GREEN}{preview_dist}{UI.RESET} commits/branch")

    filename_input = input(f"  Target file to modify (default {UI.CYAN}data.txt{UI.RESET}): ").strip()
    filename = filename_input if filename_input else "data.txt"

    msg_type_choice = input(f"  Use realistic automated commit messages? (Y/n, default {UI.GREEN}Y{UI.RESET}): ").strip().lower()
    custom_msg = ""
    if msg_type_choice in ("n", "no"):
        custom_msg = input("  Enter your custom commit message: ").strip() or "graph-greener!"

    # 4. Execution
    if selected_mode == "commit":
        execute_direct_commits(repo_path, base_branch, filename, total_commits, custom_msg)
    else:
        execute_branch_and_merge(repo_path, base_branch, filename, total_commits, num_branches, custom_msg)

    # 5. Final Summary
    UI.header("Completion Summary")
    total_activity = total_commits if selected_mode == "commit" else total_commits + num_branches
    UI.card("Status Report", [
        f"Mode:            {UI.GREEN + ('PROPORTIONAL BRANCH & MERGE' if selected_mode == 'merge' else 'DIRECT COMMIT')}{UI.RESET}",
        f"Base Branch:     {UI.CYAN}{base_branch}{UI.RESET}",
        f"Branches Made:   {UI.MAGENTA}{num_branches if selected_mode == 'merge' else 0}{UI.RESET}",
        f"Feature Commits: {UI.YELLOW}{total_commits}{UI.RESET}",
        f"Merge Commits:   {UI.MAGENTA}{num_branches if selected_mode == 'merge' else 0}{UI.RESET}",
        f"Total Activity:  {UI.GREEN}{total_activity} total commits added{UI.RESET}",
        f"Target File:     {UI.WHITE}{filename}{UI.RESET}",
        f"Contribution:    {UI.GREEN}Synced with GitHub Activity & Graph! 🌟{UI.RESET}"
    ])
    print(f"\n{UI.GREEN}✨ All operations completed successfully! Happy coding!{UI.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{UI.YELLOW}Process interrupted by user. Exiting safely.{UI.RESET}")
        sys.exit(0)
