"""
Sample Data Loader
Populates database with coding problems for testing
"""

import json
import os
import re
import unicodedata
from pathlib import Path

from src.database import Database


DIFFICULTIES = {"Easy", "Medium", "Hard"}
MARKER_TEXT = {"", "⭐", "⭐️", "✅", "🟢", "🟡", "🔴", "🔴!", "🟢!", "🟡!"}

TITLE_ID_OVERRIDES = {
    "2sum": "two-sum",
    "two sum": "two-sum",
    "3sum": "3sum",
    "best time to buy and sell stock": "best-time-stock",
    "containers with most water": "container-water",
    "container with most water": "container-water",
    "contains duplicate": "contains-duplicate",
    "valid anagram": "valid-anagram",
    "valid palindrome": "valid-palindrome",
    "maximum subarray": "maximum-subarray",
    "longest substring without repeating characters": "longest-substring",
    "search in rotated sorted array": "search-rotated",
    "climbing stairs": "climbing-stairs",
    "coin change": "coin-change",
    "house robber": "house-robber",
    "longest increasing subsequence": "longest-increasing",
    "product of array except self": "product-except-self",
    "merge sorted array": "merge-sorted-array",
    "invert binary tree": "invert-tree",
    "same tree": "same-tree",
    "binary tree level order traversal": "level-order",
    "lowest common ancestor of a binary search tree": "lowest-common-ancestor",
}


def _normalize_title(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("’", "'")).strip()


def _slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    normalized = normalized.lower().replace("&", "and")
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    return normalized.strip("-") or "problem"


def _problem_id_for(title: str, seen: dict) -> str:
    key = _normalize_title(title).lower()
    base = TITLE_ID_OVERRIDES.get(key, _slug(title))
    count = seen.get(base, 0) + 1
    seen[base] = count
    return base if count == 1 else f"{base}-{count}"


def _clean_marker(value: str) -> str:
    text = value.strip()
    text = text.replace("⭐️", "⭐").replace("✅", "").strip()
    return text


def _heading_parts(line: str):
    match = re.match(r"^(#{2,8})\s+(.*)$", line.strip())
    if not match:
        return None
    return len(match.group(1)), match.group(2).strip()


def _extract_problem_heading(text: str):
    link = re.match(r"^\[(.*?)\]\((.*)\)(.*)$", text)
    if link:
        title = _normalize_title(link.group(1))
        return title, link.group(2).strip(), True
    if text in DIFFICULTIES or _clean_marker(text) in MARKER_TEXT:
        return None
    if len(text) < 4:
        return None
    return _normalize_title(text), None, False


def _is_summary_text(text: str) -> bool:
    cleaned = _clean_marker(text)
    if cleaned in MARKER_TEXT or cleaned in DIFFICULTIES:
        return False
    return len(cleaned.split()) >= 4


def _candidate_dsa_paths():
    env_path = os.getenv("DSA_PROBLEMS_PATH")
    paths = []
    if env_path:
        paths.append(Path(env_path))
    paths.extend([
        Path("data/dsa_problems.md"),
        Path.home() / "Desktop" / "DSA Problems.md",
    ])
    return paths


def _parse_dsa_markdown(path: Path):
    if not path.exists():
        return []

    problems = []
    seen_ids = {}
    topic = None
    difficulty = None
    pattern_parts = []
    current = None
    summary_lines = []

    def flush_current():
        nonlocal current, summary_lines
        if not current:
            return
        summary = " ".join(line.strip() for line in summary_lines if line.strip())
        description = summary or f"Practice {current['title']} from the curated DSA bank."
        source = f"Source: {current['url']}" if current["url"] else "Source: Curated DSA list"
        current["description"] = f"{description} {source}"
        current["constraints"] = (
            "Use the linked platform statement for full constraints. "
            "Manual attempt recording is available when no demo tests are configured."
        )
        problems.append(current)
        current = None
        summary_lines = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parts = _heading_parts(raw_line)
        if not parts:
            if current and raw_line.strip():
                summary_lines.append(raw_line.strip())
            continue

        level, text = parts
        if level == 2:
            flush_current()
            topic = _normalize_title(re.sub(r"\(.*?\)", "", text))
            difficulty = None
            pattern_parts = []
            continue

        if text in DIFFICULTIES:
            flush_current()
            difficulty = text
            continue

        problem_heading = _extract_problem_heading(text)
        if problem_heading and level >= 4 and difficulty:
            title, url, has_link = problem_heading
            if not has_link and level > 5:
                continue
            flush_current()
            pattern = " / ".join(pattern_parts[-2:]) if pattern_parts else None
            tags = ",".join(
                part
                for part in [_slug(topic or "DSA"), _slug(pattern or ""), _slug(url or "curated")]
                if part
            )
            current = {
                "problem_id": _problem_id_for(title, seen_ids),
                "title": title,
                "topic": topic or "DSA",
                "pattern": pattern,
                "difficulty": difficulty,
                "tags": tags,
                "url": url,
            }
            continue

        if current and _is_summary_text(text):
            summary_lines.append(text)
            continue

        if level >= 3 and text not in DIFFICULTIES and _clean_marker(text) not in MARKER_TEXT:
            flush_current()
            pattern_parts.append(_normalize_title(text))

    flush_current()
    return problems


