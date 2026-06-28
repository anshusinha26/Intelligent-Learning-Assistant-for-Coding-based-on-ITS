#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import heapq
import inspect
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]


CATEGORY_LABELS = [
    "minimum_input",
    "maximum_input",
    "negative_values",
    "duplicates",
    "sorted_input",
    "reverse_sorted",
    "empty_input",
    "single_element",
    "large_values",
    "randomized",
    "boundary_conditions",
]

CASE_EXPLANATION_TEXT = {
    "minimum_input": "Smallest valid input, used to verify base-case behavior.",
    "maximum_input": "High-volume style input that checks scale handling.",
    "negative_values": "Includes negative values to confirm sign-sensitive logic.",
    "duplicates": "Contains duplicates to verify de-duplication and frequency handling.",
    "sorted_input": "Sorted arrangement that can hide off-by-one boundary bugs.",
    "reverse_sorted": "Reverse order to test assumptions about monotonic input.",
    "empty_input": "Empty or near-empty structure to validate guard handling.",
    "single_element": "Single-item case to verify minimal non-empty behavior.",
    "large_values": "Large numeric magnitudes to exercise arithmetic boundaries.",
    "randomized": "Randomly mixed data to detect brittle hard-coded behavior.",
    "boundary_conditions": "Boundary-focused case around indices and window edges.",
}


@dataclass
class Blueprint:
    signature: str
    task: str
    constraints: List[str]
    time_complexity: str
    space_complexity: str
    solver: Callable[..., Any]
    visible_inputs: List[List[Any]]
    hidden_builder: Callable[[random.Random], List[List[Any]]]
    algorithm_note: str


def as_jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [as_jsonable(item) for item in value]
    if isinstance(value, list):
        return [as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    return value


def normalize_tree(values):
    while values and values[-1] is None:
        values.pop()
    return values


def parse_tree(values):
    if not values:
        return None
    nodes = [None if value is None else {"val": value, "left": None, "right": None} for value in values]
    kids = collections.deque(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        if kids:
            node["left"] = kids.popleft()
        if kids:
            node["right"] = kids.popleft()
    return nodes[0]


def serialize_tree(root):
    if root is None:
        return []
    out = []
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node["val"])
        queue.append(node["left"])
        queue.append(node["right"])
    return normalize_tree(out)


def solve_find_min_rotated(nums):
    left, right = 0, len(nums) - 1
    while left < right:
        mid = (left + right) // 2
        if nums[mid] > nums[right]:
            left = mid + 1
        else:
            right = mid
    return nums[left]


def solve_search_rotated(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[left] <= nums[mid]:
            if nums[left] <= target < nums[mid]:
                right = mid - 1
            else:
                left = mid + 1
        else:
            if nums[mid] < target <= nums[right]:
                left = mid + 1
            else:
                right = mid - 1
    return -1


def solve_reverse_linked_list(values):
    return list(reversed(values))


def solve_merge_two_sorted_lists(a, b):
    i = 0
    j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i])
            i += 1
        else:
            out.append(b[j])
            j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def solve_reorder_list(values):
    out = []
    left = 0
    right = len(values) - 1
    while left <= right:
        if left == right:
            out.append(values[left])
        else:
            out.append(values[left])
            out.append(values[right])
        left += 1
        right -= 1
    return out


def solve_remove_nth(values, n):
    index = len(values) - n
    return values[:index] + values[index + 1 :]


def solve_linked_list_cycle(values, pos):
    return pos >= 0 and pos < len(values)


def solve_invert_binary_tree(tree_values):
    def invert(node):
        if node is None:
            return None
        node["left"], node["right"] = invert(node["right"]), invert(node["left"])
        return node

    return serialize_tree(invert(parse_tree(list(tree_values))))


def solve_max_depth_tree(tree_values):
    root = parse_tree(list(tree_values))

    def depth(node):
        if node is None:
            return 0
        return 1 + max(depth(node["left"]), depth(node["right"]))

    return depth(root)


def solve_diameter_tree(tree_values):
    root = parse_tree(list(tree_values))
    best = 0

    def height(node):
        nonlocal best
        if node is None:
            return 0
        left = height(node["left"])
        right = height(node["right"])
        best = max(best, left + right)
        return 1 + max(left, right)

    height(root)
    return best


def solve_balanced_tree(tree_values):
    root = parse_tree(list(tree_values))

    def check(node):
        if node is None:
            return 0
        left = check(node["left"])
        if left == -1:
            return -1
        right = check(node["right"])
        if right == -1:
            return -1
        if abs(left - right) > 1:
            return -1
        return 1 + max(left, right)

    return check(root) != -1


def solve_same_tree(a, b):
    return a == b


def solve_subtree(root_vals, sub_vals):
    if not sub_vals:
        return True
    if not root_vals:
        return False
    root = parse_tree(list(root_vals))
    sub = parse_tree(list(sub_vals))

    def same(a, b):
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return a["val"] == b["val"] and same(a["left"], b["left"]) and same(a["right"], b["right"])

    def walk(node):
        if node is None:
            return False
        return same(node, sub) or walk(node["left"]) or walk(node["right"])

    return walk(root)


def solve_level_order(tree_values):
    root = parse_tree(list(tree_values))
    if root is None:
        return []
    out = []
    queue = collections.deque([root])
    while queue:
        size = len(queue)
        level = []
        for _ in range(size):
            node = queue.popleft()
            level.append(node["val"])
            if node["left"] is not None:
                queue.append(node["left"])
            if node["right"] is not None:
                queue.append(node["right"])
        out.append(level)
    return out


def solve_kth_largest(nums, k):
    heap = []
    for value in nums:
        if len(heap) < k:
            heapq.heappush(heap, value)
        elif value > heap[0]:
            heapq.heapreplace(heap, value)
    return heap[0]


def solve_task_scheduler(tasks, n):
    counter = collections.Counter(tasks)
    max_freq = max(counter.values())
    max_count = sum(1 for value in counter.values() if value == max_freq)
    return max(len(tasks), (max_freq - 1) * (n + 1) + max_count)


def solve_median_stream(operations, values):
    lower = []
    upper = []
    out = []
    for idx, operation in enumerate(operations):
        payload = values[idx] if idx < len(values) else []
        if operation == "MedianFinder":
            lower = []
            upper = []
            out.append(None)
        elif operation == "addNum":
            value = payload[0]
            heapq.heappush(lower, -value)
            if upper and -lower[0] > upper[0]:
                heapq.heappush(upper, -heapq.heappop(lower))
            if len(lower) > len(upper) + 1:
                heapq.heappush(upper, -heapq.heappop(lower))
            if len(upper) > len(lower):
                heapq.heappush(lower, -heapq.heappop(upper))
            out.append(None)
        elif operation == "findMedian":
            if len(lower) > len(upper):
                out.append(float(-lower[0]))
            else:
                out.append(round((-lower[0] + upper[0]) / 2, 5))
        else:
            out.append(None)
    return out


def solve_merge_k_lists(lists):
    heap = []
    for list_index, arr in enumerate(lists):
        if arr:
            heapq.heappush(heap, (arr[0], list_index, 0))
    out = []
    while heap:
        value, list_index, element_index = heapq.heappop(heap)
        out.append(value)
        next_index = element_index + 1
        if next_index < len(lists[list_index]):
            heapq.heappush(heap, (lists[list_index][next_index], list_index, next_index))
    return out


def solve_subsets(nums):
    out = [[]]
    for value in nums:
        out.extend([subset + [value] for subset in out])
    out = [sorted(subset) for subset in out]
    out.sort(key=lambda subset: (len(subset), subset))
    return out


def solve_combination_sum(candidates, target):
    candidates = sorted(set(candidates))
    out = []

    def dfs(index, total, path):
        if total == target:
            out.append(path[:])
            return
        if total > target:
            return
        for idx in range(index, len(candidates)):
            path.append(candidates[idx])
            dfs(idx, total + candidates[idx], path)
            path.pop()

    dfs(0, 0, [])
    out.sort()
    return out


def solve_permutations(nums):
    out = []

    def backtrack(path, remaining):
        if not remaining:
            out.append(path[:])
            return
        for idx, value in enumerate(remaining):
            backtrack(path + [value], remaining[:idx] + remaining[idx + 1 :])

    backtrack([], nums)
    out.sort()
    return out


def solve_word_search(board, word):
    rows = len(board)
    cols = len(board[0]) if board else 0
    grid = [row[:] for row in board]

    def dfs(r, c, idx):
        if idx == len(word):
            return True
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return False
        if grid[r][c] != word[idx]:
            return False
        temp = grid[r][c]
        grid[r][c] = "#"
        found = (
            dfs(r + 1, c, idx + 1)
            or dfs(r - 1, c, idx + 1)
            or dfs(r, c + 1, idx + 1)
            or dfs(r, c - 1, idx + 1)
        )
        grid[r][c] = temp
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


