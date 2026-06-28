#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import heapq
import json
import math
import random
import re
import string
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.judge import JudgeService


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

STRING_FOCUSED_LABELS = [
    "minimum_input",
    "single_element",
    "empty_input",
    "duplicates",
    "boundary_conditions",
    "maximum_input",
]

STRING_PROBLEMS = {
    "valid-anagram",
    "group-anagrams",
    "valid-palindrome",
    "longest-substring-without-repeating-characters",
    "longest-repeating-character-replacement",
    "permutation-in-string",
    "minimum-window-substring",
    "valid-parentheses",
    "evaluate-reverse-polish-notation",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return [as_jsonable(item) for item in value]
    if isinstance(value, list):
        return [as_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    return value


def is_alnum(ch: str) -> bool:
    return ch.isalnum()


def solve_two_sum(nums: List[int], target: int) -> List[int]:
    seen: Dict[int, int] = {}
    for idx, num in enumerate(nums):
        need = target - num
        if need in seen:
            return [seen[need], idx]
        seen[num] = idx
    return []


def solve_contains_duplicate(nums: List[int]) -> bool:
    return len(nums) != len(set(nums))


def solve_valid_anagram(s: str, t: str) -> bool:
    return collections.Counter(s) == collections.Counter(t)


def solve_group_anagrams(words: List[str]) -> List[List[str]]:
    buckets: Dict[tuple, List[str]] = collections.defaultdict(list)
    for word in words:
        buckets[tuple(sorted(word))].append(word)
    groups = [sorted(group) for group in buckets.values()]
    groups.sort(key=lambda group: (group[0], len(group)))
    return groups


def solve_product_except_self(nums: List[int]) -> List[int]:
    n = len(nums)
    out = [1] * n
    prefix = 1
    for i in range(n):
        out[i] = prefix
        prefix *= nums[i]
    suffix = 1
    for i in range(n - 1, -1, -1):
        out[i] *= suffix
        suffix *= nums[i]
    return out


def solve_top_k_frequent(nums: List[int], k: int) -> List[int]:
    counter = collections.Counter(nums)
    heap: List[tuple[int, int]] = []
    for value, frequency in counter.items():
        entry = (frequency, -value)
        if len(heap) < k:
            heapq.heappush(heap, entry)
        elif entry > heap[0]:
            heapq.heapreplace(heap, entry)
    return [-value for _frequency, value in sorted(heap, key=lambda item: (-item[0], item[1]))]


def solve_longest_consecutive(nums: List[int]) -> int:
    values = set(nums)
    best = 0
    for value in values:
        if value - 1 in values:
            continue
        length = 1
        while value + length in values:
            length += 1
        best = max(best, length)
    return best


def solve_valid_palindrome(s: str) -> bool:
    i, j = 0, len(s) - 1
    while i < j:
        while i < j and not is_alnum(s[i]):
            i += 1
        while i < j and not is_alnum(s[j]):
            j -= 1
        if s[i].lower() != s[j].lower():
            return False
        i += 1
        j -= 1
    return True


def solve_two_sum_ii(numbers: List[int], target: int) -> List[int]:
    left, right = 0, len(numbers) - 1
    while left < right:
        total = numbers[left] + numbers[right]
        if total == target:
            return [left + 1, right + 1]
        if total < target:
            left += 1
        else:
            right -= 1
    return []


def solve_three_sum(nums: List[int]) -> List[List[int]]:
    nums = sorted(nums)
    triplets: List[List[int]] = []
    n = len(nums)
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total == 0:
                triplets.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
            elif total < 0:
                left += 1
            else:
                right -= 1
    triplets.sort()
    return triplets


def solve_container_with_most_water(height: List[int]) -> int:
    left, right = 0, len(height) - 1
    best = 0
    while left < right:
        best = max(best, (right - left) * min(height[left], height[right]))
        if height[left] <= height[right]:
            left += 1
        else:
            right -= 1
    return best


def solve_trapping_rain_water(height: List[int]) -> int:
    left, right = 0, len(height) - 1
    left_max, right_max = 0, 0
    water = 0
    while left <= right:
        if left_max <= right_max:
            left_max = max(left_max, height[left])
            water += left_max - height[left]
            left += 1
        else:
            right_max = max(right_max, height[right])
            water += right_max - height[right]
            right -= 1
    return water


def solve_longest_substring_without_repeat(s: str) -> int:
    window_start = 0
    best = 0
    seen: Dict[str, int] = {}
    for idx, ch in enumerate(s):
        if ch in seen and seen[ch] >= window_start:
            window_start = seen[ch] + 1
        seen[ch] = idx
        best = max(best, idx - window_start + 1)
    return best


def solve_longest_repeating_replacement(s: str, k: int) -> int:
    freq = collections.Counter()
    left = 0
    max_count = 0
    best = 0
    for right, ch in enumerate(s):
        freq[ch] += 1
        max_count = max(max_count, freq[ch])
        while (right - left + 1) - max_count > k:
            freq[s[left]] -= 1
            left += 1
        best = max(best, right - left + 1)
    return best


def solve_permutation_in_string(s1: str, s2: str) -> bool:
    if len(s1) > len(s2):
        return False
    need = collections.Counter(s1)
    window = collections.Counter(s2[: len(s1)])
    if window == need:
        return True
    for idx in range(len(s1), len(s2)):
        window[s2[idx]] += 1
        left_char = s2[idx - len(s1)]
        window[left_char] -= 1
        if window[left_char] == 0:
            del window[left_char]
        if window == need:
            return True
    return False


def solve_minimum_window_substring(s: str, t: str) -> str:
    if not s or not t:
        return ""
    need = collections.Counter(t)
    missing = len(t)
    left = 0
    best_start = 0
    best_len = math.inf
    for right, ch in enumerate(s):
        if need[ch] > 0:
            missing -= 1
        need[ch] -= 1
        while missing == 0:
            if right - left + 1 < best_len:
                best_len = right - left + 1
                best_start = left
            left_char = s[left]
            need[left_char] += 1
            if need[left_char] > 0:
                missing += 1
            left += 1
    if best_len == math.inf:
        return ""
    return s[best_start : best_start + best_len]


def solve_sliding_window_maximum(nums: List[int], k: int) -> List[int]:
    dq: collections.deque[int] = collections.deque()
    out: List[int] = []
    for idx, value in enumerate(nums):
        while dq and dq[0] <= idx - k:
            dq.popleft()
        while dq and nums[dq[-1]] <= value:
            dq.pop()
        dq.append(idx)
        if idx >= k - 1:
            out.append(nums[dq[0]])
    return out


def solve_valid_parentheses(s: str) -> bool:
    close_to_open = {")": "(", "]": "[", "}": "{"}
    stack: List[str] = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in close_to_open:
            if not stack or stack[-1] != close_to_open[ch]:
                return False
            stack.pop()
    return not stack


def solve_min_stack(operations: List[str], values: List[List[int]]) -> List[Any]:
    stack: List[int] = []
    min_stack: List[int] = []
    output: List[Any] = []
    for idx, operation in enumerate(operations):
        payload = values[idx] if idx < len(values) else []
        if operation == "MinStack":
            stack = []
            min_stack = []
            output.append(None)
        elif operation == "push":
            value = payload[0]
            stack.append(value)
            if not min_stack:
                min_stack.append(value)
            else:
                min_stack.append(min(value, min_stack[-1]))
            output.append(None)
        elif operation == "pop":
            if stack:
                stack.pop()
                min_stack.pop()
            output.append(None)
        elif operation == "top":
            output.append(stack[-1] if stack else None)
        elif operation == "getMin":
            output.append(min_stack[-1] if min_stack else None)
        else:
            output.append(None)
    return output


def solve_eval_rpn(tokens: List[str]) -> int:
    stack: List[int] = []
    for token in tokens:
        if token in {"+", "-", "*", "/"}:
            b = stack.pop()
            a = stack.pop()
            if token == "+":
                stack.append(a + b)
            elif token == "-":
                stack.append(a - b)
            elif token == "*":
                stack.append(a * b)
            else:
                stack.append(int(a / b))
        else:
            stack.append(int(token))
    return stack[-1]


def solve_daily_temperatures(temperatures: List[int]) -> List[int]:
    stack: List[int] = []
    out = [0] * len(temperatures)
    for idx, value in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < value:
            prev = stack.pop()
            out[prev] = idx - prev
        stack.append(idx)
    return out


def solve_car_fleet(target: int, position: List[int], speed: List[int]) -> int:
    cars = sorted(zip(position, speed), reverse=True)
    fleets = 0
    last_time = -1.0
    for pos, spd in cars:
        time = (target - pos) / spd
        if time > last_time:
            fleets += 1
            last_time = time
    return fleets


def solve_binary_search(nums: List[int], target: int) -> int:
    left, right = 0, len(nums) - 1
    while left <= right:
        mid = (left + right) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


def solve_search_2d_matrix(matrix: List[List[int]], target: int) -> bool:
    if not matrix or not matrix[0]:
        return False
    rows = len(matrix)
    cols = len(matrix[0])
    left, right = 0, rows * cols - 1
    while left <= right:
        mid = (left + right) // 2
        value = matrix[mid // cols][mid % cols]
        if value == target:
            return True
        if value < target:
            left = mid + 1
        else:
            right = mid - 1
    return False


def solve_koko_eating_bananas(piles: List[int], h: int) -> int:
    left, right = 1, max(piles)
    while left < right:
        speed = (left + right) // 2
        required = sum((pile + speed - 1) // speed for pile in piles)
        if required <= h:
            right = speed
        else:
            left = speed + 1
    return left


SOLVERS: Dict[str, Callable[..., Any]] = {
    "two-sum": solve_two_sum,
    "contains-duplicate": solve_contains_duplicate,
    "valid-anagram": solve_valid_anagram,
    "group-anagrams": solve_group_anagrams,
    "product-of-array-except-self": solve_product_except_self,
    "top-k-frequent-elements": solve_top_k_frequent,
    "longest-consecutive-sequence": solve_longest_consecutive,
    "valid-palindrome": solve_valid_palindrome,
    "two-sum-ii-input-array-is-sorted": solve_two_sum_ii,
    "3sum": solve_three_sum,
    "container-with-most-water": solve_container_with_most_water,
    "trapping-rain-water": solve_trapping_rain_water,
    "longest-substring-without-repeating-characters": solve_longest_substring_without_repeat,
    "longest-repeating-character-replacement": solve_longest_repeating_replacement,
    "permutation-in-string": solve_permutation_in_string,
    "minimum-window-substring": solve_minimum_window_substring,
    "sliding-window-maximum": solve_sliding_window_maximum,
    "valid-parentheses": solve_valid_parentheses,
    "min-stack": solve_min_stack,
    "evaluate-reverse-polish-notation": solve_eval_rpn,
    "daily-temperatures": solve_daily_temperatures,
    "car-fleet": solve_car_fleet,
    "binary-search": solve_binary_search,
    "search-a-2d-matrix": solve_search_2d_matrix,
    "koko-eating-bananas": solve_koko_eating_bananas,
}


@dataclass
class ProblemSpec:
    signature: str
    starter_code: str
    reference_code: str
    time_complexity: str
    space_complexity: str
    task: str
    constraints: List[str]
    hints: List[str]
    common_mistakes: List[str]
    visible_inputs: List[List[Any]]
    hidden_builder: Callable[[random.Random], List[List[Any]]]
    editorial_intuition: str
    editorial_algorithm: str
    company_tags: List[str]
    tags: List[str]


def generate_two_sum_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    while len(out) < 20:
        n = rng.randint(2, 18)
        nums = rng.sample(range(-80, 81), n)
        i, j = sorted(rng.sample(range(n), 2))
        target = nums[i] + nums[j]
        pairs = 0
        seen = {}
        for idx, num in enumerate(nums):
            need = target - num
            if need in seen:
                pairs += 1
            seen[num] = idx
        if pairs == 1:
            out.append([nums, target])
    return out


def generate_contains_duplicate_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(10):
        arr = rng.sample(range(-200, 201), rng.randint(1, 40))
        out.append([arr])
    for _ in range(10):
        arr = rng.sample(range(-200, 201), rng.randint(2, 35))
        arr.append(arr[rng.randrange(len(arr))])
        rng.shuffle(arr)
        out.append([arr])
    return out


def random_word(rng: random.Random, min_len: int = 1, max_len: int = 6) -> str:
    letters = string.ascii_lowercase[:8]
    return "".join(rng.choice(letters) for _ in range(rng.randint(min_len, max_len)))


def generate_valid_anagram_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(10):
        base = random_word(rng, 1, 8)
        chars = list(base)
        rng.shuffle(chars)
        out.append([base, "".join(chars)])
    for _ in range(10):
        base = random_word(rng, 1, 8)
        chars = list(base)
        idx = rng.randrange(len(chars))
        chars[idx] = rng.choice(string.ascii_lowercase)
        out.append([base, "".join(chars)])
    return out


def generate_group_anagrams_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(20):
        words = []
        groups = rng.randint(2, 5)
        for _g in range(groups):
            seed = random_word(rng, 2, 5)
            chars = list(seed)
            for _ in range(rng.randint(1, 3)):
                rng.shuffle(chars)
                words.append("".join(chars))
        words.extend(random_word(rng, 2, 6) for _ in range(rng.randint(0, 3)))
        rng.shuffle(words)
        out.append([words])
    return out


def generate_product_except_self_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(20):
        n = rng.randint(2, 25)
        arr = [rng.randint(-9, 9) for _ in range(n)]
        if all(value == 0 for value in arr):
            arr[0] = 1
        out.append([arr])
    return out


def generate_top_k_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(20):
        n = rng.randint(1, 45)
        arr = [rng.randint(-15, 15) for _ in range(n)]
        k = rng.randint(1, min(8, len(set(arr))))
        out.append([arr, k])
    return out


def generate_longest_consecutive_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(20):
        start = rng.randint(-60, 60)
        run = list(range(start, start + rng.randint(1, 14)))
        noise = rng.sample(range(-120, 121), rng.randint(0, 20))
        arr = run + noise
        rng.shuffle(arr)
        out.append([arr])
    return out


def generate_valid_palindrome_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    symbols = " ,:;'!-_"
    for _ in range(10):
        half = random_word(rng, 1, 6)
        mirrored = half + half[::-1]
        decorated = "".join(ch + rng.choice(symbols) for ch in mirrored)
        out.append([decorated])
    for _ in range(10):
        word = random_word(rng, 3, 10)
        out.append([word + "x"])
    return out


def generate_two_sum_ii_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    while len(out) < 20:
        arr = sorted(rng.sample(range(-120, 121), rng.randint(2, 18)))
        i, j = sorted(rng.sample(range(len(arr)), 2))
        target = arr[i] + arr[j]
        pairs = 0
        left, right = 0, len(arr) - 1
        while left < right:
            total = arr[left] + arr[right]
            if total == target:
                pairs += 1
                left += 1
                right -= 1
            elif total < target:
                left += 1
            else:
                right -= 1
        if pairs == 1:
            out.append([arr, target])
    return out


def generate_three_sum_hidden(rng: random.Random) -> List[List[Any]]:
    return [[[rng.randint(-8, 8) for _ in range(rng.randint(3, 12))]] for _ in range(20)]


def generate_container_hidden(rng: random.Random) -> List[List[Any]]:
    return [[[rng.randint(0, 1000) for _ in range(rng.randint(2, 60))]] for _ in range(20)]


def generate_trapping_hidden(rng: random.Random) -> List[List[Any]]:
    return [[[rng.randint(0, 12) for _ in range(rng.randint(1, 80))]] for _ in range(20)]


def generate_longest_substring_hidden(rng: random.Random) -> List[List[Any]]:
    letters = string.ascii_lowercase[:10]
    return [["".join(rng.choice(letters) for _ in range(rng.randint(0, 60)))] for _ in range(20)]


def generate_longest_repeating_hidden(rng: random.Random) -> List[List[Any]]:
    letters = "ABCD"
    out = []
    for _ in range(20):
        s = "".join(rng.choice(letters) for _ in range(rng.randint(1, 70)))
        k = rng.randint(0, 8)
        out.append([s, k])
    return out


def generate_permutation_hidden(rng: random.Random) -> List[List[Any]]:
    letters = string.ascii_lowercase[:6]
    out = []
    for _ in range(20):
        n1 = rng.randint(1, 5)
        n2 = rng.randint(n1, 20)
        s1 = "".join(rng.choice(letters) for _ in range(n1))
        s2 = "".join(rng.choice(letters) for _ in range(n2))
        if rng.random() < 0.5:
            idx = rng.randint(0, max(0, n2 - n1))
            perm = list(s1)
            rng.shuffle(perm)
            s2 = s2[:idx] + "".join(perm) + s2[idx + n1 :]
        out.append([s1, s2])
    return out


def generate_min_window_hidden(rng: random.Random) -> List[List[Any]]:
    letters = "abcde"
    out = []
    for _ in range(20):
        t_len = rng.randint(1, 4)
        t = "".join(rng.choice(letters) for _ in range(t_len))
        s_len = rng.randint(t_len, 28)
        s = "".join(rng.choice(letters) for _ in range(s_len))
        if rng.random() < 0.7:
            idx = rng.randint(0, s_len - t_len)
            s = s[:idx] + t + s[idx + t_len :]
        out.append([s, t])
    return out


def generate_sliding_window_max_hidden(rng: random.Random) -> List[List[Any]]:
    out = []
    for _ in range(20):
        nums = [rng.randint(-20, 20) for _ in range(rng.randint(1, 50))]
        k = rng.randint(1, len(nums))
        out.append([nums, k])
    return out


def generate_valid_parentheses_hidden(rng: random.Random) -> List[List[Any]]:
    valid_samples = ["()", "()[]{}", "{[]}", "([{}])", "(((())))", ""]
    invalid_samples = ["(]", "([)]", "(", "}", "(()", "())", "{[}]"]
    out = []
    for _ in range(10):
        out.append([rng.choice(valid_samples)])
    for _ in range(10):
        out.append([rng.choice(invalid_samples)])
    return out


def generate_min_stack_hidden(rng: random.Random) -> List[List[Any]]:
    out: List[List[Any]] = []
    for _ in range(20):
        operations = ["MinStack"]
        values: List[List[int]] = [[]]
        size = 0
        for _step in range(rng.randint(8, 24)):
            if size == 0:
                op = "push"
            else:
                op = rng.choice(["push", "pop", "top", "getMin"])
            if op == "push":
                value = rng.randint(-40, 40)
                operations.append("push")
                values.append([value])
                size += 1
            elif op == "pop":
                operations.append("pop")
                values.append([])
                size -= 1
            elif op == "top":
                operations.append("top")
                values.append([])
            else:
                operations.append("getMin")
                values.append([])
        out.append([operations, values])
    return out


def generate_eval_rpn_hidden(_rng: random.Random) -> List[List[Any]]:
    expressions = [
        ["2", "1", "+", "3", "*"],
        ["4", "13", "5", "/", "+"],
        ["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"],
        ["3", "-4", "+"],
        ["5", "1", "2", "+", "4", "*", "+", "3", "-"],
        ["7", "2", "/"],
        ["8", "3", "-", "2", "*"],
        ["15", "7", "1", "1", "+", "-", "/", "3", "*", "2", "1", "1", "+", "+", "-"],
        ["12", "3", "/"],
        ["2", "3", "4", "*", "+"],
        ["9", "3", "/"],
        ["-6", "2", "/"],
        ["1", "2", "+", "7", "*"],
        ["20", "3", "-", "2", "/"],
        ["6", "2", "3", "+", "*"],
        ["14", "5", "/"],
        ["2", "2", "+"],
        ["3", "5", "+", "7", "-"],
        ["10", "2", "8", "*", "+", "3", "-"],
        ["4", "2", "+", "3", "/"],
    ]
    return [[tokens] for tokens in expressions]


def generate_daily_temperatures_hidden(rng: random.Random) -> List[List[Any]]:
    return [[[rng.randint(30, 100) for _ in range(rng.randint(1, 80))]] for _ in range(20)]


def generate_car_fleet_hidden(rng: random.Random) -> List[List[Any]]:
    out = []
    for _ in range(20):
        n = rng.randint(1, 20)
        target = rng.randint(10, 200)
        positions = rng.sample(range(0, target), n)
        speeds = [rng.randint(1, 10) for _ in range(n)]
        out.append([target, positions, speeds])
    return out


def generate_binary_search_hidden(rng: random.Random) -> List[List[Any]]:
    out = []
    for _ in range(20):
        arr = sorted(rng.sample(range(-200, 201), rng.randint(1, 60)))
        if rng.random() < 0.6:
            target = rng.choice(arr)
        else:
            target = rng.randint(-250, 250)
            while target in arr:
                target += 1
        out.append([arr, target])
    return out


def generate_search_2d_hidden(rng: random.Random) -> List[List[Any]]:
    out = []
    for _ in range(20):
        rows = rng.randint(1, 6)
        cols = rng.randint(1, 6)
        start = rng.randint(-50, 20)
        values = [start]
        for _i in range(rows * cols - 1):
            values.append(values[-1] + rng.randint(1, 4))
        matrix = [values[i * cols : (i + 1) * cols] for i in range(rows)]
        if rng.random() < 0.6:
            target = rng.choice(values)
        else:
            target = values[-1] + rng.randint(1, 5)
        out.append([matrix, target])
    return out


def generate_koko_hidden(rng: random.Random) -> List[List[Any]]:
    out = []
    for _ in range(20):
        n = rng.randint(1, 30)
        piles = [rng.randint(1, 10_000) for _ in range(n)]
        h = rng.randint(n, n * 20)
        out.append([piles, h])
    return out


PROBLEM_SPECS: Dict[str, ProblemSpec] = {
    "two-sum": ProblemSpec(
        signature="def solve(nums: list[int], target: int) -> list[int]:",
        starter_code="def solve(nums, target):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            def solve(nums, target):
                seen = {}
                for i, num in enumerate(nums):
                    need = target - num
                    if need in seen:
                        return [seen[need], i]
                    seen[num] = i
                return []
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(n)",
        task="Given an integer array and target sum, return indices of the unique pair that adds to target.",
        constraints=[
            "2 <= len(nums) <= 10^5",
            "-10^9 <= nums[i], target <= 10^9",
            "Exactly one valid pair exists in each judge test.",
            "Return indices in ascending order [i, j] with i < j.",
        ],
        hints=[
            "Store values already seen with their index.",
            "For each number x, check whether target - x was seen earlier.",
            "Insert current value only after checking complement to avoid reusing the same index.",
        ],
        common_mistakes=[
            "Overwriting index for duplicate values before checking complement.",
            "Returning values instead of indices.",
            "Using O(n^2) scan and timing out on large input.",
        ],
        visible_inputs=[
            [[2, 7, 11, 15], 9],
            [[3, 2, 4], 6],
            [[-1, -2, -3, -4, -5], -8],
            [[0, 4, 3, 0], 0],
            [[1, 5], 6],
            [[10, -2, 8, 7], 5],
        ],
        hidden_builder=generate_two_sum_hidden,
        editorial_intuition="A complement table lets each element answer the question: did we already see the number needed to complete target?",
        editorial_algorithm="Iterate once, keep `seen[value] = index`, and return when complement exists.",
        company_tags=["google", "amazon", "microsoft"],
        tags=["array", "hash-map", "complement-lookup"],
    ),
    "contains-duplicate": ProblemSpec(
        signature="def solve(nums: list[int]) -> bool:",
        starter_code="def solve(nums):\n    return False\n",
        reference_code="def solve(nums):\n    return len(nums) != len(set(nums))\n",
        time_complexity="O(n)",
        space_complexity="O(n)",
        task="Return True when at least one value appears more than once in the array.",
        constraints=[
            "1 <= len(nums) <= 10^5",
            "-10^9 <= nums[i] <= 10^9",
        ],
        hints=[
            "Track unique values with a set.",
            "A duplicate exists if insertion would repeat an existing value.",
            "Compare original length with set length for a concise check.",
        ],
        common_mistakes=[
            "Sorting first and increasing complexity to O(n log n) unnecessarily.",
            "Returning False too early after checking only part of the array.",
            "Using list membership checks leading to O(n^2).",
        ],
        visible_inputs=[
            [[1, 2, 3, 1]],
            [[1, 2, 3, 4]],
            [[1, 1, 1, 3, 3, 4, 3, 2, 4, 2]],
            [[42]],
            [[-1, -2, -3, -1]],
            [[0, 1, 2, 3, 4, 5]],
        ],
        hidden_builder=generate_contains_duplicate_hidden,
        editorial_intuition="The problem asks whether uniqueness is violated, which is exactly what a set models.",
        editorial_algorithm="Insert each value into a set or compare set size with array size.",
        company_tags=["google", "meta", "amazon"],
        tags=["array", "set", "membership-test"],
    ),
    "valid-anagram": ProblemSpec(
        signature="def solve(s: str, t: str) -> bool:",
        starter_code="def solve(s, t):\n    return False\n",
        reference_code=textwrap.dedent(
            """
            from collections import Counter

            def solve(s, t):
                return Counter(s) == Counter(t)
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Return True if t is an anagram of s using lowercase English letters.",
        constraints=[
            "1 <= len(s), len(t) <= 10^5",
            "s and t contain only lowercase English letters.",
        ],
        hints=[
            "Anagrams must have identical character frequencies.",
            "Early reject when lengths differ.",
            "A 26-size frequency table or Counter works in linear time.",
        ],
        common_mistakes=[
            "Sorting both strings and paying O(n log n) when O(n) is enough.",
            "Ignoring length mismatch and still counting.",
            "Handling only presence, not frequency.",
        ],
        visible_inputs=[
            ["anagram", "nagaram"],
            ["rat", "car"],
            ["aacc", "ccac"],
            ["listen", "silent"],
            ["x", "x"],
            ["abc", "ab"],
        ],
        hidden_builder=generate_valid_anagram_hidden,
        editorial_intuition="Two words are anagrams only when each character count matches exactly.",
        editorial_algorithm="Count each character in both strings and compare frequency maps.",
        company_tags=["amazon", "microsoft", "adobe"],
        tags=["string", "counting", "frequency-map"],
    ),
    "group-anagrams": ProblemSpec(
        signature="def solve(words: list[str]) -> list[list[str]]:",
        starter_code="def solve(words):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            from collections import defaultdict

            def solve(words):
                buckets = defaultdict(list)
                for word in words:
                    key = tuple(sorted(word))
                    buckets[key].append(word)
                groups = [sorted(group) for group in buckets.values()]
                groups.sort(key=lambda group: (group[0], len(group)))
                return groups
            """
        ).strip()
        + "\n",
        time_complexity="O(n * k log k)",
        space_complexity="O(n * k)",
        task="Group words that are anagrams. Output must be deterministic: sort words in each group, then sort groups by first word.",
        constraints=[
            "1 <= len(words) <= 10^4",
            "0 <= len(words[i]) <= 100",
            "words[i] contains lowercase English letters.",
        ],
        hints=[
            "An anagram group shares the same sorted-character signature.",
            "Use a dictionary from signature to list of words.",
            "Apply deterministic sorting before returning.",
        ],
        common_mistakes=[
            "Using mutable list as dictionary key.",
            "Returning non-deterministic group order causing flaky checks.",
            "Forgetting to sort words inside groups.",
        ],
        visible_inputs=[
            [["eat", "tea", "tan", "ate", "nat", "bat"]],
            [[""]],
            [["a"]],
            [["abc", "bca", "cab", "xyz", "zyx"]],
            [["ab", "ba", "abc", "cba", "bac"]],
            [["aa", "aa", "bb"]],
        ],
        hidden_builder=generate_group_anagrams_hidden,
        editorial_intuition="Anagram grouping is hashing by canonical form.",
        editorial_algorithm="Map sorted-character key to words, then sort each bucket and the bucket list.",
        company_tags=["google", "amazon", "meta"],
        tags=["hashing", "grouping", "string"],
    ),
    "product-of-array-except-self": ProblemSpec(
        signature="def solve(nums: list[int]) -> list[int]:",
        starter_code="def solve(nums):\n    return [0] * len(nums)\n",
        reference_code=textwrap.dedent(
            """
            def solve(nums):
                n = len(nums)
                out = [1] * n
                prefix = 1
                for i in range(n):
                    out[i] = prefix
                    prefix *= nums[i]
                suffix = 1
                for i in range(n - 1, -1, -1):
                    out[i] *= suffix
                    suffix *= nums[i]
                return out
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1) extra (excluding output)",
        task="Return an array where each position i contains product of all nums[j] for j != i, without division.",
        constraints=[
            "2 <= len(nums) <= 10^5",
            "-30 <= nums[i] <= 30",
            "The product of any prefix/suffix fits in 32-bit signed integer.",
        ],
        hints=[
            "Split contribution into left product and right product.",
            "First pass writes prefix products.",
            "Second pass multiplies running suffix into output.",
        ],
        common_mistakes=[
            "Using division which fails with zeros and violates requirements.",
            "Allocating full prefix and suffix arrays unnecessarily.",
            "Forgetting to reset suffix accumulator for second pass.",
        ],
        visible_inputs=[
            [[1, 2, 3, 4]],
            [[-1, 1, 0, -3, 3]],
            [[2, 3]],
            [[0, 4, 0]],
            [[5, -2, 1]],
            [[10, 10, 10, 10]],
        ],
        hidden_builder=generate_product_except_self_hidden,
        editorial_intuition="Each position result is independent product of everything left and right.",
        editorial_algorithm="Compose output in two sweeps: prefix then suffix multiplication.",
        company_tags=["amazon", "meta", "google"],
        tags=["array", "prefix-suffix", "no-division"],
    ),
    "top-k-frequent-elements": ProblemSpec(
        signature="def solve(nums: list[int], k: int) -> list[int]:",
        starter_code="def solve(nums, k):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            from collections import Counter
            import heapq

            def solve(nums, k):
                counter = Counter(nums)
                heap = []
                for value, frequency in counter.items():
                    entry = (frequency, -value)
                    if len(heap) < k:
                        heapq.heappush(heap, entry)
                    elif entry > heap[0]:
                        heapq.heapreplace(heap, entry)
                return [-value for _frequency, value in sorted(heap, key=lambda item: (-item[0], item[1]))]
            """
        ).strip()
        + "\n",
        time_complexity="O(n log k)",
        space_complexity="O(n)",
        task="Return k most frequent numbers. Tie-break by smaller numeric value first for deterministic output.",
        constraints=[
            "1 <= len(nums) <= 10^5",
            "1 <= k <= number of distinct values",
            "-10^4 <= nums[i] <= 10^4",
        ],
        hints=[
            "Frequency table first, selection second.",
            "A min-heap of size k avoids sorting all distinct values.",
            "Counter greatly simplifies counting logic.",
        ],
        common_mistakes=[
            "Ignoring tie-break and returning unstable order.",
            "Sorting raw array instead of frequency map.",
            "Choosing k larger than distinct count without validation.",
        ],
        visible_inputs=[
            [[1, 1, 1, 2, 2, 3], 2],
            [[1], 1],
            [[4, 4, 4, 6, 6, 7, 7], 2],
            [[-1, -1, -2, -2, -2, 3], 2],
            [[5, 5, 4, 4, 3, 3], 3],
            [[9, 8, 7, 7, 8, 8], 1],
        ],
        hidden_builder=generate_top_k_hidden,
        editorial_intuition="Frequency ranking turns raw values into sortable score pairs.",
        editorial_algorithm="Count occurrences, keep only top-k in a min-heap, then output in deterministic rank order.",
        company_tags=["google", "amazon", "meta"],
        tags=["hash-map", "sorting", "top-k"],
    ),
    "longest-consecutive-sequence": ProblemSpec(
        signature="def solve(nums: list[int]) -> int:",
        starter_code="def solve(nums):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(nums):
                values = set(nums)
                best = 0
                for value in values:
                    if value - 1 in values:
                        continue
                    length = 1
                    while value + length in values:
                        length += 1
                    best = max(best, length)
                return best
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(n)",
        task="Return length of the longest run of consecutive integers, regardless of original order.",
        constraints=[
            "0 <= len(nums) <= 10^5",
            "-10^9 <= nums[i] <= 10^9",
        ],
        hints=[
            "Use set membership for O(1) average lookups.",
            "Start streak counting only from numbers without predecessor.",
            "Each number is extended once across all streaks.",
        ],
        common_mistakes=[
            "Sorting first and paying O(n log n).",
            "Restarting count from every number, causing O(n^2).",
            "Not handling empty list correctly.",
        ],
        visible_inputs=[
            [[100, 4, 200, 1, 3, 2]],
            [[0, 3, 7, 2, 5, 8, 4, 6, 0, 1]],
            [[]],
            [[1, 2, 0, 1]],
            [[9]],
            [[-2, -3, -1, 5, 6, 7]],
        ],
        hidden_builder=generate_longest_consecutive_hidden,
        editorial_intuition="Consecutive runs can be found by detecting run starts, not by sorting.",
        editorial_algorithm="For each value lacking predecessor, count forward run length in set.",
        company_tags=["google", "microsoft", "amazon"],
        tags=["set", "sequence", "hashing"],
    ),
    "valid-palindrome": ProblemSpec(
        signature="def solve(s: str) -> bool:",
        starter_code="def solve(s):\n    return False\n",
        reference_code=textwrap.dedent(
            """
            def solve(s):
                i, j = 0, len(s) - 1
                while i < j:
                    while i < j and not s[i].isalnum():
                        i += 1
                    while i < j and not s[j].isalnum():
                        j -= 1
                    if s[i].lower() != s[j].lower():
                        return False
                    i += 1
                    j -= 1
                return True
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Check whether string is palindrome after removing non-alphanumeric chars and ignoring case.",
        constraints=[
            "0 <= len(s) <= 2 * 10^5",
            "s may contain letters, digits, and punctuation.",
        ],
        hints=[
            "Use two pointers from both ends.",
            "Skip characters that are not alphanumeric.",
            "Compare lowercase forms only.",
        ],
        common_mistakes=[
            "Building a new filtered string and using extra memory.",
            "Forgetting case normalization.",
            "Not handling empty string correctly.",
        ],
        visible_inputs=[
            ["A man, a plan, a canal: Panama"],
            ["race a car"],
            [" "],
            ["0P"],
            ["No lemon, no melon"],
            ["ab_a"],
        ],
        hidden_builder=generate_valid_palindrome_hidden,
        editorial_intuition="The cleaned palindrome property can be checked in-place with two pointers.",
        editorial_algorithm="Skip invalid chars and compare lowercase endpoints until pointers cross.",
        company_tags=["facebook", "google", "amazon"],
        tags=["two-pointers", "string", "normalization"],
    ),
    "two-sum-ii-input-array-is-sorted": ProblemSpec(
        signature="def solve(numbers: list[int], target: int) -> list[int]:",
        starter_code="def solve(numbers, target):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            def solve(numbers, target):
                left, right = 0, len(numbers) - 1
                while left < right:
                    total = numbers[left] + numbers[right]
                    if total == target:
                        return [left + 1, right + 1]
                    if total < target:
                        left += 1
                    else:
                        right -= 1
                return []
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Array is sorted ascending. Return 1-indexed positions of the unique pair summing to target.",
        constraints=[
            "2 <= len(numbers) <= 10^5",
            "-10^9 <= numbers[i], target <= 10^9",
            "Exactly one solution exists.",
            "Return [i, j] with 1 <= i < j <= n.",
        ],
        hints=[
            "Sorted order enables two-pointer scan.",
            "If sum too small, move left pointer right.",
            "If sum too large, move right pointer left.",
        ],
        common_mistakes=[
            "Returning 0-indexed indices.",
            "Using hash map despite sorted input.",
            "Moving wrong pointer and missing solution.",
        ],
        visible_inputs=[
            [[2, 7, 11, 15], 9],
            [[2, 3, 4], 6],
            [[-1, 0], -1],
            [[1, 2, 3, 4, 4, 9, 56, 90], 8],
            [[-5, -3, -1, 2, 9], 6],
            [[1, 5], 6],
        ],
        hidden_builder=generate_two_sum_ii_hidden,
        editorial_intuition="Monotonic order lets us shrink search range greedily.",
        editorial_algorithm="Use two pointers at ends and close in based on current sum.",
        company_tags=["amazon", "adobe", "microsoft"],
        tags=["two-pointers", "sorted-array", "pair-sum"],
    ),
    "3sum": ProblemSpec(
        signature="def solve(nums: list[int]) -> list[list[int]]:",
        starter_code="def solve(nums):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            def solve(nums):
                nums = sorted(nums)
                triplets = []
                n = len(nums)
                for i in range(n - 2):
                    if i > 0 and nums[i] == nums[i - 1]:
                        continue
                    left, right = i + 1, n - 1
                    while left < right:
                        total = nums[i] + nums[left] + nums[right]
                        if total == 0:
                            triplets.append([nums[i], nums[left], nums[right]])
                            left += 1
                            right -= 1
                            while left < right and nums[left] == nums[left - 1]:
                                left += 1
                            while left < right and nums[right] == nums[right + 1]:
                                right -= 1
                        elif total < 0:
                            left += 1
                        else:
                            right -= 1
                triplets.sort()
                return triplets
            """
        ).strip()
        + "\n",
        time_complexity="O(n^2)",
        space_complexity="O(1) extra",
        task="Return all unique triplets [a,b,c] with a+b+c=0. Each triplet and final list must be sorted lexicographically.",
        constraints=[
            "0 <= len(nums) <= 3000",
            "-10^5 <= nums[i] <= 10^5",
        ],
        hints=[
            "Sort once to control duplicates and enable two pointers.",
            "Fix one index and solve two-sum on remaining suffix.",
            "Skip repeated values at fixed and moving pointers.",
        ],
        common_mistakes=[
            "Returning duplicate triplets.",
            "Not sorting output deterministically.",
            "Using O(n^3) brute force.",
        ],
        visible_inputs=[
            [[-1, 0, 1, 2, -1, -4]],
            [[0, 1, 1]],
            [[0, 0, 0]],
            [[-2, 0, 1, 1, 2]],
            [[-4, -2, -2, 0, 1, 2, 2, 4]],
            [[1, 2, -2, -1]],
        ],
        hidden_builder=generate_three_sum_hidden,
        editorial_intuition="After sorting, each fixed value reduces task to 2-sum with duplicate control.",
        editorial_algorithm="For each pivot, run bidirectional search and skip repeated neighbors.",
        company_tags=["facebook", "amazon", "microsoft"],
        tags=["two-pointers", "sorting", "dedup"],
    ),
    "container-with-most-water": ProblemSpec(
        signature="def solve(height: list[int]) -> int:",
        starter_code="def solve(height):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(height):
                left, right = 0, len(height) - 1
                best = 0
                while left < right:
                    best = max(best, (right - left) * min(height[left], height[right]))
                    if height[left] <= height[right]:
                        left += 1
                    else:
                        right -= 1
                return best
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Find the largest area formed by two vertical lines and the x-axis.",
        constraints=[
            "2 <= len(height) <= 10^5",
            "0 <= height[i] <= 10^4",
        ],
        hints=[
            "Area depends on shorter wall and distance.",
            "Move pointer at shorter wall to seek larger minimum height.",
            "Each pair is considered at most once.",
        ],
        common_mistakes=[
            "Moving taller pointer, which cannot improve area for current width.",
            "Checking all O(n^2) pairs.",
            "Overflow concerns when width*height is large in other languages.",
        ],
        visible_inputs=[
            [[1, 8, 6, 2, 5, 4, 8, 3, 7]],
            [[1, 1]],
            [[4, 3, 2, 1, 4]],
            [[1, 2, 1]],
            [[2, 3, 10, 5, 7, 8, 9]],
            [[0, 2, 0, 4, 0]],
        ],
        hidden_builder=generate_container_hidden,
        editorial_intuition="The width shrinks each move, so only a higher limiting wall can improve area.",
        editorial_algorithm="Two pointers converge, always moving the smaller-height side.",
        company_tags=["amazon", "google", "meta"],
        tags=["two-pointers", "greedy", "geometry"],
    ),
    "trapping-rain-water": ProblemSpec(
        signature="def solve(height: list[int]) -> int:",
        starter_code="def solve(height):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(height):
                left, right = 0, len(height) - 1
                left_max, right_max = 0, 0
                water = 0
                while left <= right:
                    if left_max <= right_max:
                        left_max = max(left_max, height[left])
                        water += left_max - height[left]
                        left += 1
                    else:
                        right_max = max(right_max, height[right])
                        water += right_max - height[right]
                        right -= 1
                return water
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Given bar heights, compute total trapped rainwater after rainfall.",
        constraints=[
            "1 <= len(height) <= 2 * 10^5",
            "0 <= height[i] <= 10^5",
        ],
        hints=[
            "Water above index is bounded by min(max_left, max_right).",
            "Track running max from both ends.",
            "Advance side with smaller max because it determines bound now.",
        ],
        common_mistakes=[
            "Using local neighbors instead of global left/right maxima.",
            "Subtracting in wrong order and producing negative water.",
            "Forgetting zero-height boundaries.",
        ],
        visible_inputs=[
            [[0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]],
            [[4, 2, 0, 3, 2, 5]],
            [[1, 2, 3, 4, 5]],
            [[5, 4, 1, 2]],
            [[2, 0, 2]],
            [[3]],
        ],
        hidden_builder=generate_trapping_hidden,
        editorial_intuition="Each bar can trap water only up to the shorter boundary seen from both sides.",
        editorial_algorithm="Use two-pointer sweep with left/right maxima accumulators.",
        company_tags=["amazon", "google", "microsoft"],
        tags=["two-pointers", "prefix-suffix", "water-trapping"],
    ),
    "longest-substring-without-repeating-characters": ProblemSpec(
        signature="def solve(s: str) -> int:",
        starter_code="def solve(s):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(s):
                start = 0
                best = 0
                seen = {}
                for i, ch in enumerate(s):
                    if ch in seen and seen[ch] >= start:
                        start = seen[ch] + 1
                    seen[ch] = i
                    best = max(best, i - start + 1)
                return best
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(min(n, alphabet))",
        task="Return the length of longest substring containing no repeated characters.",
        constraints=[
            "0 <= len(s) <= 5 * 10^4",
            "s may include letters, digits, symbols, and spaces.",
        ],
        hints=[
            "Maintain a sliding window of unique characters.",
            "Track last seen index per character.",
            "When duplicate enters window, move left boundary past old index.",
        ],
        common_mistakes=[
            "Resetting window completely on duplicate instead of sliding.",
            "Not guarding against old duplicate indices before current window start.",
            "Quadratic substring checks.",
        ],
        visible_inputs=[
            ["abcabcbb"],
            ["bbbbb"],
            ["pwwkew"],
            [""],
            ["dvdf"],
            ["anviaj"],
        ],
        hidden_builder=generate_longest_substring_hidden,
        editorial_intuition="Valid window invariant: all chars appear once.",
        editorial_algorithm="Expand right pointer, shift left pointer when duplicate violates invariant.",
        company_tags=["amazon", "google", "meta"],
        tags=["sliding-window", "hash-map", "string"],
    ),
    "longest-repeating-character-replacement": ProblemSpec(
        signature="def solve(s: str, k: int) -> int:",
        starter_code="def solve(s, k):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            from collections import Counter

            def solve(s, k):
                freq = Counter()
                left = 0
                max_count = 0
                best = 0
                for right, ch in enumerate(s):
                    freq[ch] += 1
                    max_count = max(max_count, freq[ch])
                    while (right - left + 1) - max_count > k:
                        freq[s[left]] -= 1
                        left += 1
                    best = max(best, right - left + 1)
                return best
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Return max window length that can be made of one repeated letter after at most k replacements.",
        constraints=[
            "1 <= len(s) <= 10^5",
            "s contains uppercase English letters.",
            "0 <= k <= len(s)",
        ],
        hints=[
            "Window is valid when replacements needed <= k.",
            "Needed replacements = window_length - max_freq_in_window.",
            "Keep expanding and shrink only when invalid.",
        ],
        common_mistakes=[
            "Recomputing max frequency by scanning map every step.",
            "Shrinking too aggressively and losing best window.",
            "Confusing distinct count with replacement count.",
        ],
        visible_inputs=[
            ["ABAB", 2],
            ["AABABBA", 1],
            ["AAAA", 2],
            ["ABCDE", 1],
            ["BAAAB", 2],
            ["ABBB", 2],
        ],
        hidden_builder=generate_longest_repeating_hidden,
        editorial_intuition="Only the dominant character matters for replacement budget.",
        editorial_algorithm="Sliding window with tracked highest frequency in current window.",
        company_tags=["amazon", "microsoft", "google"],
        tags=["sliding-window", "frequency", "greedy-window"],
    ),
    "permutation-in-string": ProblemSpec(
        signature="def solve(s1: str, s2: str) -> bool:",
        starter_code="def solve(s1, s2):\n    return False\n",
        reference_code=textwrap.dedent(
            """
            from collections import Counter

            def solve(s1, s2):
                if len(s1) > len(s2):
                    return False
                need = Counter(s1)
                window = Counter(s2[:len(s1)])
                if window == need:
                    return True
                for i in range(len(s1), len(s2)):
                    window[s2[i]] += 1
                    left_char = s2[i - len(s1)]
                    window[left_char] -= 1
                    if window[left_char] == 0:
                        del window[left_char]
                    if window == need:
                        return True
                return False
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(1)",
        task="Check whether any permutation of s1 appears as a contiguous substring in s2.",
        constraints=[
            "1 <= len(s1), len(s2) <= 10^4",
            "Strings contain lowercase English letters.",
        ],
        hints=[
            "Window length is fixed at len(s1).",
            "Compare character counts of current window with target counts.",
            "Update counts incrementally when sliding by one character.",
        ],
        common_mistakes=[
            "Resorting each window repeatedly.",
            "Forgetting to remove zero-count keys before map comparison.",
            "Using variable-length window for fixed-length check.",
        ],
        visible_inputs=[
            ["ab", "eidbaooo"],
            ["ab", "eidboaoo"],
            ["adc", "dcda"],
            ["a", "a"],
            ["hello", "ooolleoooleh"],
            ["xyz", "afdgzyxksldfm"],
        ],
        hidden_builder=generate_permutation_hidden,
        editorial_intuition="Permutation match is frequency equality over a fixed-size window.",
        editorial_algorithm="Maintain sliding counter of size len(s1) and compare with target counter.",
        company_tags=["facebook", "amazon", "google"],
        tags=["sliding-window", "anagram-window", "frequency-map"],
    ),
    "minimum-window-substring": ProblemSpec(
        signature="def solve(s: str, t: str) -> str:",
        starter_code="def solve(s, t):\n    return \"\"\n",
        reference_code=textwrap.dedent(
            """
            from collections import Counter

            def solve(s, t):
                if not s or not t:
                    return ""
                need = Counter(t)
                missing = len(t)
                left = 0
                best_start = 0
                best_len = float("inf")
                for right, ch in enumerate(s):
                    if need[ch] > 0:
                        missing -= 1
                    need[ch] -= 1
                    while missing == 0:
                        if right - left + 1 < best_len:
                            best_len = right - left + 1
                            best_start = left
                        left_char = s[left]
                        need[left_char] += 1
                        if need[left_char] > 0:
                            missing += 1
                        left += 1
                if best_len == float("inf"):
                    return ""
                return s[best_start:best_start + best_len]
            """
        ).strip()
        + "\n",
        time_complexity="O(|s| + |t|)",
        space_complexity="O(1)",
        task="Return the smallest substring of s containing all characters of t with multiplicity. Return empty string if impossible.",
        constraints=[
            "1 <= len(s), len(t) <= 10^5",
            "s and t contain English letters.",
        ],
        hints=[
            "Track unmet required characters while expanding right pointer.",
            "Once valid, shrink left boundary to make window minimal.",
            "Store best valid window seen so far.",
        ],
        common_mistakes=[
            "Treating t as a set instead of multiset.",
            "Not shrinking enough after window becomes valid.",
            "Returning first valid window instead of smallest.",
        ],
        visible_inputs=[
            ["ADOBECODEBANC", "ABC"],
            ["a", "a"],
            ["a", "aa"],
            ["ab", "b"],
            ["aa", "aa"],
            ["thisisateststring", "tist"],
        ],
        hidden_builder=generate_min_window_hidden,
        editorial_intuition="The minimal valid interval emerges from expand-then-contract window control.",
        editorial_algorithm="Counter-based requirement tracking with greedy left shrink on validity.",
        company_tags=["google", "amazon", "microsoft"],
        tags=["sliding-window", "minimum-cover", "two-pointers"],
    ),
    "sliding-window-maximum": ProblemSpec(
        signature="def solve(nums: list[int], k: int) -> list[int]:",
        starter_code="def solve(nums, k):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            from collections import deque

            def solve(nums, k):
                dq = deque()
                out = []
                for i, value in enumerate(nums):
                    while dq and dq[0] <= i - k:
                        dq.popleft()
                    while dq and nums[dq[-1]] <= value:
                        dq.pop()
                    dq.append(i)
                    if i >= k - 1:
                        out.append(nums[dq[0]])
                return out
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(k)",
        task="For each window of size k, return the maximum value.",
        constraints=[
            "1 <= len(nums) <= 10^5",
            "1 <= k <= len(nums)",
            "-10^4 <= nums[i] <= 10^4",
        ],
        hints=[
            "Deque stores candidate indices in decreasing value order.",
            "Remove indices that leave window from front.",
            "Pop smaller trailing values because new value dominates them.",
        ],
        common_mistakes=[
            "Storing values instead of indices and losing window-expiry logic.",
            "Using heap without lazy deletion handling.",
            "Recomputing max each window with O(nk).",
        ],
        visible_inputs=[
            [[1, 3, -1, -3, 5, 3, 6, 7], 3],
            [[1], 1],
            [[9, 8, 7, 6, 5], 2],
            [[4, 4, 4, 4], 2],
            [[7, 2, 4], 2],
            [[-1, -3, -5, -2], 2],
        ],
        hidden_builder=generate_sliding_window_max_hidden,
        editorial_intuition="A monotonic deque keeps the current window max at the front.",
        editorial_algorithm="Maintain decreasing deque of indices while sliding across array once.",
        company_tags=["amazon", "google", "meta"],
        tags=["deque", "monotonic-queue", "sliding-window"],
    ),
    "valid-parentheses": ProblemSpec(
        signature="def solve(s: str) -> bool:",
        starter_code="def solve(s):\n    return False\n",
        reference_code=textwrap.dedent(
            """
            def solve(s):
                close_to_open = {')': '(', ']': '[', '}': '{'}
                stack = []
                for ch in s:
                    if ch in '([{':
                        stack.append(ch)
                    elif ch in close_to_open:
                        if not stack or stack[-1] != close_to_open[ch]:
                            return False
                        stack.pop()
                return not stack
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(n)",
        task="Return True when every bracket is correctly opened and closed in proper order.",
        constraints=[
            "0 <= len(s) <= 10^5",
            "s consists only of characters ()[]{}.",
        ],
        hints=[
            "Use stack for unmatched opening brackets.",
            "On closing bracket, top of stack must be matching opener.",
            "Valid expression ends with empty stack.",
        ],
        common_mistakes=[
            "Comparing closing symbols directly instead of opener mapping.",
            "Forgetting to reject leftover open brackets.",
            "Ignoring unexpected closing symbol on empty stack.",
        ],
        visible_inputs=[
            ["()"],
            ["()[]{}"],
            ["(]"],
            ["([)]"],
            ["{[]}"],
            [""],
        ],
        hidden_builder=generate_valid_parentheses_hidden,
        editorial_intuition="Nesting rules naturally map to LIFO behavior.",
        editorial_algorithm="Push openers, match and pop on closers, validate empty residue.",
        company_tags=["amazon", "google", "microsoft"],
        tags=["stack", "matching", "parsing"],
    ),
    "min-stack": ProblemSpec(
        signature="def solve(operations: list[str], values: list[list[int]]) -> list[object]:",
        starter_code="def solve(operations, values):\n    return []\n",
        reference_code=textwrap.dedent(
            """
            def solve(operations, values):
                stack = []
                min_stack = []
                output = []
                for i, op in enumerate(operations):
                    payload = values[i] if i < len(values) else []
                    if op == "MinStack":
                        stack = []
                        min_stack = []
                        output.append(None)
                    elif op == "push":
                        x = payload[0]
                        stack.append(x)
                        if not min_stack:
                            min_stack.append(x)
                        else:
                            min_stack.append(min(x, min_stack[-1]))
                        output.append(None)
                    elif op == "pop":
                        if stack:
                            stack.pop()
                            min_stack.pop()
                        output.append(None)
                    elif op == "top":
                        output.append(stack[-1] if stack else None)
                    elif op == "getMin":
                        output.append(min_stack[-1] if min_stack else None)
                    else:
                        output.append(None)
                return output
            """
        ).strip()
        + "\n",
        time_complexity="O(n) total, O(1) each operation",
        space_complexity="O(n)",
        task="Simulate MinStack operations and return per-operation outputs. Use None for constructor/push/pop operations.",
        constraints=[
            "1 <= len(operations) <= 10^4",
            "values has same length as operations; each push carries one integer.",
            "All top/getMin calls are valid for generated tests.",
        ],
        hints=[
            "Maintain regular stack plus stack of running minimums.",
            "Push min(current, previous_min) to min stack on each push.",
            "Pop both stacks together.",
        ],
        common_mistakes=[
            "Computing min by scanning entire stack each time.",
            "Not syncing min stack on pop.",
            "Returning wrong placeholder values for non-query operations.",
        ],
        visible_inputs=[
            [["MinStack", "push", "push", "push", "getMin", "pop", "top", "getMin"], [[], [-2], [0], [-3], [], [], [], []]],
            [["MinStack", "push", "push", "getMin", "top"], [[], [1], [2], [], []]],
            [["MinStack", "push", "push", "pop", "getMin"], [[], [2], [1], [], []]],
            [["MinStack", "push", "getMin"], [[], [5], []]],
            [["MinStack", "push", "push", "push", "pop", "getMin"], [[], [3], [4], [2], [], []]],
            [["MinStack", "push", "top", "pop", "push", "getMin"], [[], [7], [], [], [1], []]],
        ],
        hidden_builder=generate_min_stack_hidden,
        editorial_intuition="Minimum query needs historical minima, not just current values.",
        editorial_algorithm="Pair each stack depth with minimum up to that depth via second stack.",
        company_tags=["google", "amazon", "adobe"],
        tags=["stack", "design", "constant-time-min"],
    ),
    "evaluate-reverse-polish-notation": ProblemSpec(
        signature="def solve(tokens: list[str]) -> int:",
        starter_code="def solve(tokens):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(tokens):
                stack = []
                for token in tokens:
                    if token in {"+", "-", "*", "/"}:
                        b = stack.pop()
                        a = stack.pop()
                        if token == "+":
                            stack.append(a + b)
                        elif token == "-":
                            stack.append(a - b)
                        elif token == "*":
                            stack.append(a * b)
                        else:
                            stack.append(int(a / b))
                    else:
                        stack.append(int(token))
                return stack[-1]
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(n)",
        task="Evaluate arithmetic expression in Reverse Polish Notation. Division truncates toward zero.",
        constraints=[
            "1 <= len(tokens) <= 10^4",
            "Tokens are integers or operators + - * /.",
            "Expression is valid and never divides by zero.",
        ],
        hints=[
            "Use stack of intermediate values.",
            "Operator consumes top two values: a then b.",
            "Use truncation toward zero for division.",
        ],
        common_mistakes=[
            "Using floor division for negatives instead of truncation toward zero.",
            "Reversing operand order for subtraction/division.",
            "Attempting infix parsing instead of direct stack simulation.",
        ],
        visible_inputs=[
            [["2", "1", "+", "3", "*"]],
            [["4", "13", "5", "/", "+"]],
            [["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"]],
            [["3", "-4", "+"]],
            [["5", "1", "2", "+", "4", "*", "+", "3", "-"]],
            [["-6", "2", "/"]],
        ],
        hidden_builder=generate_eval_rpn_hidden,
        editorial_intuition="Postfix notation eliminates precedence ambiguity; stack resolves dependencies naturally.",
        editorial_algorithm="Push numbers; apply operators to top two elements and push result.",
        company_tags=["amazon", "microsoft", "oracle"],
        tags=["stack", "expression-evaluation", "simulation"],
    ),
    "daily-temperatures": ProblemSpec(
        signature="def solve(temperatures: list[int]) -> list[int]:",
        starter_code="def solve(temperatures):\n    return [0] * len(temperatures)\n",
        reference_code=textwrap.dedent(
            """
            def solve(temperatures):
                stack = []
                out = [0] * len(temperatures)
                for i, t in enumerate(temperatures):
                    while stack and temperatures[stack[-1]] < t:
                        prev = stack.pop()
                        out[prev] = i - prev
                    stack.append(i)
                return out
            """
        ).strip()
        + "\n",
        time_complexity="O(n)",
        space_complexity="O(n)",
        task="For each day, return days to wait for a warmer temperature; 0 if none.",
        constraints=[
            "1 <= len(temperatures) <= 10^5",
            "30 <= temperatures[i] <= 100",
        ],
        hints=[
            "Need next greater element to the right for each index.",
            "Use monotonic decreasing stack of unresolved indices.",
            "Resolve older indices when current temperature is warmer.",
        ],
        common_mistakes=[
            "Nested scan causing O(n^2).",
            "Storing temperatures only, losing index difference.",
            "Not filling zeros for unresolved indices.",
        ],
        visible_inputs=[
            [[73, 74, 75, 71, 69, 72, 76, 73]],
            [[30, 40, 50, 60]],
            [[30, 60, 90]],
            [[90, 80, 70]],
            [[70]],
            [[65, 65, 66, 64, 67]],
        ],
        hidden_builder=generate_daily_temperatures_hidden,
        editorial_intuition="Each day waits for next higher value to the right.",
        editorial_algorithm="Maintain stack of indices with decreasing temperatures; pop when warmer day appears.",
        company_tags=["amazon", "google", "microsoft"],
        tags=["monotonic-stack", "next-greater", "array"],
    ),
    "car-fleet": ProblemSpec(
        signature="def solve(target: int, position: list[int], speed: list[int]) -> int:",
        starter_code="def solve(target, position, speed):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(target, position, speed):
                cars = sorted(zip(position, speed), reverse=True)
                fleets = 0
                last_time = -1.0
                for pos, spd in cars:
                    time = (target - pos) / spd
                    if time > last_time:
                        fleets += 1
                        last_time = time
                return fleets
            """
        ).strip()
        + "\n",
        time_complexity="O(n log n)",
        space_complexity="O(n)",
        task="Count fleets reaching target: cars merge when rear catches front before target.",
        constraints=[
            "1 <= n <= 10^5",
            "0 <= position[i] < target <= 10^6",
            "1 <= speed[i] <= 10^6",
            "All positions are distinct.",
        ],
        hints=[
            "Sort cars by position descending (closest to target first).",
            "Compute arrival time for each car.",
            "A new fleet forms only if current time is greater than fleet time ahead.",
        ],
        common_mistakes=[
            "Sorting ascending and losing catch-up interpretation.",
            "Comparing speeds instead of arrival times.",
            "Treating equal arrival time as separate fleets.",
        ],
        visible_inputs=[
            [12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]],
            [10, [3], [3]],
            [100, [0, 2, 4], [4, 2, 1]],
            [20, [6, 8], [3, 2]],
            [15, [1, 5, 10], [3, 2, 1]],
            [30, [5, 10, 15, 20], [4, 3, 2, 1]],
        ],
        hidden_builder=generate_car_fleet_hidden,
        editorial_intuition="When scanning from front to back, only non-increasing arrival times merge.",
        editorial_algorithm="Sort by position descending and count new maxima of arrival time.",
        company_tags=["amazon", "uber", "google"],
        tags=["sorting", "stack-like-scan", "simulation"],
    ),
    "binary-search": ProblemSpec(
        signature="def solve(nums: list[int], target: int) -> int:",
        starter_code="def solve(nums, target):\n    return -1\n",
        reference_code=textwrap.dedent(
            """
            def solve(nums, target):
                left, right = 0, len(nums) - 1
                while left <= right:
                    mid = (left + right) // 2
                    if nums[mid] == target:
                        return mid
                    if nums[mid] < target:
                        left = mid + 1
                    else:
                        right = mid - 1
                return -1
            """
        ).strip()
        + "\n",
        time_complexity="O(log n)",
        space_complexity="O(1)",
        task="Return index of target in sorted unique array, or -1 if absent.",
        constraints=[
            "1 <= len(nums) <= 10^5",
            "nums is sorted ascending with distinct values.",
            "-10^9 <= nums[i], target <= 10^9",
        ],
        hints=[
            "Compare target with middle element.",
            "Discard half that cannot contain target.",
            "Careful with loop condition and boundaries.",
        ],
        common_mistakes=[
            "Using while left < right and missing last element.",
            "Updating boundaries incorrectly causing infinite loop.",
            "Returning value instead of index.",
        ],
        visible_inputs=[
            [[-1, 0, 3, 5, 9, 12], 9],
            [[-1, 0, 3, 5, 9, 12], 2],
            [[5], 5],
            [[1, 3], 3],
            [[2, 4, 6, 8, 10], 6],
            [[2, 4, 6, 8, 10], 1],
        ],
        hidden_builder=generate_binary_search_hidden,
        editorial_intuition="Sorted order means each comparison halves remaining search interval.",
        editorial_algorithm="Iterative binary search with inclusive boundaries.",
        company_tags=["google", "amazon", "microsoft"],
        tags=["binary-search", "sorted-array", "divide-and-conquer"],
    ),
    "search-a-2d-matrix": ProblemSpec(
        signature="def solve(matrix: list[list[int]], target: int) -> bool:",
        starter_code="def solve(matrix, target):\n    return False\n",
        reference_code=textwrap.dedent(
            """
            def solve(matrix, target):
                if not matrix or not matrix[0]:
                    return False
                rows = len(matrix)
                cols = len(matrix[0])
                left, right = 0, rows * cols - 1
                while left <= right:
                    mid = (left + right) // 2
                    value = matrix[mid // cols][mid % cols]
                    if value == target:
                        return True
                    if value < target:
                        left = mid + 1
                    else:
                        right = mid - 1
                return False
            """
        ).strip()
        + "\n",
        time_complexity="O(log(m*n))",
        space_complexity="O(1)",
        task="Matrix rows are sorted and first item of each row is greater than last item of previous row. Return whether target exists.",
        constraints=[
            "1 <= m, n <= 300",
            "-10^4 <= matrix[i][j], target <= 10^4",
        ],
        hints=[
            "Matrix behaves like flattened sorted array.",
            "Map 1D index -> (row, col) using division and modulo.",
            "Run classic binary search over virtual indices.",
        ],
        common_mistakes=[
            "Scanning each row linearly and losing logarithmic advantage.",
            "Incorrect row/column conversion from flattened index.",
            "Not handling empty matrix safely.",
        ],
        visible_inputs=[
            [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3],
            [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13],
            [[[1]], 1],
            [[[1], [3], [5]], 4],
            [[[1, 2, 3, 4]], 3],
            [[[1, 2, 3, 4]], 8],
        ],
        hidden_builder=generate_search_2d_hidden,
        editorial_intuition="Global row ordering enables one binary search across all cells.",
        editorial_algorithm="Search over index range [0, m*n-1] with 2D coordinate mapping.",
        company_tags=["amazon", "microsoft", "google"],
        tags=["binary-search", "matrix", "index-mapping"],
    ),
    "koko-eating-bananas": ProblemSpec(
        signature="def solve(piles: list[int], h: int) -> int:",
        starter_code="def solve(piles, h):\n    return 0\n",
        reference_code=textwrap.dedent(
            """
            def solve(piles, h):
                left, right = 1, max(piles)
                while left < right:
                    speed = (left + right) // 2
                    required = sum((pile + speed - 1) // speed for pile in piles)
                    if required <= h:
                        right = speed
                    else:
                        left = speed + 1
                return left
            """
        ).strip()
        + "\n",
        time_complexity="O(n log M)",
        space_complexity="O(1)",
        task="Find minimum integer eating speed k so all piles are finished within h hours.",
        constraints=[
            "1 <= len(piles) <= 10^5",
            "1 <= piles[i] <= 10^9",
            "len(piles) <= h <= 10^9",
        ],
        hints=[
            "Feasibility is monotonic: if speed works, any faster speed works.",
            "Binary search answer space from 1 to max(piles).",
            "Hours needed for one pile at speed k is ceil(pile / k).",
        ],
        common_mistakes=[
            "Binary searching pile index instead of speed.",
            "Using floating point ceil repeatedly.",
            "Wrong boundary update when feasible.",
        ],
        visible_inputs=[
            [[3, 6, 7, 11], 8],
            [[30, 11, 23, 4, 20], 5],
            [[30, 11, 23, 4, 20], 6],
            [[312884470], 312884469],
            [[9, 9, 9], 3],
            [[1, 1, 1, 1], 8],
        ],
        hidden_builder=generate_koko_hidden,
        editorial_intuition="As speed increases, required time decreases monotonically.",
        editorial_algorithm="Binary search smallest feasible speed with hour-budget predicate.",
        company_tags=["google", "amazon", "meta"],
        tags=["binary-search-on-answer", "math", "ceil-division"],
    ),
}


def join_constraints(lines: List[str]) -> str:
    return "\n".join(f"- {line}" for line in lines)


def format_case(args: Sequence[Any], expected: Any, explanation: str) -> str:
    return (
        f"Input: `{json.dumps(as_jsonable(list(args)), ensure_ascii=False)}`\n"
        f"Output: `{json.dumps(as_jsonable(expected), ensure_ascii=False)}`\n"
        f"Explanation: {explanation}"
    )


def labels_for_problem(slug: str, visibility: str) -> List[str]:
    if visibility == "visible" and slug in STRING_PROBLEMS:
        return STRING_FOCUSED_LABELS
    return CATEGORY_LABELS


def explanation_for_case(label: str) -> str:
    return CASE_EXPLANATION_TEXT.get(label, "Case validates expected behavior.")


def build_cases(slug: str, input_rows: List[List[Any]], visibility: str) -> List[Dict[str, Any]]:
    solver = SOLVERS[slug]
    cases = []
    labels = labels_for_problem(slug, visibility)
    for idx, args in enumerate(input_rows):
        normalized_args = [as_jsonable(arg) for arg in args]
        expected = as_jsonable(solver(*normalized_args))
        label = labels[idx % len(labels)]
        cases.append(
            {
                "input": normalized_args,
                "expected": expected,
                "explanation": f"{label}: {explanation_for_case(label)}",
                "weight": 1.0,
            }
        )
    return cases


def build_editorial(spec: ProblemSpec, title: str) -> str:
    correctness = (
        f"The approach is correct because {spec.editorial_intuition.rstrip('.').lower()}."
        " The algorithm section defines a deterministic state transition, and each step keeps the"
        f" required condition for `{title}` true until termination. Therefore, the final returned"
        " value satisfies the problem definition for all valid inputs."
    )
    return (
        f"### Intuition\n{spec.editorial_intuition}\n\n"
        f"### Algorithm\n{spec.editorial_algorithm}\n\n"
        f"### Correctness\n"
        f"{correctness}\n\n"
        f"### Implementation Notes\n"
        f"- Follow the exact function signature from starter code.\n"
        f"- Validate pointer/index updates around loop boundaries.\n"
        f"### Complexity\n"
        f"- Time: `{spec.time_complexity}`\n"
        f"- Space: `{spec.space_complexity}`"
    )


def build_examples_md(slug: str, visible_cases: List[Dict[str, Any]]) -> str:
    blocks = []
    for idx, case in enumerate(visible_cases[:3], start=1):
        blocks.append(
            f"Example {idx}\n"
            + format_case(case["input"], case["expected"], case["explanation"])
        )
    return "\n\n".join(blocks)


def sentence_case_topic(topic: str) -> str:
    return re.sub(r"\s+", " ", topic.strip())


def build_statement(title: str, topic: str, spec: ProblemSpec) -> str:
    return (
        f"Solve `{title}` from the {sentence_case_topic(topic)} curriculum.\n\n"
        f"Task\n{spec.task}\n\n"
        f"Function Signature\n`{spec.signature}`\n\n"
        "Input/Output Contract\n"
        "- Read all inputs from function arguments.\n"
        "- Return the computed result in the same shape shown in examples.\n"
        "- Do not print from the function."
    )


def build_problem_payload(
    curriculum_problem: Dict[str, Any],
    spec: ProblemSpec,
    recommendation_graph: Dict[str, Dict[str, List[str]]],
    related_map: Dict[str, List[str]],
    subset_slugs: set[str],
    order_index: int,
    ordered_slugs: List[str],
) -> Dict[str, Any]:
    slug = curriculum_problem["slug"]
    title = curriculum_problem["title"]
    topic = curriculum_problem["topic"]
    subtopic = curriculum_problem["subtopic"]
    pattern = curriculum_problem["pattern"]
    difficulty = curriculum_problem["difficulty"]
    estimated_minutes = int(curriculum_problem["estimated_solving_time_minutes"])

    rng = random.Random(f"phase3d-{slug}-2026")
    visible_cases = build_cases(slug, spec.visible_inputs, "visible")
    hidden_inputs = spec.hidden_builder(rng)
    hidden_cases = build_cases(slug, hidden_inputs, "hidden")

    if len(visible_cases) < 5 or len(visible_cases) > 10:
        raise ValueError(f"{slug}: visible test count must be 5..10, got {len(visible_cases)}")
    if len(hidden_cases) < 20 or len(hidden_cases) > 50:
        raise ValueError(f"{slug}: hidden test count must be 20..50, got {len(hidden_cases)}")

    statement_md = build_statement(title, topic, spec)
    constraints_md = join_constraints(spec.constraints)
    editorial_md = build_editorial(spec, title)
    examples_md = build_examples_md(slug, visible_cases)

    prereq = [item for item in recommendation_graph["prerequisite"].get(slug, []) if item in subset_slugs]
    alternative = [item for item in recommendation_graph["alternative"].get(slug, []) if item in subset_slugs]
    follow_up = [item for item in recommendation_graph["follow_up"].get(slug, []) if item in subset_slugs]
    review = [item for item in recommendation_graph["review"].get(slug, []) if item in subset_slugs]
    recovery = [item for item in recommendation_graph["recovery"].get(slug, []) if item in subset_slugs]
    related = [item for item in related_map.get(slug, []) if item in subset_slugs and item != slug]

    if not prereq and not alternative and not follow_up and not review and not recovery and not related:
        if order_index > 0:
            prereq = [ordered_slugs[order_index - 1]]
        if order_index < len(ordered_slugs) - 1:
            follow_up = [ordered_slugs[order_index + 1]]
            related = [ordered_slugs[order_index + 1]]

    rag_statement_chunks = list(
        dict.fromkeys(
            [
                f"{title}: {spec.task}",
                f"Function signature: {spec.signature}",
                f"Key constraints: {', '.join(spec.constraints[:2])}",
            ]
        )
    )
    rag_editorial_chunks = list(
        dict.fromkeys(
            [
                spec.editorial_intuition,
                spec.editorial_algorithm,
                f"Complexity target: time {spec.time_complexity}, space {spec.space_complexity}.",
            ]
        )
    )
    rag_hint_chunks = list(dict.fromkeys(spec.hints))
    rag_common_mistakes_chunks = list(dict.fromkeys(spec.common_mistakes))
    rag_learning_chunks = list(dict.fromkeys(curriculum_problem.get("learning_objectives") or []))

    metadata = {
        "company_tags": spec.company_tags,
        "source": "premium-phase3d-internal",
        "source_citation": f"curriculum/{slug}",
        "estimated_minutes": estimated_minutes,
        "tags": sorted(set(spec.tags + [slug, difficulty.lower(), topic.lower().replace(" ", "-")])),
        "judge": {
            "time_limit_seconds": 2,
            "memory_limit_mb": 128,
            "max_output_chars": 12000,
            "visible_tests_required": True,
            "hidden_tests_required": True,
        },
        "recommendation_prerequisites": list(curriculum_problem.get("recommendation_prerequisites") or []),
        "review_prerequisites": list(curriculum_problem.get("review_prerequisites") or []),
    }

    return {
        "problem_id": slug,
        "title": title,
        "topic": topic,
        "subtopic": subtopic,
        "pattern": pattern,
        "difficulty": difficulty,
        "metadata": metadata,
        "educational_assets": {
            "statement_md": statement_md,
            "constraints_md": constraints_md,
            "examples_md": examples_md,
            "editorial_md": editorial_md,
        },
        "hints": [{"order": idx + 1, "text_md": hint} for idx, hint in enumerate(spec.hints)],
        "reference_solution": {
            "language": "python",
            "code": spec.reference_code,
            "time_complexity": spec.time_complexity,
            "space_complexity": spec.space_complexity,
        },
        "starter_code": {
            "language": "python",
            "function_name": "solve",
            "code": spec.starter_code,
        },
        "tests": {
            "visible": visible_cases,
            "hidden": hidden_cases,
        },
        "recommendation_graph": {
            "prerequisite": sorted(set(prereq)),
            "alternative": sorted(set(alternative)),
            "follow_up": sorted(set(follow_up)),
            "review": sorted(set(review)),
            "recovery": sorted(set(recovery)),
        },
        "learning_objectives": list(curriculum_problem.get("learning_objectives") or []),
        "common_mistakes": spec.common_mistakes,
        "prerequisites": list(curriculum_problem.get("prerequisites") or []),
        "related_problems": sorted(set(related)),
        "rag_assets": {
            "statement_chunks": rag_statement_chunks,
            "editorial_chunks": rag_editorial_chunks,
            "hints_chunks": rag_hint_chunks,
            "common_mistakes_chunks": rag_common_mistakes_chunks,
            "learning_objectives_chunks": rag_learning_chunks,
        },
        "version": 1,
    }


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
        if isinstance(edge, dict):
            source = edge.get("from")
            target = edge.get("to")
            if isinstance(source, str) and isinstance(target, str):
                out["alternative"][source].append(target)
                out["alternative"][target].append(source)
        elif isinstance(edge, list) and len(edge) == 2:
            source, target = edge
            if isinstance(source, str) and isinstance(target, str):
                out["alternative"][source].append(target)
                out["alternative"][target].append(source)
    for edge in graph_payload.get("review_edges", []):
        trigger = edge.get("trigger_problem") if isinstance(edge, dict) else None
        reviews = edge.get("review_problems") if isinstance(edge, dict) else None
        if isinstance(trigger, str) and isinstance(reviews, list):
            for target in reviews:
                if isinstance(target, str):
                    out["review"][trigger].append(target)
    for edge in graph_payload.get("recovery_edges", []):
        trigger = edge.get("struggling_problem") if isinstance(edge, dict) else None
        recover_with = edge.get("recover_with") if isinstance(edge, dict) else None
        if isinstance(trigger, str) and isinstance(recover_with, list):
            for target in recover_with:
                if isinstance(target, str):
                    out["recovery"][trigger].append(target)

    return out


def build_related_map(graph_payload: Dict[str, Any]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = collections.defaultdict(list)
    for edge in graph_payload.get("stretch_edges", []):
        if not isinstance(edge, dict):
            continue
        source = edge.get("from_problem")
        targets = edge.get("stretch_to")
        if isinstance(source, str) and isinstance(targets, list):
            for target in targets:
                if isinstance(target, str):
                    out[source].append(target)
    return out


def run_reference_checks(problems: List[Dict[str, Any]]) -> Dict[str, Any]:
    judge = JudgeService()
    negative_codes = {
        "wrong_answer": "def solve(*args):\n    return None\n",
        "runtime_error": "def solve(*args):\n    raise RuntimeError('boom')\n",
        "time_limit": "def solve(*args):\n    while True:\n        pass\n",
        "compilation_error": "def solve(\n    return 1\n",
        "memory_limit": "def solve(*args):\n    raise MemoryError('simulated memory pressure')\n",
    }
    results = []
    for problem in problems:
        pid = problem["problem_id"]
        code = problem["reference_solution"]["code"]
        function_name = problem["starter_code"]["function_name"]
        visible = problem["tests"]["visible"]
        hidden = problem["tests"]["hidden"]
        visible_result = judge.run_python(code, function_name, json.dumps(visible))
        hidden_result = judge.run_python(code, function_name, json.dumps(hidden))
        if visible_result["verdict"] != "Accepted":
            raise ValueError(f"{pid}: reference solution failed visible tests ({visible_result['verdict']})")
        if hidden_result["verdict"] != "Accepted":
            raise ValueError(f"{pid}: reference solution failed hidden tests ({hidden_result['verdict']})")

        negative = {}
        for name, bad_code in negative_codes.items():
            verdict = judge.run_python(bad_code, function_name, json.dumps(visible))["verdict"]
            negative[name] = verdict
        results.append(
            {
                "problem_id": pid,
                "visible_cases": len(visible),
                "hidden_cases": len(hidden),
                "visible_verdict": visible_result["verdict"],
                "hidden_verdict": hidden_result["verdict"],
                "negative_verdicts": negative,
            }
        )
    return {"problems_checked": len(results), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Premium Problem Bank Phase 3D (Problems 1-25).")
    parser.add_argument(
        "--curriculum-path",
        default="data/premium/curriculum/curriculum.json",
    )
    parser.add_argument(
        "--recommendation-graph-path",
        default="data/premium/curriculum/recommendation_graph.json",
    )
    parser.add_argument(
        "--output-path",
        default="data/premium/problem_bank.json",
    )
    parser.add_argument(
        "--report-path",
        default="reports/phase3/phase3d_generation_report.json",
    )
    args = parser.parse_args()

    curriculum_payload = json.loads(Path(args.curriculum_path).read_text(encoding="utf-8"))
    graph_payload = json.loads(Path(args.recommendation_graph_path).read_text(encoding="utf-8"))
    curriculum_items = list(curriculum_payload.get("problems") or [])[:25]
    ordered_slugs = [item["slug"] for item in curriculum_items]
    subset_slugs = set(ordered_slugs)

    missing_specs = [slug for slug in ordered_slugs if slug not in PROBLEM_SPECS]
    if missing_specs:
        raise ValueError(f"Missing generator specs for slugs: {', '.join(missing_specs)}")

    recommendation_maps = build_recommendation_maps(graph_payload)
    related_map = build_related_map(graph_payload)
    problems = []
    for idx, item in enumerate(curriculum_items):
        slug = item["slug"]
        payload = build_problem_payload(
            curriculum_problem=item,
            spec=PROBLEM_SPECS[slug],
            recommendation_graph=recommendation_maps,
            related_map=related_map,
            subset_slugs=subset_slugs,
            order_index=idx,
            ordered_slugs=ordered_slugs,
        )
        problems.append(payload)

    verification = run_reference_checks(problems)

    output_payload = {
        "schema_version": "1.0",
        "generated_at": "2026-06-26T00:00:00Z",
        "phase": "3D",
        "problem_count": len(problems),
        "problems": problems,
    }
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "summary": {
            "problems_generated": len(problems),
            "problems_validated": verification["problems_checked"],
            "visible_tests_generated": sum(len(problem["tests"]["visible"]) for problem in problems),
            "hidden_tests_generated": sum(len(problem["tests"]["hidden"]) for problem in problems),
        },
        "verification": verification,
    }
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