def _load_curated_problem_bank():
    for path in _candidate_dsa_paths():
        problems = _parse_dsa_markdown(path)
        if problems:
            print(f"Loaded DSA markdown bank from {path} ({len(problems)} problems)")
            return problems
    return []


def _starter_code(function_name: str = "solve") -> str:
    return (
        f"def {function_name}(*args):\n"
        "    # Write your solution here.\n"
        "    return None\n"
    )


EXECUTABLE_PROBLEMS = {
    "two-sum": {
        "function_name": "solve",
        "starter_code": "def solve(nums, target):\n    return []\n",
        "examples": "Input: nums=[2,7,11,15], target=9 | Output: [0,1]",
        "constraints": "Return any valid pair of indices. Demo judge expects exact sample outputs.",
        "test_cases": [
            {"input": [[2, 7, 11, 15], 9], "expected": [0, 1]},
            {"input": [[3, 2, 4], 6], "expected": [1, 2]},
            {"input": [[3, 3], 6], "expected": [0, 1]},
        ],
    },
    "contains-duplicate": {
        "function_name": "solve",
        "starter_code": "def solve(nums):\n    return False\n",
        "examples": "Input: nums=[1,2,3,1] | Output: true",
        "constraints": "Return True if any value appears at least twice.",
        "test_cases": [
            {"input": [[1, 2, 3, 1]], "expected": True},
            {"input": [[1, 2, 3, 4]], "expected": False},
            {"input": [[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]], "expected": True},
        ],
    },
    "best-time-stock": {
        "function_name": "solve",
        "starter_code": "def solve(prices):\n    return 0\n",
        "examples": "Input: prices=[7,1,5,3,6,4] | Output: 5",
        "constraints": "Choose one buy day and one future sell day.",
        "test_cases": [
            {"input": [[7, 1, 5, 3, 6, 4]], "expected": 5},
            {"input": [[7, 6, 4, 3, 1]], "expected": 0},
            {"input": [[1, 2]], "expected": 1},
        ],
    },
    "maximum-subarray": {
        "function_name": "solve",
        "starter_code": "def solve(nums):\n    return 0\n",
        "examples": "Input: nums=[-2,1,-3,4,-1,2,1,-5,4] | Output: 6",
        "constraints": "Return maximum sum over a non-empty contiguous subarray.",
        "test_cases": [
            {"input": [[-2, 1, -3, 4, -1, 2, 1, -5, 4]], "expected": 6},
            {"input": [[1]], "expected": 1},
            {"input": [[5, 4, -1, 7, 8]], "expected": 23},
        ],
    },
    "valid-anagram": {
        "function_name": "solve",
        "starter_code": "def solve(s, t):\n    return False\n",
        "examples": "Input: s='anagram', t='nagaram' | Output: true",
        "constraints": "Return True when both strings contain same character counts.",
        "test_cases": [
            {"input": ["anagram", "nagaram"], "expected": True},
            {"input": ["rat", "car"], "expected": False},
            {"input": ["aacc", "ccac"], "expected": False},
        ],
    },
    "valid-palindrome": {
        "function_name": "solve",
        "starter_code": "def solve(s):\n    return False\n",
        "examples": "Input: s='A man, a plan, a canal: Panama' | Output: true",
        "constraints": "Ignore non-alphanumeric characters and case.",
        "test_cases": [
            {"input": ["A man, a plan, a canal: Panama"], "expected": True},
            {"input": ["race a car"], "expected": False},
            {"input": [" "], "expected": True},
        ],
    },
    "reverse-string": {
        "function_name": "solve",
        "starter_code": "def solve(s):\n    return s\n",
        "examples": "Input: s='hello' | Output: 'olleh'",
        "constraints": "Demo judge uses string return instead of in-place list mutation.",
        "test_cases": [
            {"input": ["hello"], "expected": "olleh"},
            {"input": ["Hannah"], "expected": "hannaH"},
            {"input": [""], "expected": ""},
        ],
    },
    "longest-substring": {
        "function_name": "solve",
        "starter_code": "def solve(s):\n    return 0\n",
        "examples": "Input: s='abcabcbb' | Output: 3",
        "constraints": "Return length of longest substring without repeated characters.",
        "test_cases": [
            {"input": ["abcabcbb"], "expected": 3},
            {"input": ["bbbbb"], "expected": 1},
            {"input": ["pwwkew"], "expected": 3},
        ],
    },
    "search-rotated": {
        "function_name": "solve",
        "starter_code": "def solve(nums, target):\n    return -1\n",
        "examples": "Input: nums=[4,5,6,7,0,1,2], target=0 | Output: 4",
        "constraints": "Return index if found, otherwise -1.",
        "test_cases": [
            {"input": [[4, 5, 6, 7, 0, 1, 2], 0], "expected": 4},
            {"input": [[4, 5, 6, 7, 0, 1, 2], 3], "expected": -1},
            {"input": [[1], 0], "expected": -1},
        ],
    },
    "climbing-stairs": {
        "function_name": "solve",
        "starter_code": "def solve(n):\n    return 0\n",
        "examples": "Input: n=3 | Output: 3",
        "constraints": "Each move can climb 1 or 2 steps.",
        "test_cases": [
            {"input": [2], "expected": 2},
            {"input": [3], "expected": 3},
            {"input": [5], "expected": 8},
        ],
    },
}