def solve_number_of_islands(grid):
    if not grid:
        return 0
    work = [row[:] for row in grid]
    rows = len(work)
    cols = len(work[0])
    count = 0

    def flood(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols:
            return
        if work[r][c] != "1":
            return
        work[r][c] = "0"
        flood(r + 1, c)
        flood(r - 1, c)
        flood(r, c + 1)
        flood(r, c - 1)

    for r in range(rows):
        for c in range(cols):
            if work[r][c] == "1":
                count += 1
                flood(r, c)
    return count


def solve_clone_graph(adj):
    return [neighbors[:] for neighbors in adj]


def solve_pacific_atlantic(heights):
    if not heights:
        return []
    rows = len(heights)
    cols = len(heights[0])

    def bfs(starts):
        reachable = set(starts)
        queue = collections.deque(starts)
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr = r + dr
                nc = c + dc
                if nr < 0 or nr >= rows or nc < 0 or nc >= cols:
                    continue
                if (nr, nc) in reachable:
                    continue
                if heights[nr][nc] < heights[r][c]:
                    continue
                reachable.add((nr, nc))
                queue.append((nr, nc))
        return reachable

    pacific_starts = [(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)]
    atlantic_starts = [(rows - 1, c) for c in range(cols)] + [(r, cols - 1) for r in range(rows)]
    pacific = bfs(pacific_starts)
    atlantic = bfs(atlantic_starts)
    out = [[r, c] for r, c in sorted(pacific & atlantic)]
    return out


def solve_course_schedule(num_courses, prerequisites):
    graph = [[] for _ in range(num_courses)]
    indegree = [0] * num_courses
    for course, pre in prerequisites:
        graph[pre].append(course)
        indegree[course] += 1
    queue = collections.deque([i for i in range(num_courses) if indegree[i] == 0])
    seen = 0
    while queue:
        node = queue.popleft()
        seen += 1
        for nxt in graph[node]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return seen == num_courses


def solve_course_schedule_ii(num_courses, prerequisites):
    graph = [[] for _ in range(num_courses)]
    indegree = [0] * num_courses
    for course, pre in prerequisites:
        graph[pre].append(course)
        indegree[course] += 1
    queue = collections.deque(sorted(i for i in range(num_courses) if indegree[i] == 0))
    order = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for nxt in sorted(graph[node]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return order if len(order) == num_courses else []


def solve_graph_valid_tree(n, edges):
    if len(edges) != n - 1:
        return False
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v in edges:
        pu = find(u)
        pv = find(v)
        if pu == pv:
            return False
        parent[pu] = pv
    return True


def solve_network_delay(times, n, k):
    graph = collections.defaultdict(list)
    for u, v, w in times:
        graph[u].append((v, w))
    dist = {node: float("inf") for node in range(1, n + 1)}
    dist[k] = 0
    heap = [(0, k)]
    while heap:
        cur_dist, node = heapq.heappop(heap)
        if cur_dist > dist[node]:
            continue
        for nxt, weight in graph[node]:
            cand = cur_dist + weight
            if cand < dist[nxt]:
                dist[nxt] = cand
                heapq.heappush(heap, (cand, nxt))
    ans = max(dist.values())
    return -1 if ans == float("inf") else ans


def solve_climbing_stairs(n):
    if n <= 2:
        return n
    a = 1
    b = 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b


def solve_house_robber(nums):
    rob = 0
    skip = 0
    for value in nums:
        rob, skip = skip + value, max(skip, rob)
    return max(rob, skip)


def solve_house_robber_ii(nums):
    if len(nums) == 1:
        return nums[0]

    def rob_linear(arr):
        rob = 0
        skip = 0
        for value in arr:
            rob, skip = skip + value, max(skip, rob)
        return max(rob, skip)

    return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))


def solve_coin_change(coins, amount):
    dp = [amount + 1] * (amount + 1)
    dp[0] = 0
    for total in range(1, amount + 1):
        for coin in coins:
            if coin <= total:
                dp[total] = min(dp[total], dp[total - coin] + 1)
    return -1 if dp[amount] > amount else dp[amount]


def solve_lis(nums):
    tails = []
    for value in nums:
        left = 0
        right = len(tails)
        while left < right:
            mid = (left + right) // 2
            if tails[mid] < value:
                left = mid + 1
            else:
                right = mid
        if left == len(tails):
            tails.append(value)
        else:
            tails[left] = value
    return len(tails)


def solve_partition_equal_subset(nums):
    total = sum(nums)
    if total % 2 == 1:
        return False
    target = total // 2
    possible = {0}
    for value in nums:
        next_possible = set(possible)
        for cur in possible:
            cand = cur + value
            if cand == target:
                return True
            if cand < target:
                next_possible.add(cand)
        possible = next_possible
    return target in possible


def solve_unique_paths(m, n):
    dp = [1] * n
    for _ in range(m - 1):
        for c in range(1, n):
            dp[c] += dp[c - 1]
    return dp[-1]


def solve_lcs(text1, text2):
    rows = len(text1) + 1
    cols = len(text2) + 1
    dp = [[0] * cols for _ in range(rows)]
    for i in range(1, rows):
        for j in range(1, cols):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[-1][-1]


def solve_jump_game(nums):
    reach = 0
    for idx, value in enumerate(nums):
        if idx > reach:
            return False
        reach = max(reach, idx + value)
    return True


def solve_jump_game_ii(nums):
    if len(nums) <= 1:
        return 0
    jumps = 0
    current_end = 0
    farthest = 0
    for idx in range(len(nums) - 1):
        farthest = max(farthest, idx + nums[idx])
        if idx == current_end:
            jumps += 1
            current_end = farthest
    return jumps


def solve_gas_station(gas, cost):
    total = 0
    tank = 0
    start = 0
    for idx in range(len(gas)):
        delta = gas[idx] - cost[idx]
        total += delta
        tank += delta
        if tank < 0:
            tank = 0
            start = idx + 1
    return start if total >= 0 else -1


def solve_merge_intervals(intervals):
    if not intervals:
        return []
    intervals = sorted(intervals)
    merged = [intervals[0][:]]
    for start, end in intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def solve_insert_interval(intervals, new_interval):
    out = []
    idx = 0
    while idx < len(intervals) and intervals[idx][1] < new_interval[0]:
        out.append(intervals[idx])
        idx += 1
    while idx < len(intervals) and intervals[idx][0] <= new_interval[1]:
        new_interval[0] = min(new_interval[0], intervals[idx][0])
        new_interval[1] = max(new_interval[1], intervals[idx][1])
        idx += 1
    out.append(new_interval[:])
    out.extend(intervals[idx:])
    return out


def solve_non_overlapping_intervals(intervals):
    intervals = sorted(intervals, key=lambda item: item[1])
    removed = 0
    last_end = float("-inf")
    for start, end in intervals:
        if start < last_end:
            removed += 1
        else:
            last_end = end
    return removed


def solve_single_number(nums):
    out = 0
    for value in nums:
        out ^= value
    return out


def solve_number_of_1_bits(n):
    count = 0
    while n:
        n &= n - 1
        count += 1
    return count


def solve_counting_bits(n):
    out = [0] * (n + 1)
    for idx in range(1, n + 1):
        out[idx] = out[idx >> 1] + (idx & 1)
    return out


def solve_powx_n(x, n):
    if n == 0:
        return 1.0
    power = abs(n)
    result = 1.0
    base = float(x)
    while power > 0:
        if power & 1:
            result *= base
        base *= base
        power >>= 1
    value = result if n > 0 else 1.0 / result
    return round(value, 6)


def solve_happy_number(n):
    seen = set()
    cur = n
    while cur != 1 and cur not in seen:
        seen.add(cur)
        nxt = 0
        while cur:
            cur, digit = divmod(cur, 10)
            nxt += digit * digit
        cur = nxt
    return cur == 1


def solve_plus_one(digits):
    out = digits[:]
    idx = len(out) - 1
    carry = 1
    while idx >= 0 and carry:
        out[idx] += carry
        carry = out[idx] // 10
        out[idx] %= 10
        idx -= 1
    if carry:
        out.insert(0, carry)
    return out


def solve_rotate_image(matrix):
    n = len(matrix)
    out = [row[:] for row in matrix]
    for r in range(n):
        for c in range(n):
            out[c][n - 1 - r] = matrix[r][c]
    return out


def gen_rotated_sorted(rng, n):
    arr = sorted(rng.sample(range(-500, 500), n))
    pivot = rng.randint(0, n - 1)
    return arr[pivot:] + arr[:pivot]


def hidden_find_min(rng):
    return [[gen_rotated_sorted(rng, rng.randint(3, 40))] for _ in range(20)]


def hidden_search_rotated(rng):
    out = []
    for _ in range(20):
        arr = gen_rotated_sorted(rng, rng.randint(3, 40))
        if rng.random() < 0.7:
            target = rng.choice(arr)
        else:
            target = 1001
        out.append([arr, target])
    return out


def hidden_reverse_list(rng):
    return [[[rng.randint(-20, 20) for _ in range(rng.randint(0, 30))]] for _ in range(20)]


def hidden_merge_lists(rng):
    out = []
    for _ in range(20):
        a = sorted(rng.randint(-30, 30) for _ in range(rng.randint(0, 15)))
        b = sorted(rng.randint(-30, 30) for _ in range(rng.randint(0, 15)))
        out.append([a, b])
    return out


