"""
Sample Data Loader
Populates database with coding problems for testing
"""

from src.database import Database

def load_sample_problems(db: Database):
    """Load 30 sample coding problems"""
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
    
    for problem in problems:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO problems 
                (problem_id, title, topic, pattern, difficulty, tags, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, problem)
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
        
        for attempt in attempts:
            learner.record_attempt(user_id, *attempt)
        
        print(f"Added {len(attempts)} sample attempts")
        
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