def _with_judge_fields(problem):
    source_url = None
    if isinstance(problem, dict):
        problem_id = problem["problem_id"]
        title = problem["title"]
        topic = problem["topic"]
        pattern = problem.get("pattern")
        difficulty = problem["difficulty"]
        tags = problem.get("tags")
        description = problem.get("description")
        constraints = problem.get("constraints")
        examples = problem.get("examples")
        source_url = problem.get("url") or problem.get("source_url")
    else:
        problem_id, title, topic, pattern, difficulty, tags, description = problem
        constraints = None
        examples = None

    spec = EXECUTABLE_PROBLEMS.get(problem_id, {})
    return (
        problem_id,
        title,
        topic,
        pattern,
        difficulty,
        tags,
        description,
        spec.get("constraints", constraints),
        spec.get("examples", examples),
        source_url,
        spec.get("function_name", "solve"),
        spec.get("starter_code", _starter_code()),
        json.dumps(spec["test_cases"]) if spec.get("test_cases") else None,
    )


def _generate_question_bank(count: int = 420):
    topics = {
        "Array": ["Prefix Sum", "Two Pointers", "Sliding Window", "Hash Map", "Binary Search"],
        "String": ["Hash Map", "Two Pointers", "Sliding Window", "Stack", "Dynamic Programming"],
        "Linked List": ["Two Pointers", "Fast Slow Pointers", "Recursion", "Iterative"],
        "Tree": ["DFS", "BFS", "Recursion", "Binary Search Tree"],
        "Graph": ["DFS", "BFS", "Topological Sort", "Union Find", "Shortest Path"],
        "Dynamic Programming": ["1D DP", "2D DP", "Knapsack", "State Machine"],
        "Stack": ["Monotonic Stack", "Parsing", "Simulation"],
        "Heap": ["Priority Queue", "Top K", "Merge K"],
    }
    difficulties = ["Easy", "Medium", "Medium", "Hard"]
    generated = []
    topic_names = list(topics.keys())

    for index in range(1, count + 1):
        topic = topic_names[(index - 1) % len(topic_names)]
        pattern = topics[topic][(index - 1) % len(topics[topic])]
        difficulty = difficulties[(index - 1) % len(difficulties)]
        slug_topic = topic.lower().replace(" ", "-")
        slug_pattern = pattern.lower().replace(" ", "-")
        problem_id = f"{slug_topic}-{slug_pattern}-drill-{index:03d}"
        title = f"{pattern} {topic} Drill {index:03d}"
        tags = f"{slug_topic},{slug_pattern},practice"
        description = (
            f"Practice {pattern} technique in {topic}. "
            "Use this item for adaptive ITS tracking and manual attempt recording."
        )
        generated.append((problem_id, title, topic, pattern, difficulty, tags, description))

    return generated