def hidden_reorder(rng):
    return [[[rng.randint(0, 99) for _ in range(rng.randint(1, 30))]] for _ in range(20)]


def hidden_remove_nth(rng):
    out = []
    for _ in range(20):
        arr = [rng.randint(0, 50) for _ in range(rng.randint(1, 25))]
        n = rng.randint(1, len(arr))
        out.append([arr, n])
    return out


def hidden_cycle(rng):
    out = []
    for _ in range(20):
        size = rng.randint(0, 20)
        arr = [rng.randint(0, 50) for _ in range(size)]
        if size == 0:
            pos = -1
        else:
            pos = rng.choice([-1] + list(range(size)))
        out.append([arr, pos])
    return out


def hidden_tree_values(rng):
    out = []
    for _ in range(20):
        size = rng.randint(0, 31)
        arr = []
        for idx in range(size):
            if idx == 0:
                arr.append(rng.randint(-20, 20))
            else:
                arr.append(None if rng.random() < 0.22 else rng.randint(-20, 20))
        out.append([normalize_tree(arr)])
    return out


def hidden_same_tree(rng):
    out = []
    base = hidden_tree_values(rng)
    for item in base:
        a = item[0]
        if rng.random() < 0.5:
            b = json.loads(json.dumps(a))
        else:
            b = json.loads(json.dumps(a))
            if b:
                idx = rng.randint(0, len(b) - 1)
                if b[idx] is None:
                    b[idx] = rng.randint(-20, 20)
                else:
                    b[idx] += 1
        out.append([a, normalize_tree(b)])
    return out


def hidden_subtree(rng):
    out = []
    for _ in range(20):
        root = hidden_tree_values(rng)[0][0]
        if not root:
            out.append([root, []])
            continue
        start = rng.randint(0, max(0, len(root) - 1))
        sub = [root[start]]
        left = 2 * start + 1
        right = 2 * start + 2
        if left < len(root):
            sub.append(root[left])
        if right < len(root):
            sub.append(root[right])
        out.append([root, normalize_tree(sub)])
    return out


def hidden_kth_largest(rng):
    out = []
    for _ in range(20):
        nums = [rng.randint(-100, 100) for _ in range(rng.randint(1, 40))]
        k = rng.randint(1, len(nums))
        out.append([nums, k])
    return out


def hidden_task_scheduler(rng):
    letters = "ABCDEF"
    out = []
    for _ in range(20):
        tasks = [rng.choice(letters) for _ in range(rng.randint(1, 35))]
        n = rng.randint(0, 6)
        out.append([tasks, n])
    return out


def hidden_median_stream(rng):
    out = []
    for _ in range(20):
        operations = ["MedianFinder"]
        values = [[]]
        data = []
        steps = rng.randint(8, 30)
        for _step in range(steps):
            if not data or rng.random() < 0.7:
                operations.append("addNum")
                value = rng.randint(-100, 100)
                data.append(value)
                values.append([value])
            else:
                operations.append("findMedian")
                values.append([])
        out.append([operations, values])
    return out


def hidden_merge_k_lists(rng):
    out = []
    for _ in range(20):
        k = rng.randint(0, 8)
        lists = []
        for _j in range(k):
            arr = sorted(rng.randint(-40, 40) for _ in range(rng.randint(0, 10)))
            lists.append(arr)
        out.append([lists])
    return out


def hidden_subsets(rng):
    return [[[rng.sample(range(-10, 11), rng.randint(0, 8))]] for _ in range(20)]


def hidden_combination_sum(rng):
    out = []
    for _ in range(20):
        candidates = sorted(set(rng.randint(2, 12) for _ in range(rng.randint(2, 6))))
        target = rng.randint(1, 40)
        out.append([candidates, target])
    return out


def hidden_permutations(rng):
    out = []
    for _ in range(20):
        nums = rng.sample(range(-9, 10), rng.randint(1, 7))
        out.append([nums])
    return out


def hidden_word_search(rng):
    letters = "ABCD"
    out = []
    for _ in range(20):
        rows = rng.randint(1, 5)
        cols = rng.randint(1, 5)
        board = [[rng.choice(letters) for _ in range(cols)] for _ in range(rows)]
        word_len = rng.randint(1, min(7, rows * cols))
        word = "".join(rng.choice(letters) for _ in range(word_len))
        out.append([board, word])
    return out


def hidden_num_islands(rng):
    out = []
    for _ in range(20):
        rows = rng.randint(1, 8)
        cols = rng.randint(1, 8)
        grid = [[rng.choice(["0", "1"]) for _ in range(cols)] for _ in range(rows)]
        out.append([grid])
    return out


def hidden_clone_graph(rng):
    out = []
    for _ in range(20):
        n = rng.randint(1, 8)
        adj = []
        for node in range(1, n + 1):
            neighbors = [other for other in range(1, n + 1) if other != node and rng.random() < 0.25]
            adj.append(sorted(neighbors))
        out.append([adj])
    return out


def hidden_pacific_atlantic(rng):
    out = []
    for _ in range(20):
        rows = rng.randint(1, 6)
        cols = rng.randint(1, 6)
        grid = [[rng.randint(0, 20) for _ in range(cols)] for _ in range(rows)]
        out.append([grid])
    return out


def hidden_course_schedule(rng):
    out = []
    for _ in range(20):
        n = rng.randint(2, 12)
        edges = []
        for _e in range(rng.randint(0, n * 2)):
            a = rng.randint(0, n - 1)
            b = rng.randint(0, n - 1)
            if a != b:
                edges.append([a, b])
        out.append([n, edges])
    return out


def hidden_graph_valid_tree(rng):
    out = []
    for _ in range(20):
        n = rng.randint(1, 12)
        edges = []
        for _e in range(rng.randint(0, n + 4)):
            a = rng.randint(0, n - 1)
            b = rng.randint(0, n - 1)
            if a != b:
                edges.append([a, b])
        out.append([n, edges])
    return out


def hidden_network_delay(rng):
    out = []
    for _ in range(20):
        n = rng.randint(2, 10)
        times = []
        for _e in range(rng.randint(n - 1, n * 3)):
            u = rng.randint(1, n)
            v = rng.randint(1, n)
            if u != v:
                times.append([u, v, rng.randint(1, 20)])
        k = rng.randint(1, n)
        out.append([times, n, k])
    return out


def hidden_stairs(rng):
    return [[rng.randint(1, 45)] for _ in range(20)]


def hidden_house_robber(rng):
    return [[[rng.randint(0, 80) for _ in range(rng.randint(1, 40))]] for _ in range(20)]


def hidden_coin_change(rng):
    out = []
    for _ in range(20):
        coins = sorted(set(rng.randint(1, 20) for _ in range(rng.randint(1, 6))))
        amount = rng.randint(0, 120)
        out.append([coins, amount])
    return out


def hidden_lis(rng):
    return [[[rng.randint(-100, 100) for _ in range(rng.randint(1, 60))]] for _ in range(20)]


def hidden_partition(rng):
    return [[[rng.randint(1, 40) for _ in range(rng.randint(1, 22))]] for _ in range(20)]


def hidden_unique_paths(rng):
    return [[rng.randint(1, 20), rng.randint(1, 20)] for _ in range(20)]


def hidden_lcs(rng):
    letters = "abcde"
    out = []
    for _ in range(20):
        a = "".join(rng.choice(letters) for _ in range(rng.randint(1, 20)))
        b = "".join(rng.choice(letters) for _ in range(rng.randint(1, 20)))
        out.append([a, b])
    return out


def hidden_jump(rng):
    return [[[rng.randint(0, 8) for _ in range(rng.randint(1, 40))]] for _ in range(20)]


def hidden_gas_station(rng):
    out = []
    for _ in range(20):
        n = rng.randint(1, 30)
        gas = [rng.randint(0, 20) for _ in range(n)]
        cost = [rng.randint(0, 20) for _ in range(n)]
        out.append([gas, cost])
    return out


def hidden_intervals(rng):
    out = []
    for _ in range(20):
        arr = []
        for _j in range(rng.randint(0, 16)):
            a = rng.randint(-20, 30)
            b = rng.randint(a, a + rng.randint(0, 10))
            arr.append([a, b])
        out.append([arr])
    return out


def hidden_insert_interval(rng):
    out = []
    for _ in range(20):
        arr = []
        for _j in range(rng.randint(0, 12)):
            a = rng.randint(-20, 30)
            b = rng.randint(a, a + rng.randint(0, 8))
            arr.append([a, b])
        arr = sorted(arr)
        new_a = rng.randint(-20, 30)
        new_b = rng.randint(new_a, new_a + rng.randint(0, 8))
        out.append([arr, [new_a, new_b]])
    return out


def hidden_single_number(rng):
    out = []
    for _ in range(20):
        pairs = [rng.randint(-50, 50) for _ in range(rng.randint(1, 15))]
        unique = rng.randint(-50, 50)
        nums = []
        for value in pairs:
            nums.extend([value, value])
        nums.append(unique)
        rng.shuffle(nums)
        out.append([nums])
    return out