def load_sample_problems(db: Database):
    """Load curated DSA problems; fallback to generated scaffold if markdown is absent."""
    conn = db.get_connection()
    cursor = conn.cursor()
    
    problems = [
        # Arrays - Easy
        ("two-sum", "Two Sum", "Array", "Hash Map", "Easy", "array,hash-table", 
         "Find two numbers that add up to target"),
        ("best-time-stock", "Best Time to Buy and Sell Stock", "Array", "One Pass", "Easy", 
         "array,dp", "Find max profit from stock prices"),
        ("contains-duplicate", "Contains Duplicate", "Array", "Hash Set", "Easy", 
         "array,hash-table", "Check if array has duplicates"),
        ("maximum-subarray", "Maximum Subarray", "Array", "Kadane's Algorithm", "Easy", 
         "array,dp", "Find contiguous subarray with max sum"),
        ("merge-sorted-array", "Merge Sorted Array", "Array", "Two Pointers", "Easy", 
         "array,two-pointers", "Merge two sorted arrays in-place"),
        
        # Arrays - Medium
        ("3sum", "3Sum", "Array", "Two Pointers", "Medium", "array,two-pointers", 
         "Find all triplets that sum to zero"),
        ("container-water", "Container With Most Water", "Array", "Two Pointers", "Medium", 
         "array,greedy", "Find max water container can hold"),
        ("product-except-self", "Product of Array Except Self", "Array", "Prefix Sum", "Medium", 
         "array,prefix-sum", "Calculate product array without division"),
        ("search-rotated", "Search in Rotated Sorted Array", "Array", "Binary Search", "Medium", 
         "array,binary-search", "Search in rotated array"),
        
        # Strings - Easy
        ("valid-anagram", "Valid Anagram", "String", "Hash Map", "Easy", 
         "string,hash-table", "Check if two strings are anagrams"),
        ("valid-palindrome", "Valid Palindrome", "String", "Two Pointers", "Easy", 
         "string,two-pointers", "Check if string is palindrome"),
        ("reverse-string", "Reverse String", "String", "Two Pointers", "Easy", 
         "string,two-pointers", "Reverse string in-place"),
        
        # Strings - Medium
        ("longest-substring", "Longest Substring Without Repeating", "String", "Sliding Window", "Medium", 
         "string,sliding-window", "Find longest substring without repeats"),
        ("group-anagrams", "Group Anagrams", "String", "Hash Map", "Medium", 
         "string,hash-table", "Group anagrams together"),
        ("longest-palindrome", "Longest Palindromic Substring", "String", "Dynamic Programming", "Medium", 
         "string,dp", "Find longest palindromic substring"),
        
        # Linked Lists - Easy
        ("reverse-linked-list", "Reverse Linked List", "Linked List", "Iterative", "Easy", 
         "linked-list", "Reverse a singly linked list"),
        ("merge-two-lists", "Merge Two Sorted Lists", "Linked List", "Two Pointers", "Easy", 
         "linked-list,recursion", "Merge two sorted linked lists"),
        ("linked-list-cycle", "Linked List Cycle", "Linked List", "Fast Slow Pointers", "Easy", 
         "linked-list,two-pointers", "Detect cycle in linked list"),
        
        # Trees - Easy
        ("max-depth-tree", "Maximum Depth of Binary Tree", "Tree", "DFS", "Easy", 
         "tree,dfs,recursion", "Find max depth of binary tree"),
        ("same-tree", "Same Tree", "Tree", "DFS", "Easy", 
         "tree,dfs", "Check if two trees are identical"),
        ("invert-tree", "Invert Binary Tree", "Tree", "DFS", "Easy", 
         "tree,dfs,recursion", "Invert/mirror a binary tree"),
        
        # Trees - Medium
        ("validate-bst", "Validate Binary Search Tree", "Tree", "DFS", "Medium", 
         "tree,dfs", "Validate if tree is valid BST"),
        ("level-order", "Binary Tree Level Order Traversal", "Tree", "BFS", "Medium", 
         "tree,bfs", "Return level order traversal"),
        ("lowest-common-ancestor", "Lowest Common Ancestor of BST", "Tree", "DFS", "Medium", 
         "tree,dfs,bst", "Find LCA in BST"),
        
        # Dynamic Programming - Medium
        ("climbing-stairs", "Climbing Stairs", "Dynamic Programming", "1D DP", "Easy", 
         "dp,math", "Count ways to climb stairs"),
        ("coin-change", "Coin Change", "Dynamic Programming", "1D DP", "Medium", 
         "dp,array", "Find min coins for amount"),
        ("longest-increasing", "Longest Increasing Subsequence", "Dynamic Programming", "1D DP", "Medium", 
         "dp,binary-search", "Find LIS length"),
        ("house-robber", "House Robber", "Dynamic Programming", "1D DP", "Medium", 
         "dp,array", "Max money without robbing adjacent"),
        
        # Graphs - Medium
        ("number-of-islands", "Number of Islands", "Graph", "DFS", "Medium", 
         "graph,dfs,bfs", "Count number of islands"),
        ("clone-graph", "Clone Graph", "Graph", "DFS", "Medium", 
         "graph,dfs,bfs,hash-table", "Deep copy of graph"),
    ]
    
    curated_problems = _load_curated_problem_bank()
    if curated_problems:
        problems = curated_problems
        for table in ("recommendations", "revision_schedule", "submissions", "attempts"):
            cursor.execute(f"DELETE FROM {table} WHERE problem_id LIKE ?", ("%-drill-%",))
        cursor.execute("DELETE FROM problems WHERE problem_id LIKE ?", ("%-drill-%",))
    else:
        problems.extend(_generate_question_bank())

    for problem in (_with_judge_fields(problem) for problem in problems):
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO problems 
                (
                    problem_id, title, topic, pattern, difficulty, tags, description,
                    constraints, examples, source_url, function_name, starter_code, test_cases
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, problem)
            cursor.execute("""
                UPDATE problems
                SET title = ?, topic = ?, pattern = ?, difficulty = ?, tags = ?,
                    description = ?, constraints = ?, examples = ?, source_url = ?,
                    function_name = ?, starter_code = ?, test_cases = ?
                WHERE problem_id = ?
            """, (
                problem[1], problem[2], problem[3], problem[4], problem[5],
                problem[6], problem[7], problem[8], problem[9], problem[10],
                problem[11], problem[12], problem[0],
            ))
        except Exception as e:
            print(f"Error inserting {problem[0]}: {e}")
    
    conn.commit()
    conn.close()
    print(f"Loaded {len(problems)} sample problems")