def hidden_hamming(rng):
    return [[rng.randint(0, 2**31 - 1)] for _ in range(20)]


def hidden_count_bits(rng):
    return [[rng.randint(0, 128)] for _ in range(20)]


def hidden_pow(rng):
    out = []
    for _ in range(20):
        x = round(rng.uniform(-4, 4), 2)
        n = rng.randint(-12, 12)
        if x == 0 and n < 0:
            x = 2.0
        out.append([x, n])
    return out


def hidden_happy(rng):
    return [[rng.randint(1, 500)] for _ in range(20)]


def hidden_plus_one(rng):
    out = []
    for _ in range(20):
        digits = [rng.randint(0, 9) for _ in range(rng.randint(1, 15))]
        if digits[0] == 0:
            digits[0] = rng.randint(1, 9)
        out.append([digits])
    return out


def hidden_rotate_image(rng):
    out = []
    for _ in range(20):
        n = rng.randint(1, 7)
        matrix = [[rng.randint(-20, 20) for _ in range(n)] for _ in range(n)]
        out.append([matrix])
    return out


BLUEPRINTS: Dict[str, Blueprint] = {
    "find-minimum-in-rotated-sorted-array": Blueprint("def solve(nums: list[int]) -> int:", "Return the minimum value in a rotated sorted array of unique integers.", ["1 <= len(nums) <= 10^5", "-10^9 <= nums[i] <= 10^9", "nums is sorted then rotated at an unknown pivot."], "O(log n)", "O(1)", solve_find_min_rotated, [[[3, 4, 5, 1, 2]], [[4, 5, 6, 7, 0, 1, 2]], [[11, 13, 15, 17]], [[2, 1]], [[1]]], hidden_find_min, "Binary search compares mid against right boundary to isolate the unsorted half containing the minimum."),
    "search-in-rotated-sorted-array": Blueprint("def solve(nums: list[int], target: int) -> int:", "Return index of target in rotated sorted array, or -1 when absent.", ["1 <= len(nums) <= 10^5", "-10^4 <= nums[i], target <= 10^4", "All values are distinct."], "O(log n)", "O(1)", solve_search_rotated, [[[4, 5, 6, 7, 0, 1, 2], 0], [[4, 5, 6, 7, 0, 1, 2], 3], [[1], 0], [[1, 3], 3], [[5, 1, 3], 5]], hidden_search_rotated, "At each step one side is sorted; decide if target lies there and discard the other side."),
    "reverse-linked-list": Blueprint("def solve(values: list[int]) -> list[int]:", "Given linked-list values in order, return values after reversing the list.", ["0 <= len(values) <= 10^5", "-10^4 <= values[i] <= 10^4"], "O(n)", "O(1) extra", solve_reverse_linked_list, [[[1, 2, 3, 4, 5]], [[1, 2]], [[]], [[7]], [[-1, 0, 1]]], hidden_reverse_list, "Reverse pointer direction conceptually; array form mirrors this by reversing order."),
    "merge-two-sorted-lists": Blueprint("def solve(a: list[int], b: list[int]) -> list[int]:", "Merge two sorted lists into one sorted output.", ["0 <= len(a), len(b) <= 10^5", "-10^4 <= value <= 10^4", "Both inputs are individually sorted."], "O(n + m)", "O(1) extra", solve_merge_two_sorted_lists, [[[1, 2, 4], [1, 3, 4]], [[], []], [[], [0]], [[-3, 0, 5], [-2, 2, 9]], [[1], [2, 3, 4]]], hidden_merge_lists, "Two-pointer merge always selects smaller front element, preserving sorted order."),
    "reorder-list": Blueprint("def solve(values: list[int]) -> list[int]:", "Reorder list as L0, Ln, L1, Ln-1, ... and return resulting values.", ["1 <= len(values) <= 10^5", "-10^3 <= values[i] <= 10^3"], "O(n)", "O(n)", solve_reorder_list, [[[1, 2, 3, 4]], [[1, 2, 3, 4, 5]], [[1]], [[1, 2]], [[10, 20, 30, 40, 50, 60]]], hidden_reorder, "Split and interleave from both ends to emulate linked-list reorder pattern."),
    "remove-nth-node-from-end-of-list": Blueprint("def solve(values: list[int], n: int) -> list[int]:", "Remove the n-th node from the end and return remaining list values.", ["1 <= len(values) <= 10^5", "1 <= n <= len(values)"], "O(n)", "O(1) extra", solve_remove_nth, [[[1, 2, 3, 4, 5], 2], [[1], 1], [[1, 2], 1], [[1, 2], 2], [[10, 20, 30], 3]], hidden_remove_nth, "Locate removal index using length-n offset (two-pointer idea in linked-list form)."),
    "linked-list-cycle": Blueprint("def solve(values: list[int], pos: int) -> bool:", "Given list values and tail link index pos, return whether a cycle exists.", ["0 <= len(values) <= 10^5", "-1 <= pos < len(values)"], "O(1)", "O(1)", solve_linked_list_cycle, [[[3, 2, 0, -4], 1], [[1, 2], 0], [[1], -1], [[], -1], [[1], 0]], hidden_cycle, "Cycle exists exactly when tail points back to a valid index in this encoded representation."),
    "invert-binary-tree": Blueprint("def solve(tree_values: list[int | None]) -> list[int | None]:", "Invert a binary tree represented in level-order array form and return level-order output.", ["0 <= len(tree_values) <= 10^4", "-100 <= node value <= 100"], "O(n)", "O(h)", solve_invert_binary_tree, [[[4, 2, 7, 1, 3, 6, 9]], [[2, 1, 3]], [[]], [[1]], [[1, 2, 3, 4, None, 5, 6]]], hidden_tree_values, "Swap left and right subtree at each node with DFS or BFS traversal."),
    "maximum-depth-of-binary-tree": Blueprint("def solve(tree_values: list[int | None]) -> int:", "Return maximum depth of tree represented in level-order array form.", ["0 <= len(tree_values) <= 10^4"], "O(n)", "O(h)", solve_max_depth_tree, [[[3, 9, 20, None, None, 15, 7]], [[1, None, 2]], [[]], [[1]], [[1, 2, 3, 4, 5, None, None, 8]]], hidden_tree_values, "Depth is 1 + max(depth(left), depth(right)); compute recursively or iteratively."),
    "diameter-of-binary-tree": Blueprint("def solve(tree_values: list[int | None]) -> int:", "Return diameter (max edges on any path) of binary tree in level-order form.", ["0 <= len(tree_values) <= 10^4"], "O(n)", "O(h)", solve_diameter_tree, [[[1, 2, 3, 4, 5]], [[1, 2]], [[1]], [[]], [[1, 2, 3, 4, None, None, 5]]], hidden_tree_values, "Track best left_height + right_height while computing subtree heights."),
    "balanced-binary-tree": Blueprint("def solve(tree_values: list[int | None]) -> bool:", "Return True if every node's left/right subtree heights differ by at most one.", ["0 <= len(tree_values) <= 10^4"], "O(n)", "O(h)", solve_balanced_tree, [[[3, 9, 20, None, None, 15, 7]], [[1, 2, 2, 3, 3, None, None, 4, 4]], [[]], [[1]], [[1, 2, 3, 4, None, None, 5, 6]]], hidden_tree_values, "Post-order height computation can short-circuit when imbalance appears."),
    "same-tree": Blueprint("def solve(a: list[int | None], b: list[int | None]) -> bool:", "Return True if two trees in level-order representation are structurally identical with equal values.", ["0 <= len(a), len(b) <= 10^4"], "O(n)", "O(h)", solve_same_tree, [[[1, 2, 3], [1, 2, 3]], [[1, 2], [1, None, 2]], [[1, 2, 1], [1, 1, 2]], [[], []], [[1], [1]]], hidden_same_tree, "Synchronize traversal of both trees and compare value plus structure at each node."),
    "subtree-of-another-tree": Blueprint("def solve(root_vals: list[int | None], sub_vals: list[int | None]) -> bool:", "Return True if sub_vals tree occurs as a subtree in root_vals tree.", ["0 <= len(root_vals), len(sub_vals) <= 10^4"], "O(n * m)", "O(h)", solve_subtree, [[[3, 4, 5, 1, 2], [4, 1, 2]], [[3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]], [[], []], [[1, 1], [1]], [[1, 2, 3], [2]]], hidden_subtree, "Scan candidate roots and run equality check when values align."),
    "binary-tree-level-order-traversal": Blueprint("def solve(tree_values: list[int | None]) -> list[list[int]]:", "Return node values level by level from top to bottom.", ["0 <= len(tree_values) <= 10^4"], "O(n)", "O(n)", solve_level_order, [[[3, 9, 20, None, None, 15, 7]], [[1]], [[]], [[1, 2, 3, 4, None, None, 5]], [[1, None, 2, None, 3]]], hidden_tree_values, "Breadth-first traversal naturally emits one list per level."),
    "kth-largest-element-in-an-array": Blueprint("def solve(nums: list[int], k: int) -> int:", "Return the k-th largest element in the array.", ["1 <= len(nums) <= 10^5", "1 <= k <= len(nums)"], "O(n log k)", "O(k)", solve_kth_largest, [[[3, 2, 1, 5, 6, 4], 2], [[3, 2, 3, 1, 2, 4, 5, 5, 6], 4], [[1], 1], [[7, 6, 5, 4], 1], [[7, 6, 5, 4], 4]], hidden_kth_largest, "Maintain min-heap of size k so heap root is current k-th largest."),
    "task-scheduler": Blueprint("def solve(tasks: list[str], n: int) -> int:", "Return least intervals needed to execute tasks with cooldown n.", ["1 <= len(tasks) <= 10^4", "0 <= n <= 100"], "O(m)", "O(1)", solve_task_scheduler, [[["A", "A", "A", "B", "B", "B"], 2], [["A", "A", "A", "B", "B", "B"], 0], [["A", "A", "A", "A", "B", "C", "D"], 2], [["A"], 10], [["A", "B", "C", "A", "B", "C"], 3]], hidden_task_scheduler, "Use frequency frame formula based on most frequent task blocks."),
    "find-median-from-data-stream": Blueprint("def solve(operations: list[str], values: list[list[int]]) -> list[float | None]:", "Simulate MedianFinder operations. Return None for constructor/addNum, median for findMedian.", ["1 <= len(operations) <= 10^4", "operations[i] in {MedianFinder, addNum, findMedian}"], "O(log n) per add", "O(n)", solve_median_stream, [[["MedianFinder", "addNum", "addNum", "findMedian", "addNum", "findMedian"], [[], [1], [2], [], [3], []]], [["MedianFinder", "addNum", "findMedian"], [[], [5], []]], [["MedianFinder", "addNum", "addNum", "findMedian"], [[], [2], [4], []]], [["MedianFinder", "addNum", "addNum", "addNum", "findMedian"], [[], [7], [1], [3], []]], [["MedianFinder", "addNum", "findMedian", "addNum", "findMedian"], [[], [10], [], [20], []]]], hidden_median_stream, "Two heaps maintain lower and upper halves; rebalance after each insertion."),
    "merge-k-sorted-lists": Blueprint("def solve(lists: list[list[int]]) -> list[int]:", "Merge k sorted lists into one sorted output list.", ["0 <= k <= 10^4", "0 <= total elements <= 10^5"], "O(N log k)", "O(k)", solve_merge_k_lists, [[[[1, 4, 5], [1, 3, 4], [2, 6]]], [[[ ]]], [[[ ] , [ ]]], [[[1], [0]]], [[[2, 2], [1, 3], [0, 4, 5]]]], hidden_merge_k_lists, "Heap across list heads always extracts globally smallest remaining value."),
    "subsets": Blueprint("def solve(nums: list[int]) -> list[list[int]]:", "Return all subsets (power set) in deterministic sorted order.", ["0 <= len(nums) <= 10", "-10 <= nums[i] <= 10", "Input values are distinct."], "O(n * 2^n)", "O(n * 2^n)", solve_subsets, [[[1, 2, 3]], [[0]], [[]], [[-1, 1]], [[1, 2, 3, 4]]], hidden_subsets, "Each number doubles subset count: include it or exclude it."),
    "combination-sum": Blueprint("def solve(candidates: list[int], target: int) -> list[list[int]]:", "Return combinations summing to target; each candidate may be reused.", ["1 <= len(candidates) <= 30", "1 <= target <= 200"], "O(number of valid states)", "O(target)", solve_combination_sum, [[[2, 3, 6, 7], 7], [[2, 3, 5], 8], [[2], 1], [[1], 2], [[3, 4, 5], 12]], hidden_combination_sum, "Backtracking chooses candidate counts while pruning sums above target."),
    "permutations": Blueprint("def solve(nums: list[int]) -> list[list[int]]:", "Return all permutations in lexicographic order.", ["1 <= len(nums) <= 8", "Values are distinct."], "O(n * n!)", "O(n)", solve_permutations, [[[1, 2, 3]], [[0, 1]], [[1]], [[-1, 0, 1]], [[3, 2, 1]]], hidden_permutations, "Build permutations incrementally by fixing each value at current position."),
    "word-search": Blueprint("def solve(board: list[list[str]], word: str) -> bool:", "Return True if word can be formed by sequentially adjacent cells without reuse.", ["1 <= rows, cols <= 6", "1 <= len(word) <= 15"], "O(rows*cols*4^L)", "O(L)", solve_word_search, [[[["A", "B", "C", "E"], ["S", "F", "C", "S"], ["A", "D", "E", "E"]], "ABCCED"], [[["A", "B"], ["C", "D"]], "ABCD"], [[["A"]], "A"], [[["A", "A"]], "AAA"], [[["C", "A", "T"]], "CAT"]], hidden_word_search, "DFS with temporary marking explores paths while preventing cell reuse."),
    "number-of-islands": Blueprint("def solve(grid: list[list[str]]) -> int:", "Count connected components of land cells ('1') via 4-directional adjacency.", ["1 <= rows, cols <= 200"], "O(rows*cols)", "O(rows*cols) worst recursion/stack", solve_number_of_islands, [[[["1", "1", "1", "1", "0"], ["1", "1", "0", "1", "0"], ["1", "1", "0", "0", "0"], ["0", "0", "0", "0", "0"]]], [[["1", "1", "0", "0", "0"], ["1", "1", "0", "0", "0"], ["0", "0", "1", "0", "0"], ["0", "0", "0", "1", "1"]]], [[["0"]],], [[["1"]],], [[["1", "0", "1"]],]], hidden_num_islands, "Flood-fill each unvisited land cell and count how many floods are started."),
    "clone-graph": Blueprint("def solve(adj: list[list[int]]) -> list[list[int]]:", "Clone an undirected graph adjacency list and return cloned adjacency list.", ["1 <= number of nodes <= 100"], "O(V + E)", "O(V)", solve_clone_graph, [[[[2, 4], [1, 3], [2, 4], [1, 3]]], [[[]]], [[[2], [1]]], [[[2, 3], [1], [1]]], [[[2], [1, 3], [2]]]], hidden_clone_graph, "Use map from original node id to cloned node and copy neighbor edges."),
    "pacific-atlantic-water-flow": Blueprint("def solve(heights: list[list[int]]) -> list[list[int]]:", "Return coordinates that can reach both Pacific and Atlantic oceans.", ["1 <= rows, cols <= 200", "0 <= heights[r][c] <= 10^5"], "O(rows*cols)", "O(rows*cols)", solve_pacific_atlantic, [[[[1, 2, 2, 3, 5], [3, 2, 3, 4, 4], [2, 4, 5, 3, 1], [6, 7, 1, 4, 5], [5, 1, 1, 2, 4]]], [[[1]]], [[[1, 1], [1, 1]]], [[[10, 10, 10], [10, 1, 10], [10, 10, 10]]], [[[3, 3, 3]]]], hidden_pacific_atlantic, "Reverse-flow BFS/DFS from ocean borders intersects cells reachable from both sides."),
    "course-schedule": Blueprint("def solve(num_courses: int, prerequisites: list[list[int]]) -> bool:", "Return True if all courses can be completed given prerequisite pairs [course, prereq].", ["1 <= num_courses <= 2000", "0 <= len(prerequisites) <= 5000"], "O(V + E)", "O(V + E)", solve_course_schedule, [[2, [[1, 0]]], [2, [[1, 0], [0, 1]]], [1, []], [3, [[1, 0], [2, 1]]], [3, [[0, 1], [1, 2], [2, 0]]]], hidden_course_schedule, "Topological feasibility holds exactly when all nodes can be removed by indegree-zero process."),
    "course-schedule-ii": Blueprint("def solve(num_courses: int, prerequisites: list[list[int]]) -> list[int]:", "Return one valid course order; return [] when impossible.", ["1 <= num_courses <= 2000", "0 <= len(prerequisites) <= 5000"], "O(V + E)", "O(V + E)", solve_course_schedule_ii, [[2, [[1, 0]]], [4, [[1, 0], [2, 0], [3, 1], [3, 2]]], [1, []], [2, [[0, 1], [1, 0]]], [3, [[1, 0], [2, 1]]]], hidden_course_schedule, "Produce topological order with indegree queue; failure indicates cycle."),
    "graph-valid-tree": Blueprint("def solve(n: int, edges: list[list[int]]) -> bool:", "Return True if undirected graph is a valid tree.", ["1 <= n <= 2000", "0 <= len(edges) <= 5000"], "O(n + e)", "O(n)", solve_graph_valid_tree, [[5, [[0, 1], [0, 2], [0, 3], [1, 4]]], [5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]], [1, []], [2, [[0, 1]]], [4, [[0, 1], [2, 3], [1, 2]]]], hidden_graph_valid_tree, "Tree iff edges == n-1 and graph has no cycle (or equivalently is connected)."),
    "network-delay-time": Blueprint("def solve(times: list[list[int]], n: int, k: int) -> int:", "Return time for signal from k to reach all nodes, or -1 if unreachable.", ["1 <= n <= 100", "1 <= len(times) <= 6000"], "O((V + E) log V)", "O(V + E)", solve_network_delay, [[[[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2], [[[1, 2, 1]], 2, 1], [[[1, 2, 1]], 2, 2], [[[1, 2, 2], [1, 3, 1], [3, 2, 1]], 3, 1], [[[1, 2, 5], [2, 3, 2], [1, 3, 9]], 3, 1]], hidden_network_delay, "Dijkstra computes shortest arrival times in non-negative weighted directed graph."),
    "climbing-stairs": Blueprint("def solve(n: int) -> int:", "Return number of distinct ways to climb n stairs with steps of 1 or 2.", ["1 <= n <= 45"], "O(n)", "O(1)", solve_climbing_stairs, [[2], [3], [1], [5], [10]], hidden_stairs, "This is Fibonacci recurrence: ways(n)=ways(n-1)+ways(n-2)."),
    "house-robber": Blueprint("def solve(nums: list[int]) -> int:", "Return max money without robbing adjacent houses.", ["1 <= len(nums) <= 100", "0 <= nums[i] <= 400"], "O(n)", "O(1)", solve_house_robber, [[[1, 2, 3, 1]], [[2, 7, 9, 3, 1]], [[2, 1, 1, 2]], [[5]], [[0, 0, 0]]], hidden_house_robber, "DP state tracks best when robbing or skipping each position."),
    "house-robber-ii": Blueprint("def solve(nums: list[int]) -> int:", "Houses are in a circle. Return max money without adjacent robberies.", ["1 <= len(nums) <= 100", "0 <= nums[i] <= 400"], "O(n)", "O(1)", solve_house_robber_ii, [[[2, 3, 2]], [[1, 2, 3, 1]], [[1, 2, 3]], [[1]], [[4, 1, 2, 7, 5, 3, 1]]], hidden_house_robber, "Solve two linear cases: exclude first or exclude last house."),
    "coin-change": Blueprint("def solve(coins: list[int], amount: int) -> int:", "Return fewest coins needed to make amount; -1 if impossible.", ["1 <= len(coins) <= 12", "0 <= amount <= 10^4"], "O(len(coins)*amount)", "O(amount)", solve_coin_change, [[[1, 2, 5], 11], [[2], 3], [[1], 0], [[1, 3, 4], 6], [[2, 5, 10, 1], 27]], hidden_coin_change, "Unbounded knapsack DP computes best count for every total up to amount."),
    "longest-increasing-subsequence": Blueprint("def solve(nums: list[int]) -> int:", "Return length of longest strictly increasing subsequence.", ["1 <= len(nums) <= 2500", "-10^4 <= nums[i] <= 10^4"], "O(n log n)", "O(n)", solve_lis, [[[10, 9, 2, 5, 3, 7, 101, 18]], [[0, 1, 0, 3, 2, 3]], [[7, 7, 7, 7, 7]], [[1]], [[4, 10, 4, 3, 8, 9]]], hidden_lis, "Patience sorting tails array stores best possible tail for each LIS length."),
    "partition-equal-subset-sum": Blueprint("def solve(nums: list[int]) -> bool:", "Return True if nums can be partitioned into two subsets with equal sum.", ["1 <= len(nums) <= 200", "1 <= nums[i] <= 100"], "O(n * target)", "O(target)", solve_partition_equal_subset, [[[1, 5, 11, 5]], [[1, 2, 3, 5]], [[2, 2, 1, 1]], [[1]], [[3, 3, 3, 4, 5]]], hidden_partition, "Subset-sum to total/2 determines if equal partition exists."),
    "unique-paths": Blueprint("def solve(m: int, n: int) -> int:", "Return number of unique paths from top-left to bottom-right moving only down/right.", ["1 <= m, n <= 100"], "O(m*n)", "O(n)", solve_unique_paths, [[3, 7], [3, 2], [1, 1], [10, 10], [5, 1]], hidden_unique_paths, "Each cell paths = top + left; rolling array computes row by row."),
    "longest-common-subsequence": Blueprint("def solve(text1: str, text2: str) -> int:", "Return length of longest common subsequence.", ["1 <= len(text1), len(text2) <= 1000"], "O(m*n)", "O(m*n)", solve_lcs, [["abcde", "ace"], ["abc", "abc"], ["abc", "def"], ["bl", "yby"], ["ezupkr", "ubmrapg"]], hidden_lcs, "2D DP compares character match vs skipping one character from either side."),
    "jump-game": Blueprint("def solve(nums: list[int]) -> bool:", "Return whether end index is reachable from start with jump lengths nums[i].", ["1 <= len(nums) <= 10^4", "0 <= nums[i] <= 10^5"], "O(n)", "O(1)", solve_jump_game, [[[2, 3, 1, 1, 4]], [[3, 2, 1, 0, 4]], [[0]], [[2, 0, 0]], [[1, 1, 0, 1]]], hidden_jump, "Greedy farthest-reach invariant determines reachability in one pass."),
    "jump-game-ii": Blueprint("def solve(nums: list[int]) -> int:", "Return minimum jumps needed to reach last index.", ["1 <= len(nums) <= 10^4", "Guaranteed reachable."], "O(n)", "O(1)", solve_jump_game_ii, [[[2, 3, 1, 1, 4]], [[2, 3, 0, 1, 4]], [[0]], [[1, 1, 1, 1]], [[5, 4, 3, 2, 1, 1, 1]]], hidden_jump, "Layered greedy BFS over index ranges yields minimum jump count."),
    "gas-station": Blueprint("def solve(gas: list[int], cost: list[int]) -> int:", "Return start index to complete circuit once, else -1.", ["1 <= len(gas) == len(cost) <= 10^5", "0 <= gas[i], cost[i] <= 10^4"], "O(n)", "O(1)", solve_gas_station, [[[1, 2, 3, 4, 5], [3, 4, 5, 1, 2]], [[2, 3, 4], [3, 4, 3]], [[5], [4]], [[5], [6]], [[3, 1, 1], [1, 2, 2]]], hidden_gas_station, "If cumulative fuel drops below zero, previous starts are impossible; reset start."),
    "merge-intervals": Blueprint("def solve(intervals: list[list[int]]) -> list[list[int]]:", "Merge overlapping intervals and return sorted merged list.", ["0 <= len(intervals) <= 10^4"], "O(n log n)", "O(n)", solve_merge_intervals, [[[[1, 3], [2, 6], [8, 10], [15, 18]]], [[[1, 4], [4, 5]]], [[]], [[[1, 4], [0, 2], [3, 5]]], [[[2, 3]]]], hidden_intervals, "Sort by start; merge into running interval when overlap exists."),
    "insert-interval": Blueprint("def solve(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:", "Insert new interval into sorted non-overlapping intervals and merge where needed.", ["0 <= len(intervals) <= 10^4"], "O(n)", "O(n)", solve_insert_interval, [[[[1, 3], [6, 9]], [2, 5]], [[[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]], [[], [5, 7]], [[[1, 5]], [2, 3]], [[[1, 5]], [2, 7]]], hidden_insert_interval, "Copy left non-overlap, merge overlap zone, append right non-overlap."),
    "non-overlapping-intervals": Blueprint("def solve(intervals: list[list[int]]) -> int:", "Return minimum number of intervals to remove so rest are non-overlapping.", ["1 <= len(intervals) <= 10^5"], "O(n log n)", "O(1)", solve_non_overlapping_intervals, [[[[1, 2], [2, 3], [3, 4], [1, 3]]], [[[1, 2], [1, 2], [1, 2]]], [[[1, 2], [2, 3]]], [[[1, 100], [11, 22], [1, 11], [2, 12]]], [[[0, 2], [1, 3], [2, 4], [3, 5]]]], hidden_intervals, "Greedy by earliest finishing interval keeps maximum compatible set."),
    "single-number": Blueprint("def solve(nums: list[int]) -> int:", "Every element appears twice except one. Return the single one.", ["1 <= len(nums) <= 3*10^4"], "O(n)", "O(1)", solve_single_number, [[[2, 2, 1]], [[4, 1, 2, 1, 2]], [[1]], [[-1, -1, -2]], [[7, 3, 5, 3, 5]]], hidden_single_number, "XOR cancels paired values and leaves unique value."),
    "number-of-1-bits": Blueprint("def solve(n: int) -> int:", "Return number of set bits in non-negative integer n.", ["0 <= n <= 2^31 - 1"], "O(k)", "O(1)", solve_number_of_1_bits, [[11], [128], [2147483645], [0], [1]], hidden_hamming, "Repeatedly clear lowest set bit with n &= n-1."),
    "counting-bits": Blueprint("def solve(n: int) -> list[int]:", "Return bit counts for every integer in range [0, n].", ["0 <= n <= 10^5"], "O(n)", "O(n)", solve_counting_bits, [[2], [5], [0], [1], [10]], hidden_count_bits, "DP recurrence: bits[i] = bits[i>>1] + (i & 1)."),
    "powx-n": Blueprint("def solve(x: float, n: int) -> float:", "Return x raised to power n using fast exponentiation.", ["-100.0 < x < 100.0", "-2^31 <= n <= 2^31-1"], "O(log |n|)", "O(1)", solve_powx_n, [[2.0, 10], [2.1, 3], [2.0, -2], [1.5, 0], [-2.0, 5]], hidden_pow, "Exponentiation by squaring halves exponent each step."),
    "happy-number": Blueprint("def solve(n: int) -> bool:", "Return True if repeated sum of squares of digits reaches 1.", ["1 <= n <= 2^31 - 1"], "O(log n)", "O(log n)", solve_happy_number, [[19], [2], [1], [7], [1111111]], hidden_happy, "Detect loop with visited set while iterating digit-square transform."),
    "plus-one": Blueprint("def solve(digits: list[int]) -> list[int]:", "Given non-empty integer digits, add one and return resulting digits.", ["1 <= len(digits) <= 100", "0 <= digits[i] <= 9"], "O(n)", "O(1) extra", solve_plus_one, [[[1, 2, 3]], [[4, 3, 2, 1]], [[9]], [[9, 9, 9]], [[2, 9, 9]]], hidden_plus_one, "Propagate carry from right to left and add new leading digit if needed."),
    "rotate-image": Blueprint("def solve(matrix: list[list[int]]) -> list[list[int]]:", "Rotate an n x n matrix by 90 degrees clockwise and return rotated matrix.", ["1 <= n <= 20", "-1000 <= matrix[r][c] <= 1000"], "O(n^2)", "O(n^2)", solve_rotate_image, [[[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], [[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]], [[[1]]], [[[1, 2], [3, 4]]], [[[-1, -2], [-3, -4]]]], hidden_rotate_image, "Map (r,c) to (c,n-1-r) for clockwise rotation."),
}


TOPIC_HINTS = {
    "Binary Search": [
        "Identify a monotonic condition that lets you discard half the search range.",
        "Track loop invariants for left/right boundaries to avoid off-by-one errors.",
        "Use boundary-focused dry runs on tiny and two-element inputs.",
    ],
    "Linked List": [
        "Translate pointer behavior into index movement before coding.",
        "Preserve critical references before rewiring links or removing nodes.",
        "Validate edge cases: empty list, one node, and boundary removals.",
    ],
    "Trees": [
        "Decide traversal order first: pre-order, in-order, post-order, or BFS.",
        "Define what each recursive call returns and what state it updates.",
        "Dry-run on sparse trees with None gaps to confirm structure handling.",
    ],
    "Heap": [
        "Use heap for repeated min/max extraction under dynamic updates.",
        "Keep heap size constrained when only top-k elements matter.",
        "Watch tie-handling and deterministic ordering for stable outputs.",
    ],
    "Backtracking": [
        "Define the decision tree state clearly: index, path, and remaining target.",
        "Add pruning conditions early to cut invalid branches.",
        "Backtrack by undoing the exact state changes made before recursion.",
    ],
    "Graphs": [
        "Choose BFS/DFS/topological strategy based on edge direction and goal.",
        "Track visited state carefully to avoid repeated work or cycles.",
        "Verify disconnected components and unreachable node behavior.",
    ],
    "Dynamic Programming": [
        "Write state definition first, then recurrence and base cases.",
        "Check transition dependencies to choose 1D vs 2D DP storage.",
        "Run smallest cases manually to confirm recurrence correctness.",
    ],
    "Greedy": [
        "Find an invariant proving local optimal choices lead to global optimum.",
        "Track the exact state metric that determines next greedy action.",
        "Challenge your approach with counterexamples before finalizing.",
    ],
    "Intervals": [
        "Sort intervals by the axis relevant to merge/remove decisions.",
        "Update current active interval boundaries only when overlap exists.",
        "Test touching endpoints and nested intervals explicitly.",
    ],
    "Bit Manipulation": [
        "Use bit identities to avoid loops over all bit positions when possible.",
        "Verify behavior on zero and large values near boundary limits.",
        "Keep signed/unsigned interpretation consistent with constraints.",
    ],
    "Math": [
        "Convert repeated operations into logarithmic-time transformations.",
        "Handle numerical edge cases (zero, negatives, carry, precision) explicitly.",
        "Validate with boundary values and algebraic identities.",
    ],
}


def topic_key(topic: str) -> str:
    mapping = {
        "Graphs": "Graphs",
        "Dynamic Programming": "Dynamic Programming",
        "Bit Manipulation": "Bit Manipulation",
        "Binary Search": "Binary Search",
        "Linked List": "Linked List",
        "Trees": "Trees",
        "Heap": "Heap",
        "Backtracking": "Backtracking",
        "Greedy": "Greedy",
        "Intervals": "Intervals",
        "Math": "Math",
    }
    return mapping.get(topic, topic)


def make_hints(topic: str, task: str) -> List[str]:
    base = TOPIC_HINTS.get(topic_key(topic), TOPIC_HINTS["Math"])
    return [base[0], base[1], base[2]]


def make_common_mistakes(pattern: str) -> List[str]:
    return [
        f"Applying a brute-force {pattern} approach and exceeding time limits on stress inputs.",
        "Ignoring edge cases around empty or single-element structures.",
        "Breaking index or boundary invariants during updates and producing off-by-one errors.",
    ]


def solver_to_reference_code(solver: Callable[..., Any]) -> str:
    source = inspect.getsource(solver)
    source = re.sub(r"^def\s+\w+\(", "def solve(", source, count=1, flags=re.MULTILINE)
    helper_code = ""
    if any(name in source for name in ("parse_tree(", "serialize_tree(", "normalize_tree(")):
        helper_code = """
def normalize_tree(values):
    while values and values[-1] is None:
        values.pop()
    return values

def parse_tree(values):
    if not values:
        return None
    nodes = [None if value is None else {"val": value, "left": None, "right": None} for value in values]
    kids = collections.deque(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        if kids:
            node["left"] = kids.popleft()
        if kids:
            node["right"] = kids.popleft()
    return nodes[0]

def serialize_tree(root):
    if root is None:
        return []
    out = []
    queue = collections.deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node["val"])
        queue.append(node["left"])
        queue.append(node["right"])
    return normalize_tree(out)
""".strip()
    if helper_code:
        return helper_code + "\n\n" + source.strip() + "\n"
    return source.strip() + "\n"


def signature_to_starter(signature: str) -> str:
    line = re.sub(r":\s*[^:]+$", ":", signature.strip())
    body = "    return None\n"
    return f"{line}\n{body}"


def explanation_for_case(label: str) -> str:
    return CASE_EXPLANATION_TEXT.get(label, "Case validates expected behavior.")


def build_cases(slug: str, input_rows: List[List[Any]], solver: Callable[..., Any]) -> List[Dict[str, Any]]:
    cases = []
    for idx, args in enumerate(input_rows):
        normalized_args = [as_jsonable(arg) for arg in args]
        calc_args = json.loads(json.dumps(normalized_args))
        expected = as_jsonable(solver(*calc_args))
        label = CATEGORY_LABELS[idx % len(CATEGORY_LABELS)]
        cases.append(
            {
                "input": normalized_args,
                "expected": expected,
                "explanation": f"{label}: {explanation_for_case(label)}",
                "weight": 1.0,
            }
        )
    return cases


def build_examples_md(visible_cases: List[Dict[str, Any]]) -> str:
    blocks = []
    for idx, case in enumerate(visible_cases[:3], start=1):
        blocks.append(
            f"Example {idx}\n"
            f"Input: `{json.dumps(case['input'], ensure_ascii=False)}`\n"
            f"Output: `{json.dumps(case['expected'], ensure_ascii=False)}`\n"
            f"Explanation: {case['explanation']}"
        )
    return "\n\n".join(blocks)


def build_editorial(title: str, blueprint: Blueprint) -> str:
    return (
        f"### Intuition\n{blueprint.algorithm_note}\n\n"
        f"### Algorithm\nImplement the logic described by the function signature and maintain the key invariant through each transition.\n\n"
        f"### Correctness\nEach step preserves problem constraints while moving toward termination. Once the loop/recursion stops, the returned value satisfies the exact task definition for `{title}`.\n\n"
        f"### Implementation Notes\n"
        f"- Respect the input/output representation used in tests.\n"
        f"- Validate boundaries before reading neighbors or indices.\n"
        f"- Keep updates atomic when mutating state.\n\n"
        f"### Complexity\n"
        f"- Time: `{blueprint.time_complexity}`\n"
        f"- Space: `{blueprint.space_complexity}`"
    )


def build_statement(title: str, topic: str, blueprint: Blueprint) -> str:
    return (
        f"Solve `{title}` from the {topic} curriculum.\n\n"
        f"Task\n{blueprint.task}\n\n"
        f"Function Signature\n`{blueprint.signature}`\n\n"
        "Input/Output Contract\n"
        "- Read all inputs from function arguments.\n"
        "- Return the computed result in the same shape shown in examples.\n"
        "- Do not print from the function."
    )


def build_recommendation_maps(graph_payload: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
    out: Dict[str, Dict[str, List[str]]] = {
        "prerequisite": collections.defaultdict(list),
        "follow_up": collections.defaultdict(list),
        "alternative": collections.defaultdict(list),
        "review": collections.defaultdict(list),
        "recovery": collections.defaultdict(list),
    }

    for edge in graph_payload.get("prerequisite_edges", []):
        source = edge["from"]
        target = edge["to"]
        out["follow_up"][source].append(target)
        out["prerequisite"][target].append(source)
    for edge in graph_payload.get("alternative_edges", []):
        if isinstance(edge, list) and len(edge) == 2:
            source, target = edge
            out["alternative"][source].append(target)
            out["alternative"][target].append(source)
    for edge in graph_payload.get("review_edges", []):
        trigger = edge.get("trigger_problem")
        targets = edge.get("review_problems") or []
        if isinstance(trigger, str):
            for target in targets:
                if isinstance(target, str):
                    out["review"][trigger].append(target)
    for edge in graph_payload.get("recovery_edges", []):
        trigger = edge.get("struggling_problem")
        targets = edge.get("recover_with") or []
        if isinstance(trigger, str):
            for target in targets:
                if isinstance(target, str):
                    out["recovery"][trigger].append(target)
    return out


def build_related_map(graph_payload: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = collections.defaultdict(list)
    for edge in graph_payload.get("stretch_edges", []):
        source = edge.get("from_problem")
        targets = edge.get("stretch_to") or []
        if isinstance(source, str):
            for target in targets:
                if isinstance(target, str):
                    out[source].append(target)
    return out


def build_problem(
    curriculum_problem: Dict[str, Any],
    blueprint: Blueprint,
    recommendation_graph: Dict[str, Dict[str, List[str]]],
    related_map: Dict[str, List[str]],
    subset_slugs: set[str],
    ordered_slugs: List[str],
    order_index: int,
) -> Dict[str, Any]:
    slug = curriculum_problem["slug"]
    title = curriculum_problem["title"]
    topic = curriculum_problem["topic"]
    difficulty = curriculum_problem["difficulty"]
    rng = random.Random(f"phase3f-{slug}-2026")

    visible_cases = build_cases(slug, blueprint.visible_inputs, blueprint.solver)
    hidden_inputs = blueprint.hidden_builder(rng)
    hidden_cases = build_cases(slug, hidden_inputs, blueprint.solver)
    if len(visible_cases) < 5:
        raise ValueError(f"{slug}: need at least 5 visible tests")
    if len(hidden_cases) < 20:
        raise ValueError(f"{slug}: need at least 20 hidden tests")

    prereq = [item for item in recommendation_graph["prerequisite"].get(slug, []) if item in subset_slugs]
    alternative = [item for item in recommendation_graph["alternative"].get(slug, []) if item in subset_slugs]
    follow_up = [item for item in recommendation_graph["follow_up"].get(slug, []) if item in subset_slugs]
    review = [item for item in recommendation_graph["review"].get(slug, []) if item in subset_slugs]
    recovery = [item for item in recommendation_graph["recovery"].get(slug, []) if item in subset_slugs]
    related = [item for item in related_map.get(slug, []) if item in subset_slugs and item != slug]
    if not (prereq or alternative or follow_up or review or recovery or related):
        if order_index > 0:
            prereq = [ordered_slugs[order_index - 1]]
        if order_index < len(ordered_slugs) - 1:
            follow_up = [ordered_slugs[order_index + 1]]
            related = [ordered_slugs[order_index + 1]]

    hints = make_hints(topic, blueprint.task)
    mistakes = make_common_mistakes(curriculum_problem["pattern"])
    objectives = list(curriculum_problem.get("learning_objectives") or [])

    return {
        "problem_id": slug,
        "title": title,
        "topic": topic,
        "subtopic": curriculum_problem["subtopic"],
        "pattern": curriculum_problem["pattern"],
        "difficulty": difficulty,
        "metadata": {
            "company_tags": ["google", "amazon", "microsoft"],
            "source": "premium-phase3f-internal",
            "source_citation": f"curriculum/{slug}",
            "estimated_minutes": int(curriculum_problem["estimated_solving_time_minutes"]),
            "tags": sorted(set([slug, topic.lower().replace(" ", "-"), difficulty.lower(), "premium"])),
            "recommendation_prerequisites": list(curriculum_problem.get("recommendation_prerequisites") or []),
            "review_prerequisites": list(curriculum_problem.get("review_prerequisites") or []),
        },
        "educational_assets": {
            "statement_md": build_statement(title, topic, blueprint),
            "constraints_md": "\n".join(f"- {line}" for line in blueprint.constraints),
            "examples_md": build_examples_md(visible_cases),
            "editorial_md": build_editorial(title, blueprint),
        },
        "hints": [{"order": idx + 1, "text_md": hint} for idx, hint in enumerate(hints)],
        "reference_solution": {
            "language": "python",
            "code": solver_to_reference_code(blueprint.solver),
            "time_complexity": blueprint.time_complexity,
            "space_complexity": blueprint.space_complexity,
        },
        "starter_code": {
            "language": "python",
            "function_name": "solve",
            "code": signature_to_starter(blueprint.signature),
        },
        "tests": {"visible": visible_cases[:10], "hidden": hidden_cases[:50]},
        "recommendation_graph": {
            "prerequisite": sorted(set(prereq)),
            "alternative": sorted(set(alternative)),
            "follow_up": sorted(set(follow_up)),
            "review": sorted(set(review)),
            "recovery": sorted(set(recovery)),
        },
        "learning_objectives": objectives,
        "common_mistakes": mistakes,
        "prerequisites": list(curriculum_problem.get("prerequisites") or []),
        "related_problems": sorted(set(related)),
        "rag_assets": {
            "statement_chunks": list(dict.fromkeys([f"{title}: {blueprint.task}", f"Function signature: {blueprint.signature}"])),
            "editorial_chunks": list(dict.fromkeys([blueprint.algorithm_note, f"Complexity target: time {blueprint.time_complexity}, space {blueprint.space_complexity}."])),
            "hints_chunks": list(dict.fromkeys(hints)),
            "common_mistakes_chunks": list(dict.fromkeys(mistakes)),
            "learning_objectives_chunks": list(dict.fromkeys(objectives)),
        },
        "version": 1,
    }


def normalize_existing(existing_problem: Dict[str, Any]) -> Dict[str, Any]:
    out = json.loads(json.dumps(existing_problem))
    out["metadata"]["source"] = "premium-phase3f-internal"
    out["metadata"]["source_citation"] = f"curriculum/{out['problem_id']}"
    out["metadata"]["company_tags"] = out["metadata"].get("company_tags") or ["google", "amazon", "microsoft"]
    out["metadata"]["tags"] = sorted(set(out["metadata"].get("tags") or []))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate full premium problem bank for Phase 3F (Problems 1-75).")
    parser.add_argument("--curriculum-path", default="data/premium/curriculum/curriculum.json")
    parser.add_argument("--recommendation-graph-path", default="data/premium/curriculum/recommendation_graph.json")
    parser.add_argument("--existing-bank-path", default="data/premium/problem_bank.json")
    parser.add_argument("--output-path", default="data/premium/problem_bank.json")
    parser.add_argument("--report-path", default="reports/phase3/phase3f_generation_report.json")
    args = parser.parse_args()

    curriculum = json.loads(Path(args.curriculum_path).read_text(encoding="utf-8"))["problems"]
    graph_payload = json.loads(Path(args.recommendation_graph_path).read_text(encoding="utf-8"))
    existing_payload = json.loads(Path(args.existing_bank_path).read_text(encoding="utf-8"))
    existing_by_id = {problem["problem_id"]: problem for problem in existing_payload.get("problems", [])}

    ordered_slugs = [item["slug"] for item in curriculum]
    subset_slugs = set(ordered_slugs)
    recommendation_maps = build_recommendation_maps(graph_payload)
    related_map = build_related_map(graph_payload)

    output_problems = []
    generated_count = 0
    for idx, item in enumerate(curriculum):
        slug = item["slug"]
        if slug in BLUEPRINTS:
            blueprint = BLUEPRINTS[slug]
            output_problems.append(
                build_problem(
                    curriculum_problem=item,
                    blueprint=blueprint,
                    recommendation_graph=recommendation_maps,
                    related_map=related_map,
                    subset_slugs=subset_slugs,
                    ordered_slugs=ordered_slugs,
                    order_index=idx,
                )
            )
            generated_count += 1
            continue
        if slug in existing_by_id:
            output_problems.append(normalize_existing(existing_by_id[slug]))
            continue
        raise ValueError(f"Missing source problem for slug: {slug}")

    report = {
        "summary": {
            "new_problems_generated": generated_count,
            "total_problems": len(output_problems),
            "visible_tests": sum(len(problem["tests"]["visible"]) for problem in output_problems),
            "hidden_tests": sum(len(problem["tests"]["hidden"]) for problem in output_problems),
        }
    }

    payload = {
        "schema_version": "1.0",
        "generated_at": "2026-06-28T00:00:00Z",
        "phase": "3F",
        "problem_count": len(output_problems),
        "problems": output_problems,
    }
    Path(args.output_path).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    Path(args.report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report_path).write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