def create_demo_user(db: Database):
    """Create a demo user with some practice history"""
    from src.auth import AuthService
    from src.learner_model import LearnerModel
    
    auth = AuthService(db)
    learner = LearnerModel(db)
    
    try:
        # Create demo user
        result = auth.register_user(
            name="Demo User",
            email="demo@example.com",
            password="demo123",
            target_level="medium"
        )
        user_id = result['user_id']
        print(f"Created demo user (ID: {user_id})")
        
        # Add some sample attempts
        attempts = [
            # Easy problems - mostly accepted
            ("two-sum", "Accepted", 300, None),
            ("contains-duplicate", "Accepted", 250, None),
            ("valid-palindrome", "Accepted", 180, None),
            ("reverse-string", "Accepted", 150, None),
            ("max-depth-tree", "Wrong Answer", 420, "edge-case"),
            ("max-depth-tree", "Accepted", 380, None),
            
            # Medium problems - mixed results
            ("3sum", "Time Limit Exceeded", 1800, "timeout"),
            ("3sum", "Wrong Answer", 1500, "logic-error"),
            ("longest-substring", "Wrong Answer", 900, "off-by-one"),
            ("longest-substring", "Accepted", 850, None),
            ("search-rotated", "Wrong Answer", 600, "edge-case"),
            ("container-water", "Time Limit Exceeded", 1200, "timeout"),
            
            # DP problems - struggles
            ("climbing-stairs", "Accepted", 400, None),
            ("coin-change", "Wrong Answer", 1800, "logic-error"),
            ("house-robber", "Time Limit Exceeded", 2000, "timeout"),
            ("house-robber", "Wrong Answer", 1700, "logic-error"),
        ]
        
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT problem_id FROM problems")
        available_problem_ids = {row["problem_id"] for row in cursor.fetchall()}
        conn.close()

        inserted_attempts = 0
        for attempt in attempts:
            if attempt[0] in available_problem_ids:
                learner.record_attempt(user_id, *attempt)
                inserted_attempts += 1
        
        print(f"Added {inserted_attempts} sample attempts")
        
        return user_id
        
    except ValueError as e:
        print(f"Demo user might already exist: {e}")
        # Get existing demo user
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = ?", ("demo@example.com",))
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['user_id']
        return None

if __name__ == "__main__":
    db = Database()
    print("Loading sample data...")
    load_sample_problems(db)
    user_id = create_demo_user(db)
    
    if user_id:
        print(f"\nDemo user created!")
        print(f"Email: demo@example.com")
        print(f"Password: demo123")
        print(f"\nYou can now login and test the system!")
