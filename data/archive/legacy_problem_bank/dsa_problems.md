# DSA

## Arrays and Hashmap

### Easy

#### [Largest element in an array](https://www.geeksforgeeks.org/problems/largest-element-in-array4009/1)

##### ✅

###### Iterate through the array, updating the maximum value whenever a larger element is found.

#### [Second largest](https://www.geeksforgeeks.org/problems/second-largest3735/1)

##### ⭐️

###### 🟡

####### ✅

######## Traverse the array, updating the largest and second largest values whenever a bigger number is found or an in-between value appears.

#### [Check if array is sorted and rotated](https://leetcode.com/problems/check-if-array-is-sorted-and-rotated/#:~:text=Input%3A%20nums%20%3D%20%5B2%2C,no%20rotation)%20to%20make%20nums.)

##### ⭐️

###### 🟡

####### ✅

######## Count the number of places where the array decreases in a circular manner; if this happens at most once, the array can be rotated to become sorted.

#### [Array search](https://www.geeksforgeeks.org/problems/search-an-element-in-an-array-1587115621/1)

##### ✅

###### Linear scan the array and return the index if the target element is found; otherwise, return -1.

#### [Missing number](https://leetcode.com/problems/missing-number/)

##### ⭐️

###### 🟡

####### ✅

######## Find the missing number by subtracting the sum of the array from the sum of all numbers from 0 to n.

#### [Two sum](https://leetcode.com/problems/two-sum/)

##### ⭐️

###### 🔴

####### ✅

######## Map the numbers with their indices into a dictionary. Iterate and check if complement = target -x exists in the dictionary. Return the indices only if they are distinct.

#### [Majority element](https://leetcode.com/problems/majority-element/)

##### ⭐️

###### 🟡

####### ✅

######## Use the Boyer-Moore Voting Algorithm to track a potential majority element by incrementing or decrementing a counter during a single pass.

#### [Array leaders](https://www.geeksforgeeks.org/problems/leaders-in-an-array-1587115620/1)

##### ⭐️

###### 🟡

####### ✅

######## Traverse the array from right to left, recording elements that are greater than or equal to all elements to their right.

#### [Single number](https://leetcode.com/problems/single-number/description/)

##### ✅

###### Use XOR to cancel out duplicate numbers so that only the unique number remains.

#### [Pascal’s triangle](https://leetcode.com/problems/pascals-triangle/)

##### ⭐️

###### 🔴

####### ✅

######## Build each row of Pascal’s Triangle by summing adjacent elements from the previous row, with 1s at the ends.

#### [Find missing and repeated values](https://leetcode.com/problems/find-missing-and-repeated-values/)

##### ✅

###### Count occurrences of each number in the grid to find the repeated and missing values by checking frequencies.

#### [Valid anagram](https://leetcode.com/problems/valid-anagram/)

##### ✅

###### Compare frequency counts of both strings to check if they have the same characters.

#### [Desing hashmap](https://leetcode.com/problems/design-hashmap/description/)

##### ⭐️

#### [Maximum number of balloons](https://leetcode.com/problems/maximum-number-of-balloons/description/)

##### ⭐️

###### 🟡

####### ✅

######## Count the letters needed to form "balloon" in the text and return the minimum possible complete sets, considering duplicate letters.

#### [Number of good pairs](https://leetcode.com/problems/number-of-good-pairs/description/)

##### ⭐️

###### 🔴

####### ✅

######## Count frequencies of each number and calculate how many unique index pairs can be formed from duplicates using the combination formula.

#### [Ransom note](https://leetcode.com/problems/ransom-note)

##### ✅

###### Count each character's frequency in ransomNote and magazine and ensure magazine has enough of each required letter to construct ransomNote.

#### [Contains duplicate](https://leetcode.com/problems/contains-duplicate/)

##### ✅

###### Check if any number appears more than once by counting frequencies using a hash table or set.

#### [Contains duplicate II](https://leetcode.com/problems/contains-duplicate-ii)

##### ⭐️

###### 🔴!

####### ✅

######## Track the latest index of each number, and check if any duplicate appears within 
  k
  k distance.

#### [Convert array into zig-zag fashion](https://www.geeksforgeeks.org/problems/convert-array-into-zig-zag-fashion1638/1)

##### ⭐️

###### 🔴!

####### ✅

######## Iterate and swap adjacent elements to enforce < and > alternately for zigzag pattern.

### Medium

#### [Group anagrams](https://leetcode.com/problems/group-anagrams/)

##### ⭐️

###### ✅

####### Sort each string to create a common key, then group together all strings with the same sorted key into lists of anagrams.

#### [Encode and decode strings](https://leetcode.com/problems/encode-and-decode-strings/)

#### [Valid sudoku](https://leetcode.com/problems/valid-sudoku/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Track numbers seen in each row, column, and 3x3 box; if a duplicate appears in any, return False.

#### [Longest consecutive sequence](https://leetcode.com/problems/longest-consecutive-sequence/submissions/1665576491/)

##### ⭐️

###### 🔴!

####### ✅

######## Convert the list into a set for O(1) lookups, then iterate through each number to find the start of a sequence, and count its length, updating the maximum found.

#### [Set matrix zeros](https://leetcode.com/problems/set-matrix-zeroes/)

##### ⭐️

###### 🔴!

####### ✅

######## Mark rows and columns with zeros using the first row and column, then update the matrix in-place to set entire rows and columns to zero.

#### [Rotate image](https://leetcode.com/problems/rotate-image/)

##### ⭐️

###### 🔴!

####### ✅

######## Transpose the matrix by swapping elements across the diagonal, then reverse each row to rotate the matrix 90 degrees clockwise in-place.

#### [Spiral matrix](https://leetcode.com/problems/spiral-matrix/)

##### ⭐️

###### 🔴!

####### ✅

######## Traverse the matrix layer by layer in a spiral order by moving right across the top row, down the right column, left across the bottom row, and up the left column, adjusting boundaries after each pass until all elements are visited.

#### [Majority element II](https://leetcode.com/problems/majority-element-ii/)

#### [Number of zero-filled subarrays](https://leetcode.com/problems/number-of-zero-filled-subarrays/description/)

##### ⭐️

###### 🟡

####### ✅

######## Count the total number of zero-filled subarrays by tracking the length of consecutive zeros, adding the current count to the total whenever a zero is encountered, and resetting the count when a non-zero appears.

#### [Encode and decode tinyURL](https://leetcode.com/problems/encode-and-decode-tinyurl/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Assign a unique incremental ID to each long URL to create a short URL, store mappings between long and short URLs, and use these mappings to encode and decode URLs efficiently.

#### [Game of life](https://leetcode.com/problems/game-of-life/description/)

#### [Maximum gap](https://leetcode.com/problems/maximum-gap/description/)

#### [Insert delete getrandom O(1)](https://leetcode.com/problems/insert-delete-getrandom-o1/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Use a dictionary to map values to their indices in a list for O(1) access, store elements in a list for random access, and when removing an element, swap it with the last element before popping to maintain O(1) removal and update mappings accordingly.

#### [LRU cache](https://leetcode.com/problems/lru-cache/description/)

##### ⭐️

###### 🔴!

####### ✅

######## On get or put, move key to end (most recent); on put, evict least recently used if at capacity before inserting new key.

### Hard

#### [Text justification](https://leetcode.com/problems/text-justification/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Greedily build each line word by word. Distribute spaces evenly (extra spaces from left), then join words to match maxWidth. Left-justify the last line.

#### [First missing positive](https://leetcode.com/problems/first-missing-positive/description/)

#### [Number of submatrices that sum target](https://leetcode.com/problems/number-of-submatrices-that-sum-to-target/description/)

#### [LFU cache](https://leetcode.com/problems/lfu-cache/description/)

##### ⭐️

## Strings

### Easy

#### [Remove outermost paranthesis](https://leetcode.com/problems/remove-outermost-parentheses/)

##### ⭐️

###### 🔴!

####### ✅

######## Track balance of open and close parentheses to identify complete primitive groups, then append inner parentheses from each group by excluding the first and last characters.

#### [Largest odd number in string](https://leetcode.com/problems/largest-odd-number-in-string/)

##### ⭐️

###### 🔴

####### ✅

######## Scan the string from right to left and return the prefix up to and including the first odd digit encountered, or an empty string if none exists.

#### [Longest common prefix](https://leetcode.com/problems/longest-common-prefix/description/)

##### ⭐️

###### 🔴

####### ✅

######## Zip the strings character-wise; iterate until a mismatch appears, and build the prefix with matching characters.

#### [Isomorphic string](https://leetcode.com/problems/isomorphic-strings/description/)s

##### ⭐️

###### 🔴!

####### ✅

######## Use two dictionaries to map characters from s to t and t to s, checking for consistent one-to-one mapping while building the mappings during iteration.

#### [Rotate string](https://leetcode.com/problems/rotate-string/description/)

##### ⭐️

###### 🟡

####### ✅

######## Check if the goal string is a substring of the source string concatenated with itself and both have the same length to determine if one is a rotation of the other.

#### [Roman to integer](https://leetcode.com/problems/roman-to-integer/)

##### ⭐️

###### 🔴!

####### ✅

######## Convert each Roman numeral to its integer value and iterate through the string, adding the current value if it is greater or equal to the next, otherwise subtracting it; finally, add the last numeral's value to get the total.

#### [Check if two string arrays are equivalent](https://leetcode.com/problems/check-if-two-string-arrays-are-equivalent/description/)

##### ✅

###### Concatenate all strings in each list into a single string and compare the two resulting strings for equality.

#### [String rotated by 2 places](https://www.geeksforgeeks.org/problems/check-if-string-is-rotated-by-two-places-1587115620/1?page=1&%3Bcategory%255B%255D=Strings&%3BsortBy=)

##### ⭐️

###### 🔴!

####### ✅

######## Check if s2 equals s1 rotated left or right by 2 positions in any direction.

### Medium

#### [Sum of beauty of all substring](https://leetcode.com/problems/sum-of-beauty-of-all-substrings/description/)s

#### [Count and say](https://leetcode.com/problems/count-and-say/description/)

#### [Zigzag conversion](https://leetcode.com/problems/zigzag-conversion/description/)

#### [Minimum number of steps to make two strings anagram II](https://leetcode.com/problems/minimum-number-of-steps-to-make-two-strings-anagram-ii/description/)

#### [Custom sort string](https://leetcode.com/problems/custom-sort-string/description/)

##### ⭐️

###### 🔴

####### ✅

######## Count characters in s using a Counter, then build result by appending characters from order first followed by remaining characters not in order.

#### [Compare version numbers](https://leetcode.com/problems/compare-version-numbers/description/)

##### ✅

###### Split both version strings by '.', pad the shorter one with zeros to match lengths, then compare each integer segment pair-wise to determine which version is greater, equal, or smaller.

#### [Validate an IP address](https://leetcode.com/problems/validate-ip-address/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Split by dots, check for 4 numeric parts, no leading zeros, all in range 0–255.

### Hard

#### [Search pattern](https://www.geeksforgeeks.org/problems/search-pattern0205/1)

#### [Longest happy prefix](https://leetcode.com/problems/longest-happy-prefix/description/)

#### [Guess the word](https://leetcode.com/problems/guess-the-word/description/)

## Two Pointers and Sliding Window

### Easy

#### [Remove duplicates from sorted array](https://leetcode.com/problems/remove-duplicates-from-sorted-array/#:~:text=Input%3A%20nums%20%3D%20%5B0%2C,%2C%203%2C%20and%204%20respectively.)

#### [Move zeros](https://leetcode.com/problems/move-zeroes/)

#### [Valid palindrome](https://leetcode.com/problems/valid-palindrome/description/)

##### ⭐️

###### 🟢

####### ✅

######## Use two pointers from both ends, skipping non-alphanumeric chars and comparing case-insensitively at each step.

#### [Valid palindrome II](https://leetcode.com/problems/valid-palindrome-ii/description/)

##### ⭐️

###### 🔴

####### ✅

######## Use two pointers; on a mismatch, allow at most one character deletion by checking both possible removals for a palindrome.

#### [Best time to buy and sell stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/)

##### ⭐️

###### 🔴!

####### ✅

######## Track the minimum price so far; for each day, update max profit as the difference between current price and minimum.

#### [Maximum average subarray I](https://leetcode.com/problems/maximum-average-subarray-i/description/)

#### [Sort array by parity II](https://leetcode.com/problems/sort-array-by-parity-ii/description/)

#### [Two sum - pairs with 0 sum](https://www.geeksforgeeks.org/problems/count-pairs-with-given-sum5022/1)

##### ⭐️

###### 🔴!

####### ✅

######## Sort array, then use two pointers from both ends, collecting unique pairs whose sum is zero, skipping duplicates.

#### [Subarray with least average](https://www.geeksforgeeks.org/problems/subarray-with-least-average5031/1)

##### ⭐️

###### 🔴!

####### ✅

######## Use a fixed-size sliding window to track sum and index of the minimum average subarray, updating as the window moves.

#### [Maximum consecutive ones](https://leetcode.com/problems/max-consecutive-ones/)

#### [Merge sorted array](https://leetcode.com/problems/merge-sorted-array/)

#### [Squares of a sorted array](https://leetcode.com/problems/squares-of-a-sorted-array/description/)

#### [Find the index of the first occurrence in a string](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/description/)

#### [Is subsequence](https://leetcode.com/problems/is-subsequence/description/)

#### [Chocolate distribution problem](https://www.geeksforgeeks.org/problems/chocolate-distribution-problem3825/1)

##### ⭐️

###### 🔴!

####### ✅

########  

### Medium

#### [Two sum II - input array is sorted](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/description/)

##### ⭐️

###### 🟢

####### ✅

######## Use two pointers, one at each end of the sorted array. Move pointers inward to find pairs that sum to the target, taking advantage of the sorted order.

#### [3Sum](https://leetcode.com/problems/3sum/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Sort the array. For each number, use a two-pointer approach to find unique triplets that sum to zero, skipping duplicates to avoid repeated results.

#### [4Sum](https://leetcode.com/problems/4sum/)

##### ⭐️

###### 🔴

####### ✅

######## Extension of 3sum problem.

#### [Sort colors](https://leetcode.com/problems/sort-colors/)

#### [Rotate array](https://leetcode.com/problems/rotate-array/)

##### ⭐️

###### 🔴!

####### ✅

######## Reverse the whole array, then reverse first n−d elements and last d elements separately for in-place rotation.

#### [Containers with most water](https://leetcode.com/problems/container-with-most-water/)

##### ⭐️

###### 🟢

####### ✅

######## Use two pointers at the ends: at each step, compute area and move the pointer at the shorter line inward to maximize possible container size.

#### [Longest substring without repeating characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/description/)

##### ⭐️

###### 🔴

####### ✅

######## Use a sliding window with a set: expand right pointer to add unique chars, and shrink left pointer on duplicates to maintain a substring without repetition.

#### [Max consecutive ones III](https://leetcode.com/problems/max-consecutive-ones-iii/description/)

##### ⭐️

###### 🔴

####### ✅

######## Use a sliding window: allow up to k zeroes (by flipping), shrink window from left when flips exceed k, and track the maximum window size.

#### [Fruit into baskets](https://leetcode.com/problems/fruit-into-baskets/description/)

#### [Longest repeating character replacement](https://leetcode.com/problems/longest-repeating-character-replacement/description/)

##### ⭐️

###### 🔴

####### ✅

######## Maintain a window and track the count of most frequent char; shrink left when replacements needed exceed k. Max window size gives answer.

#### [Permutation in string](https://leetcode.com/problems/permutation-in-string/)

##### ⭐️

###### 🔴

####### ✅

######## Use sliding window and character counts; check each window of s2 for an anagram match with s1.

#### [Binary subarray with sum](https://leetcode.com/problems/binary-subarrays-with-sum/description/)

#### [Number of substring containing all three characters](https://leetcode.com/problems/number-of-substrings-containing-all-three-characters/description/)

#### [Maximum point you can obtain from cards](https://leetcode.com/problems/maximum-points-you-can-obtain-from-cards/description/)

#### [Longest substring with k uniques](https://www.geeksforgeeks.org/problems/longest-k-unique-characters-substring0853/1)

#### [Find all anagrams in a string](https://leetcode.com/problems/find-all-anagrams-in-a-string/description/)

##### ⭐️

###### 🔴

####### ✅

######## Use a sliding window and count characters; for each window of p’s length in s, check if the frequency map matches p.

#### [Maximum subarray](https://www.geeksforgeeks.org/problems/maximum-sub-array5443/1)

#### Maximum sum of distinct subarrays with length k

#### [Largest subarray with 0 sum](https://www.geeksforgeeks.org/problems/largest-subarray-with-0-sum/1)

#### [Minimum size subarray sum](https://leetcode.com/problems/minimum-size-subarray-sum/description/)

##### ⭐️

###### 🟡

####### ✅

######## Use sliding window; expand right to grow sum, shrink left when sum ≥ target, and track shortest valid window.

#### [Partition array according to given pivot](https://leetcode.com/problems/partition-array-according-to-given-pivot/description/)

#### [Find the duplicate number](https://leetcode.com/problems/find-the-duplicate-number/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Treat array values as pointers; use slow/fast approach to find cycle, then entry point gives the duplicate number.

#### [Rearrange array elements by sign](https://leetcode.com/problems/rearrange-array-elements-by-sign/)

#### [Next permutation](https://leetcode.com/problems/next-permutation/)

#### [Reverse words in a string](https://leetcode.com/problems/reverse-words-in-a-string/)

#### [Count substring](https://www.geeksforgeeks.org/problems/count-substring/1)

#### [Longest palindromic substring](https://leetcode.com/problems/longest-palindromic-substring/description/)

#### [Count palindromic subsequence ](https://www.geeksforgeeks.org/problems/count-palindromic-subsequences/1)s

### Hard

#### [Trapping rain water](https://leetcode.com/problems/trapping-rain-water/)

##### ⭐️

###### 🔴!

####### ✅

######## Precompute prefix and suffix max heights; for each bar, trapped water is min of left and right max minus current height, summed over all bars.

######## Maintain two pointers and maxes on both sides; move the side with lower height, accumulating trapped water at each step.

#### [Subarray with k different integers](https://leetcode.com/problems/subarrays-with-k-different-integers/description/)

##### ⭐️

#### [Minimum window substring](https://leetcode.com/problems/minimum-window-substring/description/)

##### ⭐️

#### [Minimum window subsequence](https://www.naukri.com/code360/problems/minimum-window-subsequence_2181133)

#### [Search a 2D matrix II](https://leetcode.com/problems/search-a-2d-matrix-ii/)

##### ⭐️

###### 🔴!

####### ✅

######## Start from top-right; if target is less, move left, if greater, move down—this efficiently prunes rows and columns in sorted 2D matrix.

#### [Sliding window maximum](https://leetcode.com/problems/sliding-window-maximum/)

##### ⭐️

###### 🔴

####### ✅

######## Use a max-heap to track window elements; after pushing new and removing out-of-window elements, report the top as current max. (not queue)

#### [Substring with concatenation of all words](https://leetcode.com/problems/substring-with-concatenation-of-all-words/description/)

## Binary Search

### 1D

#### Easy

##### [Binary search](https://leetcode.com/problems/binary-search/)

###### ⭐️

####### 🟢

######## ✅

######### Apply classic binary search: repeatedly halve the search interval by comparing target with middle element until found or interval is empty.

##### [First bad version](https://leetcode.com/problems/first-bad-version/description/)

###### ⭐️

####### 🟢

######## ✅

######### Use binary search to minimize API calls: at each step, check mid and narrow range to find the earliest version where isBadVersion returns True.

##### [Implement lower bound](https://www.geeksforgeeks.org/problems/implement-lower-bound/1)

##### [Implement upper bound](https://www.geeksforgeeks.org/problems/implement-upper-bound/1)

##### [Search insert position](https://leetcode.com/problems/search-insert-position/#:~:text=Search%20Insert%20Position%20%2D%20LeetCode&text=Given%20a%20sorted%20array%20of,(log%20n)%20runtime%20complexity.)

###### ⭐️

####### 🟢

######## ✅

######### Use binary search to find the target or its correct insertion index in sorted array by narrowing the search range with each comparison.

##### [Floor in a sorted array](https://www.geeksforgeeks.org/problems/floor-in-a-sorted-array-1587115620/1)

##### [Ceil in a sorted array](https://www.geeksforgeeks.org/problems/ceil-in-a-sorted-array/1)

##### [Number of occurence](https://www.geeksforgeeks.org/problems/number-of-occurrence2259/1)

##### [Find kth rotation](https://www.geeksforgeeks.org/problems/rotation4723/1)

#### Medium

##### [Find first and last position of element in sorted array](https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/)

###### ⭐️

####### 🟢

######## ✅

######### Use modified binary search twice: once to find the first occurrence and once for the last, by adjusting boundaries based on target matches.

##### [Search in rotated sorted array](https://leetcode.com/problems/search-in-rotated-sorted-array/)

###### ⭐️

####### 🟢

######## ✅

######### Apply binary search, determine which half is ordered each step, and narrow search to the half that must contain the target.

##### [Search in rotated sorted array II](https://leetcode.com/problems/search-in-rotated-sorted-array-ii/)

###### ⭐️

####### 🔴

######## ✅

######### Use binary search with checks for sorted halves; when elements at both ends and mid are equal, increment/decrement pointers to handle duplicates.

##### [Find minimum in rotated sorted array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/)

###### ⭐️

####### 🟡

######## ✅

######### Use binary search: check mid for rotation point and adjust search toward the unsorted half to find the minimum element.

##### [Single element in a sorted array](https://leetcode.com/problems/single-element-in-a-sorted-array/)

###### ⭐️

####### 🔴

######## ✅

######### Use binary search: exploit even-odd index pairing pattern—adjust search to the half where the single element must exist based on duplicate alignment.

##### [Find peak element](https://leetcode.com/problems/find-peak-element/#:~:text=Find%20Peak%20Element%20%2D%20LeetCode&text=A%20peak%20element%20is%20an,to%20any%20of%20the%20peaks.)

###### ⭐️

####### 🟡

######## ✅

######### Use binary search: compare mid with neighbors, and move toward the side where the next element is greater to find a peak.

### on Answers

#### Easy

##### [Sqrt(x)](https://leetcode.com/problems/sqrtx/)

###### ⭐️

####### 🟡

######## ✅

######### Use binary search to find the largest integer whose square is less than or equal to x.

##### [Kth missing positive number](https://leetcode.com/problems/kth-missing-positive-number/#:~:text=Given%20an%20array%20arr%20of,13%2C...%5D.)

###### ⭐️

####### 🔴

######## ✅

######### Use binary search: compare number of missing values up to mid with k, and adjust search range; final answer is left pointer plus k.

#### Medium

##### [Find nth root of m](https://www.geeksforgeeks.org/problems/find-nth-root-of-m5843/1)

###### ⭐️

####### 🟢

######## ✅

######### Use binary search to find integer x such that x^n=m, adjusting search bounds based on power comparison at each step.

##### [Koko eating bananas](https://leetcode.com/problems/koko-eating-bananas/)

###### ⭐️

####### 🔴

######## ✅

######### Use binary search over eating speeds; for each speed, check feasibility by computing total hours needed. Narrow range to find minimum speed.

##### [Minimum number of days to make m bouquets](https://leetcode.com/problems/minimum-number-of-days-to-make-m-bouquets/)

###### ⭐️

####### 🔴!

######## ✅

######### Binary search the days; for each candidate day, greedily count bouquets available by grouping k consecutive bloomed flowers.

##### [Find the smallest divisor](https://leetcode.com/problems/find-the-smallest-divisor-given-a-threshold/) given a threshold

###### ⭐️

####### 🟢

######## ✅

######### Use binary search to find the minimum divisor such that the sum of ceilings for each num/divisor stays within threshold.

##### [Capacity to ship packages within d days](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/)

###### ⭐️

####### 🔴!

######## ✅

######### Use binary search to find the minimum ship capacity; check feasibility by simulating shipping within days, adjusting range accordingly.

##### [Aggressive cows](https://www.geeksforgeeks.org/problems/aggressive-cows/1)

###### ⭐️

####### 🔴!

######## ✅

######### Binary search for the largest minimum distance; greedily place cows at each feasible stall, increasing distance until placement isn’t possible.

##### [Allocate minimum pages](https://www.geeksforgeeks.org/problems/allocate-minimum-number-of-pages0937/1)

###### ⭐️

####### 🔴!

######## ✅

######### Binary search on page limit: for each guess, greedily assign books to students without exceeding limit, minimizing the max pages assigned to any student.

##### [Painter's partition problem](https://www.interviewbit.com/problems/painters-partition-problem/)

###### ⭐️

####### 🔴

######## ✅

######### Binary search minimum possible max time; for each guess, greedily assign boards to painters, ensuring no one exceeds this time limit.

##### [K-th element of two arrays](http://geeksforgeeks.org/problems/k-th-element-of-two-sorted-array1317/1)

##### [Random pick with weight](https://leetcode.com/problems/random-pick-with-weight/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Precompute prefix sums; to pick index, generate a random number in the total range and use binary search to map it to corresponding index interval.

##### [K-th smallest prime fraction](https://leetcode.com/problems/k-th-smallest-prime-fraction/description/)

##### [My calendar I](https://leetcode.com/problems/my-calendar-i/description/)

###### ⭐️

####### 🔴

##### [Number of matching subsequences](https://leetcode.com/problems/number-of-matching-subsequences)

#### Hard

##### [Split array largest sum](https://leetcode.com/problems/split-array-largest-sum/)

###### ⭐️

####### 🔴

######## ✅

######### Binary search on max subarray sum; for each guess, greedily split array to minimize largest sum, ensuring no more than k partitions.

##### [Minimize max distance to gas station](https://www.geeksforgeeks.org/problems/minimize-max-distance-to-gas-station/1)

##### [Median of two sorted arrays](https://leetcode.com/problems/median-of-two-sorted-arrays/)

###### ⭐️

####### 🔴

##### [Minimum cost to make array equal](https://leetcode.com/problems/minimum-cost-to-make-array-equal/description/)

### 2D

#### Medium

##### [Search a 2D matrix](https://leetcode.com/problems/search-a-2d-matrix/)

###### ⭐️

####### 🔴

######## ✅

######### First use binary search to locate the potential row, then binary search within that row to find the target.

##### [Find a peak element II](https://leetcode.com/problems/find-a-peak-element-ii/)

###### ⭐️

####### 🟡

######## ✅

######### For each cell, check if it’s strictly greater than all four neighbors; return the coordinates of the first such peak found. (not binary search)

#### Hard

##### [Median in a row-wise sorted matrix](https://www.geeksforgeeks.org/problems/median-in-a-row-wise-sorted-matrix1527/1)

###### ⭐️

####### 🔴

### Design

#### Medium

##### [Time based key value store](https://leetcode.com/problems/time-based-key-value-store/)

###### ⭐️

####### 🔴!

######## ✅

######### Store (value, timestamp) pairs sorted by timestamp; for a get query, use binary search to find the most recent timestamp ≤ given value.

## Stacks and Queues

### Implementation

#### Easy

##### [Implement stack using array](https://www.geeksforgeeks.org/problems/implement-stack-using-array/1)

##### [Queue using array](https://www.geeksforgeeks.org/problems/implement-queue-using-array/1)

##### [Implement stack using queue](https://leetcode.com/problems/implement-stack-using-queues/description/)s

###### ⭐️

####### 🟡

######## ✅

######### Simulate stack with a single queue: push by enqueue, pop by rotating all but last to front then dequeue; top with queue’s end element.

##### [Implement queue using stack](https://leetcode.com/problems/implement-queue-using-stacks/description/)s

###### ⭐️

####### 🟡

######## ✅

######### Directly use a single list: enqueue (push) at end, dequeue (pop) from front, and peek the first element for queue behavior.

##### [Stack using linked list](https://www.geeksforgeeks.org/problems/implement-stack-using-linked-list/1)

##### [Queue using linked list](https://www.geeksforgeeks.org/problems/implement-queue-using-linked-list/1)

#### Medium

##### [Min stack](https://leetcode.com/problems/min-stack/description/)

###### ⭐️

####### 🔴

######## ✅

######### Store pairs (value, current min); push and update min with each operation so both top and min can be retrieved in O(1) time.

### Core

#### Easy

##### [Valid parentheses](https://leetcode.com/problems/valid-parentheses/)

###### ⭐️

####### 🟢

######## ✅

######### Use a stack to match opening and closing brackets: push for open, pop and check for matching close. Return false on mismatch or leftover items.

##### [Maximum nesting depth of the paranthesis](https://leetcode.com/problems/maximum-nesting-depth-of-the-parentheses/description/)

##### [Remove all adjacent duplicates in string](https://leetcode.com/problems/remove-all-adjacent-duplicates-in-string/description/)

##### [Number of recent calls](https://leetcode.com/problems/number-of-recent-calls/description/)

###### ⭐️

####### 🟡

######## ✅

######### Use a queue to store timestamps; for each ping, remove calls outside the 3000ms window, then return queue size.

##### [Time needed to buy tickets](https://leetcode.com/problems/time-needed-to-buy-tickets/description/)

##### [Number of students unable to eat lunch](https://leetcode.com/problems/number-of-students-unable-to-eat-lunch/description/)

#### Medium

##### [Generate parentheses](https://leetcode.com/problems/generate-parentheses/)

###### ⭐️

####### 🔴!

######## ✅

######### Use backtracking with counts of open and close brackets: add '(' if open < n, add ')' if close < open, to build all valid combinations.

##### [Remove duplicate letters](https://leetcode.com/problems/remove-duplicate-letters/description/)

###### ⭐️

##### [Remove stars from a string](https://leetcode.com/problems/removing-stars-from-a-string/description/)

##### [Basic calculator II](https://leetcode.com/problems/basic-calculator-ii/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Iterate and parse digits, apply each operator to current number with a stack, handling precedence by immediately evaluating * and /.

##### [Reveal cards in increasing order](https://leetcode.com/problems/reveal-cards-in-increasing-order/description/)

###### ⭐️

#### Hard

##### [Longest valid parentheses](https://leetcode.com/problems/longest-valid-parentheses/description/)

###### ⭐️

####### 🔴

######## ✅

######### Scan left-to-right and right-to-left counting '(' and ')'. When counts match, update max length. Reset counts if imbalanced to handle all valid substrings.

### Conversions

#### Medium

##### [Evaluate reverse polish notation](https://leetcode.com/problems/evaluate-reverse-polish-notation/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Use a stack: push operands, pop two for operators, apply the operation, then push the result; final result remains on the stack.

##### [Infix to postfix](https://www.geeksforgeeks.org/problems/infix-to-postfix-1587115620/1)

###### ⭐️

####### 🔴!

######## ✅

######### Use a stack to manage operators and parentheses while outputting operands directly; pop higher/equal precedence operators for each new operator, then join result.

##### [Prefix to infix conversion](https://www.geeksforgeeks.org/problems/prefix-to-infix-conversion/1)

###### ⭐️

##### [Prefix to postfix conversion](https://www.geeksforgeeks.org/problems/prefix-to-postfix-conversion/1)

###### ⭐️

##### [Postfix to prefix conversion](https://www.geeksforgeeks.org/problems/postfix-to-prefix-conversion/1)

###### ⭐️

##### [Postfix to infix conversion](https://www.geeksforgeeks.org/problems/postfix-to-infix-conversion/1)

###### ⭐️

##### [Infix to prefix notation](https://www.geeksforgeeks.org/problems/infix-to-prefix-notation/1)

###### ⭐️

### Monotonic

#### Easy

##### [Next greater element](https://www.geeksforgeeks.org/problems/next-larger-element-1587115620/1)

###### ⭐️

####### 🔴!

######## ✅

######### Use a stack to track indices; for each element, pop and resolve all previous elements smaller than current, updating their next greater value.

##### [Nearest smaller element](https://www.interviewbit.com/problems/nearest-smaller-element/)

###### ⭐️

####### 🔴!

######## ✅

######### Scan from right; use a stack to assign each element’s next left smaller. For each, pop larger values from stack and update their result.

#### Medium

##### [Daily temperatures](https://leetcode.com/problems/daily-temperatures/)

###### ⭐️

####### 🟡

######## ✅

######### Use a stack to track indices of unresolved days; for each warmer day found, pop and record the wait length as the index difference.

##### [Car fleet](https://leetcode.com/problems/car-fleet/description/)

###### ⭐️

##### [Next greater element II](https://leetcode.com/problems/next-greater-element-ii/description/)

###### ⭐️

####### 🔴

######## ✅

######### Simulate two passes with a stack; for each index, resolve all smaller elements’ next greater by wrapping indices modulo n.

##### [Sum of subarray minimum](https://leetcode.com/problems/sum-of-subarray-minimums/description/)s

###### ⭐️

####### 🔴!

######## ✅

######### For each element, find its Previous and Next Smaller Element indexes using monotonic stacks; count subarrays where it’s minimum, sum their contributions.

##### [Sum of subarray ranges](https://leetcode.com/problems/sum-of-subarray-ranges/description/)

###### ⭐️

####### 🟡

######## ✅

######### Subarray max - Subarray min

##### [Asteroid collision](https://leetcode.com/problems/asteroid-collision/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Use a stack; for each left-moving asteroid, pop smaller right-moving ones, handle equal sizes, and append if no collision occurs.

##### [Remove k digits](https://leetcode.com/problems/remove-k-digits/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Use a stack to greedily remove k digits; pop larger previous digits to form smallest number, strip leading zeros, and return result.

##### [132 pattern](https://leetcode.com/problems/132-pattern/description/)

##### [Longest continuous subarray with absolute diff less than or equal to limit](https://leetcode.com/problems/longest-continuous-subarray-with-absolute-diff-less-than-or-equal-to-limit/description/)

##### [Jump game VI](https://leetcode.com/problems/jump-game-vi/description/)

#### Hard

##### [Largest rectangle in histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/description/)

###### ⭐️

####### 🔴

######## ✅

######### For each bar, use Previous and Next Smaller Elements via stacks to determine maximal rectangle width; area is height × width, track the maximum.

##### [Maximal rectangle](https://leetcode.com/problems/maximal-rectangle/description/)

###### ⭐️

####### 🔴!

######## ✅

######### For each row, treat as histogram of consecutive 1’s heights; compute largest rectangle using Previous/Next Smaller stacks, and track maximum area.

##### [Number of visible people in a queue](https://leetcode.com/problems/number-of-visible-people-in-a-queue/description/)

###### ⭐️

##### [Max value of equation](https://leetcode.com/problems/max-value-of-equation/description/)

###### ⭐️

### Design

#### Medium

##### [Simplify path](https://leetcode.com/problems/simplify-path/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Split path by '/', use a stack to process directory names, pop for '..', ignore '.' and empty—join stack for canonical path.

##### [Online stock span](https://leetcode.com/problems/online-stock-span/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Use a stack of (price, span); for each new price, pop and sum spans of lower or equal prices, then push (price, cumulated span) and return span.

##### [The celebrity problem](https://www.geeksforgeeks.org/problems/the-celebrity-problem/1)

###### ⭐️

####### 🔴!

######## ✅

######### Count how many people each person knows and is known by; celebrity is known by everyone else, but knows no one.

## Linked List

### Singly linked list

#### Easy

##### [Inserting a node at a speicific position in a linked list](https://www.hackerrank.com/challenges/insert-a-node-at-a-specific-position-in-a-linked-list/problem)

##### [Find length of linked list](https://www.geeksforgeeks.org/problems/count-nodes-of-linked-list/1)

##### [Search in linked list](https://www.geeksforgeeks.org/problems/search-in-linked-list-1664434326/1)

##### [Middle of the linked list](https://leetcode.com/problems/middle-of-the-linked-list/description/)

###### ⭐️

####### 🟢

######## ✅

######### Use slow and fast pointers; slow advances one step, fast two, so when fast reaches end, slow is at the middle node.

##### [Reverse linked List](https://leetcode.com/problems/reverse-linked-list/) (iterative / recursive)

###### ⭐️

####### 🟡

######## ✅

######### iterative
- Iterate and reverse links one by one, moving a prev pointer forward as current node’s next is reassigned.

####### 🔴!

##### [Merge two sorted lists](https://leetcode.com/problems/merge-two-sorted-lists/)

###### ⭐️

####### 🔴!

######## ✅

######### Iterate both lists, attaching the smaller node to the result each time; connect any remaining nodes at the end.

##### [Linked list cycle](https://leetcode.com/problems/linked-list-cycle/description/)

###### ⭐️

####### 🟢

######## ✅

######### Use slow and fast pointers; if they ever meet while traversing, a cycle exists in the linked list.

##### [Palindrome linked list](https://leetcode.com/problems/palindrome-linked-list/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Find middle with slow/fast pointers, reverse second half, then compare both halves node by node for palindrome check.

##### [Intersection of two linked lists](https://leetcode.com/problems/intersection-of-two-linked-lists/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Align list heads by skipping extra nodes in longer list, then traverse both in tandem to find the intersection node (if any).

##### [Remove duplicates from sorted list](https://leetcode.com/problems/remove-duplicates-from-sorted-list/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Iterate list, and whenever consecutive nodes have equal values, bypass duplicates by adjusting pointers to skip over them.

#### Medium

##### [Design linked list](https://leetcode.com/problems/design-linked-list/description/)

###### ⭐️

####### 🔴!

##### [Deleting node in a linked list](https://leetcode.com/problems/delete-node-in-a-linked-list/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Copy next node's value to current and bypass next node by updating current's next pointer.

##### [Linked list cycle II](https://leetcode.com/problems/linked-list-cycle-ii/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Detect cycle with slow/fast pointers; on meeting, reset slow to head and move both one step to find entry point of the cycle.

##### [Find length of loop](https://www.geeksforgeeks.org/problems/find-length-of-loop/1)

##### [Odd even linked list](https://leetcode.com/problems/odd-even-linked-list/description/)

###### ⭐️

####### 🟡

######## ✅

######### Split nodes into odd and even indexed chains, then concatenate the even list after the odd for reordered result.

##### [Reorder list](https://leetcode.com/problems/reorder-list/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Find the middle, reverse second half, then merge nodes alternately from first and second halves for in-place reorder.

##### [Remove nth node from end of list](https://leetcode.com/problems/remove-nth-node-from-end-of-list/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Count total length, compute target index from start, and adjust pointers to remove the nth node from the end.

##### [Delete the middle node of a linked list](https://leetcode.com/problems/delete-the-middle-node-of-a-linked-list/description/)

##### [Sort list](https://leetcode.com/problems/sort-list/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Split list using slow/fast pointers, sort recursively, then merge two sorted halves using standard merge for linked lists.

##### [Sort a linked list of 0s, 1s and 2s](https://www.geeksforgeeks.org/problems/given-a-linked-list-of-0s-1s-and-2s-sort-it/1)

##### [Add 1 to a linked list number](https://www.geeksforgeeks.org/problems/add-1-to-a-number-represented-as-linked-list/1)

##### [Add two numbers](https://leetcode.com/problems/add-two-numbers/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Traverse both lists, sum digits with carry, create new nodes for each digit of result, and handle carry at the end.

##### [Rotate list](https://leetcode.com/problems/rotate-list/description/)

###### ⭐️

####### 🟡

######## ✅

######### Get length, find new tail after (n - k)%n steps, break and reattach the end to the old head for rotated list.

##### [Flattening of linked list](https://www.geeksforgeeks.org/problems/flattening-a-linked-list/1)

##### [Copy list with random pointer](https://leetcode.com/problems/copy-list-with-random-pointer/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Create node copies with a hashmap for original-to-copy mapping; use two passes: one for nodes and next pointers, another to assign random pointers.

##### [LRU cache](https://leetcode.com/problems/lru-cache/description/)

##### [Remove duplicates from sorted list II](https://leetcode.com/problems/remove-duplicates-from-sorted-list-ii/description/)

###### ⭐️

##### [Swap nodes in pairs](https://leetcode.com/problems/swap-nodes-in-pairs/description/)

##### [Partition list](https://leetcode.com/problems/partition-list/description/)

#### Hard

##### [Reverse nodes in k-group](https://leetcode.com/problems/reverse-nodes-in-k-group/description/)

### Doubly linked list

#### Easy

##### [Insertion at doubly linked list](https://www.geeksforgeeks.org/problems/insert-a-node-in-doubly-linked-list/1)

##### [Delete in a doubly linked list](https://www.geeksforgeeks.org/problems/delete-node-in-doubly-linked-list/1)

##### [Reverse a doubly linked list](https://www.geeksforgeeks.org/problems/reverse-a-doubly-linked-list/1)

###### ⭐️

####### 🔴

######## ✅

######### Iterate through the list, reverse both next and prev pointers at each node, and advance to the original next.

##### [Find pairs with given sum in doubly linked list](https://www.geeksforgeeks.org/problems/find-pairs-with-given-sum-in-doubly-linked-list/1)

###### ⭐️

####### 🔴!

######## ✅

######### Use two pointers at head and tail, move towards each other, and collect all node pairs whose data sum to target.

##### [Remove duplicates from a sorted doubly linked list](https://www.geeksforgeeks.org/problems/remove-duplicates-from-a-sorted-doubly-linked-list/1)

#### Medium

##### [Delete all occurrences of a given key in a doubly linked list](https://www.geeksforgeeks.org/problems/delete-all-occurrences-of-a-given-key-in-a-doubly-linked-list/1)

##### [Flatten a multilevel doubly linked list](https://leetcode.com/problems/flatten-a-multilevel-doubly-linked-list/description/)

###### ⭐️

## Heaps

### Easy

#### [Min heap implementation](https://www.geeksforgeeks.org/problems/min-heap-implementation/1)

##### ⭐️

#### [Does array represent heap](https://www.geeksforgeeks.org/problems/does-array-represent-heap4345/1)

#### [K sorted array](https://www.geeksforgeeks.org/problems/k-sorted-array1610/1)

#### [Rank transform of an array](https://leetcode.com/problems/rank-transform-of-an-array/description/)

#### [Kth largest element in a stream](https://leetcode.com/problems/kth-largest-element-in-a-stream/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Maintain a min-heap of size k; always the kth largest is at the top after each new insertion.

#### [Last stone weight](https://leetcode.com/problems/last-stone-weight/)

##### ⭐️

###### 🟡

####### ✅

######## Simulate smashing by using a max-heap (negative values); repeatedly pop the two largest, push the difference if not equal, until one or none remains.

### Medium

#### [Convert min heap to max heap](https://www.geeksforgeeks.org/problems/convert-min-heap-to-max-heap-1666385109/1)

#### [K closest points to origin](https://leetcode.com/problems/k-closest-points-to-origin/)

##### ⭐️

###### 🟡

####### ✅

######## Compute all point distances, use a min-heap, and extract the k smallest for the closest points.

#### [Kth largest element in an array](https://leetcode.com/problems/kth-largest-element-in-an-array/description/)

##### ⭐️

###### 🟢

####### ✅

######## Build max-heap (negate values), pop k−1 times; top is the kth largest element.

#### [Sort characters by frequency](https://leetcode.com/problems/sort-characters-by-frequency/description/)

##### ⭐️

#### [Kth smallest](https://www.geeksforgeeks.org/problems/kth-smallest-element5635/1)

#### [Meeting rooms II](https://www.geeksforgeeks.org/problems/attend-all-meetings-ii/1)

#### [Minimum cost of ropes](https://www.geeksforgeeks.org/problems/minimum-cost-of-ropes-1587115620/1)

##### ⭐️

###### 🟡

####### ✅

######## Use min-heap, repeatedly combine two smallest ropes, add their sum to total cost, and push back until one rope remains.

#### [Maximum sum combination](https://www.geeksforgeeks.org/problems/maximum-sum-combination/1)

#### [Top k most frequent elements](https://leetcode.com/problems/top-k-frequent-elements/description/)

##### ⭐️

###### 🟡

####### ✅

######## Count each element’s frequency, build a max-heap on frequency, and extract k most frequent elements.

#### [Top k frequent words](https://leetcode.com/problems/top-k-frequent-words/description/)

##### ⭐️

#### [Furthest building you can reach](https://leetcode.com/problems/furthest-building-you-can-reach/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Push every upward climb into a min-heap; use bricks for the smallest climbs (when heap exceeds ladders), and stop when bricks run out.

#### [Single-threaded cpu](https://leetcode.com/problems/single-threaded-cpu/description/)

##### ⭐️

#### [Process tasks using servers](https://leetcode.com/problems/process-tasks-using-servers/description/)

##### ⭐️

#### [Kth smallest element in a sorted matrix](https://leetcode.com/problems/kth-smallest-element-in-a-sorted-matrix/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Use a min-heap to track the smallest unvisited elements from each row, popping and pushing right neighbors k−1 times.

#### [Find k pairs with smallest sums](https://leetcode.com/problems/find-k-pairs-with-smallest-sums/description/)

##### ⭐️

#### [Task scheduler](https://leetcode.com/problems/task-scheduler/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Compute idle slots using (max frequency − 1) × (n + 1) + number of max-frequency tasks; result is max of this or total tasks.

######## Use a max-heap for task counts and a queue to manage cooldowns, incrementing time until all tasks are scheduled.

#### [Reorganize string](https://leetcode.com/problems/reorganize-string/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Continuously pick the highest frequency character not placed last (using max-heap), refill heap with postponed characters, and return string only if possible.

### Hard

#### [Merge k sorted lists](https://leetcode.com/problems/merge-k-sorted-lists/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Keep a min-heap of head nodes from all lists; repeatedly pop the smallest, attach to result, and push its next node until heap is empty.

#### [Find median from data stream](https://leetcode.com/problems/find-median-from-data-stream/description/)

##### ⭐️

###### 🔴!

####### ✅

######## Maintain two heaps—max-heap for the lower half and min-heap for the upper half of numbers—to insert and balance incoming elements so that the median can always be efficiently found at the top(s) of these heaps.

#### [IPO](https://leetcode.com/problems/ipo/description/)

##### ⭐️

#### [Sliding window median](https://leetcode.com/problems/sliding-window-median/description/)

##### ⭐️

###### 🟡

####### ✅

######## For each sliding window of size 
  k, build two heaps (max-heap for lower half, min-heap for upper half) from window elements and balance them to extract the median efficiently at every step.

## Recursion and Backtracking

### Basic

#### Medium

##### [String to integer (atoi)](https://leetcode.com/problems/string-to-integer-atoi/description/)

##### [Pow(x, n)](https://leetcode.com/problems/powx-n/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Use fast recursive exponentiation (exponentiation by squaring) to reduce the problem size by half each step, multiplying only once per bit of the exponent, allowing O(log n) time complexity for computing xⁿ.

##### [Count good numbers](https://leetcode.com/problems/count-good-numbers/description/)

##### [Sort a stack](https://www.geeksforgeeks.org/problems/sort-a-stack/1&selectedLang=python3)

##### [Reverse a stack](https://www.geeksforgeeks.org/problems/reverse-a-stack/1)

##### [Permutations](https://leetcode.com/problems/permutations/)

##### [Decode string](https://leetcode.com/problems/decode-string/description/)

##### [Tower of Hanoi](https://www.geeksforgeeks.org/problems/tower-of-hanoi-1587115621/1)

###### ⭐️

### Subsequences pattern

#### Easy

##### [Count all subsequences with sum k ](https://takeuforward.org/plus/dsa/problems/count-all-subsequences-with-sum-k)

#### Medium

##### [Generate all binary strings](https://www.geeksforgeeks.org/problems/generate-all-binary-strings/1)

##### [Generate parantheses](https://leetcode.com/problems/generate-parentheses/description/)

##### [Subsets](https://leetcode.com/problems/subsets/description/)

##### [Check if there exists a subsequence with sum k](https://www.geeksforgeeks.org/problems/check-if-there-exists-a-subsequence-with-sum-k/1)

##### [Combination sum](https://leetcode.com/problems/combination-sum/description/)

##### [Combination sum II](https://leetcode.com/problems/combination-sum-ii/description/)

##### [Combination sum III](https://leetcode.com/problems/combination-sum-iii/description/)

##### [Subset sums](https://www.geeksforgeeks.org/problems/subset-sums2234/1&selectedLang=python3)

##### [Subsets II](https://leetcode.com/problems/subsets-ii/)

##### [Letter combinations of a phone number](https://leetcode.com/problems/letter-combinations-of-a-phone-number/description/)

### Combos

#### Medium

##### [Word search](https://leetcode.com/problems/word-search/description/)

##### [Rat in a maze problem - I](https://www.geeksforgeeks.org/problems/rat-in-a-maze-problem/1&selectedLang=python3)

##### [M-coloring problem](https://www.geeksforgeeks.org/problems/m-coloring-problem-1587115620/1)

##### [Minimum moves to spread stones over grid](https://leetcode.com/problems/minimum-moves-to-spread-stones-over-grid/description/)

#### Hard

##### [N-queen](https://leetcode.com/problems/n-queens/description/)s

##### [Sudoku solver](https://leetcode.com/problems/sudoku-solver/description/)

##### [Expression add operators](https://leetcode.com/problems/expression-add-operators/description/)

## Trees

### Binary Trees

#### Traversals

##### Easy

###### [Binary tree preorder traversal](https://leetcode.com/problems/binary-tree-preorder-traversal/description/) - Recursive / Iterative

####### ⭐️

######## 🟢

######### ✅
- Recursively visit and record the current node value, then traverse the left subtree followed by the right subtree—processing nodes in root-left-right order.

###### [Binary tree inorder traversal](https://leetcode.com/problems/binary-tree-inorder-traversal/description/) - Recursive / Iterative

####### ⭐️

######## 🟢

######### ✅
- Recursively traverse the left subtree, then process the current node, and finally traverse the right subtree—ensuring nodes are visited in left-root-right order.

###### [Binary tree postorder traversal](https://leetcode.com/problems/binary-tree-postorder-traversal/description/) - Recursive / Iterative

####### ⭐️

######## 🟢

######### ✅
- Recursively traverse the left subtree, then the right subtree, and finally process the current node, ensuring nodes are visited in left-right-root order.

##### Medium

###### [Binary tree level order traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/description/)

####### ⭐️

######## 🟡

######### ✅
- Use a queue to perform breadth-first traversal, processing each level’s nodes from left to right and collecting their children for the next level until the entire tree is visited.

###### [Binary tree zigzag level order traversal](https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/description/)

####### ⭐️

######## 🟢

######### ✅
- Perform breadth-first traversal using a queue and alternate the direction of values at each level—left-to-right for one level, then right-to-left (by reversing) for the next—before adding to the result.

###### [Tree boundary traversal](https://www.geeksforgeeks.org/problems/boundary-traversal-of-binary-tree/1)

####### ⭐️

######## 🔴!

######### ✅
- Traverse the binary tree boundary in three stages—first collect the left boundary excluding leaves, then all leaf nodes, and finally the right boundary in reverse order—ensuring each node is visited once and included at most once in the traversal.

###### [Populating next right pointers in each node II](https://leetcode.com/problems/populating-next-right-pointers-in-each-node-ii/description/)

###### [Throne inheritance](https://leetcode.com/problems/throne-inheritance/description/)

####### ⭐️

##### Hard

###### [Vertical order traversal of a binary tree](https://leetcode.com/problems/vertical-order-traversal-of-a-binary-tree/description/)

####### ⭐️

#### Views

##### Medium

###### [Top view of binary tree](https://www.geeksforgeeks.org/problems/top-view-of-binary-tree/1)

####### ⭐️

######## 🔴!

######### ✅
- Perform level-order traversal, track each node’s horizontal distance, and record the first node encountered at each distance to represent the topmost visible nodes when viewing the tree from above.

###### [Bottom view of binary tree](https://www.geeksforgeeks.org/problems/bottom-view-of-binary-tree/1)

####### ⭐️

######## 🟡

######### ✅
- Perform level-order traversal with a queue, recording and updating the node at each horizontal distance so that only the last (bottommost) node at each distance is kept, producing the bottom view from left to right.

###### [Left view of binary tree](https://www.geeksforgeeks.org/problems/left-view-of-binary-tree/1)

####### ⭐️

######## 🟢

######### ✅
- Use level-order traversal and select the first node encountered at each level to form the left view, capturing the leftmost visible nodes from top to bottom.

###### [Binary tree right side view](https://leetcode.com/problems/binary-tree-right-side-view/description/)

####### ⭐️

######## 🟢

######### ✅
- Use level-order traversal and at each level, record the last (rightmost) node visited to represent the nodes visible from the right side of the tree, giving the right side view from top to bottom.

#### Core

##### Easy

###### [Maximum depth of binary tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/description/)

####### ⭐️

######## 🟢

######### ✅
- Solve this by recursively finding the maximum depth of the left and right subtrees at each node, and returning the greater of the two plus one to account for the current node.

###### B[alanced binary tree](https://leetcode.com/problems/balanced-binary-tree/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by recursively checking the depth of left and right subtrees at each node, and if the difference in depths is greater than one at any node, or any subtree is already unbalanced, return unbalanced; otherwise, return balanced.

###### [Diameter of binary tree](https://leetcode.com/problems/diameter-of-binary-tree/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by recursively computing the longest path (edge count) through each node as the sum of left and right subtree depths, updating the maximum diameter found, and returning the overall largest such value.

###### [Invert binary tree](https://leetcode.com/problems/invert-binary-tree/)

####### ⭐️

######## 🟡

######### ✅
- Solve this by recursively swapping the left and right children of every node in the tree, resulting in a mirror image of the original binary tree.

###### [Same tree](https://leetcode.com/problems/same-tree/description/)

####### ⭐️

######## 🔴

######### ✅
- Solve this by recursively comparing corresponding nodes of both trees to ensure both structure and values are identical at every position.

###### [Symmetric tree](https://leetcode.com/problems/symmetric-tree/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by recursively checking whether the left and right subtrees are mirror images of each other, comparing corresponding nodes for symmetry at each level.

###### [Subtree of another tree](https://leetcode.com/problems/subtree-of-another-tree/)

###### [Count complete tree nodes](https://leetcode.com/problems/count-complete-tree-nodes/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by checking if the tree is a perfect binary tree (left and right depths equal) to count nodes directly with the formula 
  2^(depth+1)−1; otherwise, recursively count nodes in left and right subtrees plus one for the root.

###### [Unique binary tree requirements](https://www.geeksforgeeks.org/problems/unique-binary-tree-requirements/1)

###### [Binary tree paths](https://leetcode.com/problems/binary-tree-paths/description/)

####### ⭐️

######## 🟡

######### ✅
- Solve this by performing DFS to build all root-to-leaf paths as strings formed by concatenating node values with '->', adding each complete path to the result list when a leaf is reached.

###### [Path sum](https://leetcode.com/problems/path-sum/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by recursively checking if there exists a root-to-leaf path whose node values sum up to the target, tracking the running total along each path and returning true upon finding a matching sum.

##### Medium

###### [Path sum II](https://leetcode.com/problems/path-sum-ii/)

####### ⭐️

######## 🟡

######### ✅
- Solve this by using DFS to explore all root-to-leaf paths, collecting those where the sum of node values equals the target, and storing each matching path in a result list.

###### [Path sum III](https://leetcode.com/problems/path-sum-iii/description/)

####### ⭐️

######## 🔴!

######### ✅
- Recursively explore all paths starting from every node, updating the path sum, and counting paths where the sum equals the target.

###### [Root to leaf paths](https://www.geeksforgeeks.org/problems/root-to-leaf-paths/1)

####### ⭐️

######## 🟡

######### ✅
- Solve this by performing a depth-first traversal, recording each root-to-leaf path as a list when a leaf node is reached, and collecting all such paths in a result list.

###### [Count good nodes in binary tree](https://leetcode.com/problems/count-good-nodes-in-binary-tree/)

###### [Maximum width of binary tree](https://leetcode.com/problems/maximum-width-of-binary-tree/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by using level-order traversal with indexing for each node, updating the maximum width by calculating the difference between the leftmost and rightmost indices at every level.

###### [Children sum in a binary tree](https://www.geeksforgeeks.org/problems/children-sum-parent/1)

###### [All nodes distance k in binary tree](https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by first converting the binary tree into an undirected graph (adjacency list), then using BFS from the target node to find all nodes exactly k steps away.

###### [Construct binary tree from preorder and inorder traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by recursively constructing the binary tree, using the first element of preorder as the root and partitioning the inorder list to build left and right subtrees accordingly.

###### [Construct binary tree from inorder and postorder traversal](https://leetcode.com/problems/construct-binary-tree-from-inorder-and-postorder-traversal/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by recursively building the binary tree, taking the last element of postorder as the root, partitioning the inorder list at the root's index, and constructing right and left subtrees accordingly.

###### [Flatten binary tree to linked list](https://leetcode.com/problems/flatten-binary-tree-to-linked-list/description/)

####### ⭐️

######## 🔴!

######### ✅
- Solve this by iteratively modifying the tree so that each node's left subtree is moved to the right, and the original right subtree is attached to the rightmost node of the moved left subtree, resulting in a flattened right-skewed linked list.

###### [Lowest common ancestor of a binary tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/description/)

####### ⭐️

######## 🔴!

######### ✅
- Use DFS: if both p and q are found in different subtrees, root is LCA; else, propagate non-null child upwards.

###### [Maximum difference between node and ancestor](https://leetcode.com/problems/maximum-difference-between-node-and-ancestor/description/)

###### [Delete nodes and return forest](https://leetcode.com/problems/delete-nodes-and-return-forest/description/)

####### ⭐️

###### [Find duplicate subtrees](https://leetcode.com/problems/find-duplicate-subtrees/description/)

####### ⭐️

###### [Distribute coins in binary tree](https://leetcode.com/problems/distribute-coins-in-binary-tree/description/)

###### [Employee importance](https://leetcode.com/problems/employee-importance/description/)

###### [Minimum height trees](https://leetcode.com/problems/minimum-height-trees/description/)

###### [Step-by-step directions from a binary tree node to another](https://leetcode.com/problems/step-by-step-directions-from-a-binary-tree-node-to-another/description/)

####### ⭐️

##### Hard

###### [Binary tree maximum path sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/description/)

####### ⭐️

###### [Burning tree](https://www.geeksforgeeks.org/problems/burning-tree/1)

####### ⭐️

###### [Serialize and deserialize binary tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/description/)

####### ⭐️

### Binary Search Trees / Ordered Set

#### Easy

##### [Search in a binary search tree](https://leetcode.com/problems/search-in-a-binary-search-tree/description/)

###### ⭐️

####### 🟢

######## ✅

######### Solve this by recursively traversing the binary search tree, moving left or right depending on whether the target value is smaller or larger than the current node, and returning the node if found.

##### [Minimum element in BST](https://www.geeksforgeeks.org/problems/minimum-element-in-bst/1)

##### [Inorder successor in BST](https://www.geeksforgeeks.org/problems/inorder-successor-in-bst/1)

###### ⭐️

##### [Two sum IV - input is a BST](https://leetcode.com/problems/two-sum-iv-input-is-a-bst/description/)

###### ⭐️

#### Medium

##### [Ceil in BST](https://www.geeksforgeeks.org/problems/implementing-ceil-in-bst/1)

##### [Floor in BST](https://www.geeksforgeeks.org/problems/floor-in-bst/1)

##### [Insert into binary search tree](https://leetcode.com/problems/insert-into-a-binary-search-tree/description/)

###### ⭐️

##### [Delete node in a BST](https://leetcode.com/problems/delete-node-in-a-bst/description/)

###### ⭐️

##### [Kth smallest element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/description/)

###### ⭐️

##### [Validate binary search tree](https://leetcode.com/problems/validate-binary-search-tree/description/)

###### ⭐️

##### [Lowest common ancestor of a binary search tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/description/)

###### ⭐️

####### 🔴!

######## ✅

######### Leverage BST properties: move down the tree—LCA is the node where p and q split to different sides, or one is equal to root.

##### [Construct binary search tree from preorder traversal](https://leetcode.com/problems/construct-binary-search-tree-from-preorder-traversal/description/)

##### [Predecessor and successor](https://www.geeksforgeeks.org/problems/predecessor-and-successor/1)

##### [Binary search tree iterator](https://leetcode.com/problems/binary-search-tree-iterator/description/)

###### ⭐️

##### [Merge two BST's](https://www.geeksforgeeks.org/problems/merge-two-bst-s/1)

###### ⭐️

##### [Recover binary search tree](https://leetcode.com/problems/recover-binary-search-tree/description/)

###### ⭐️

##### [Largest BST](https://www.geeksforgeeks.org/problems/largest-bst/1)

##### [Convert sorted array to binary search tree](https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/description/)

###### ⭐️

##### [Trim a binary search tree](https://leetcode.com/problems/trim-a-binary-search-tree/description/)

##### [Stock price fluctuation](https://leetcode.com/problems/stock-price-fluctuation/description/)

### [Generic Trees](https://www.geeksforgeeks.org/dsa/what-is-generic-tree-or-n-ary-tree/)

#### ⭐️

## Graphs

### BFS / DFS

#### Easy

##### [Flood fill](https://leetcode.com/problems/flood-fill/description/)

###### ⭐️

####### ✅

######## Change the color of the given coord, and run bfs from that coord.

#### Medium

##### [Connected components in an undirected graph](https://www.geeksforgeeks.org/problems/connected-components-in-an-undirected-graph/1)

###### ⭐️

####### ✅

######## Generic connected components algo.

##### [Number of provinces](https://leetcode.com/problems/number-of-provinces/description/)

###### ⭐️

####### 🔁

######## ✅

######### Connected components problem, where neighbor is also in range of an inner binary array.

##### [Rotten oranges](https://leetcode.com/problems/rotting-oranges/description/)

###### ⭐️

####### ✅

######## Collect all the fresh and rotten oranges and run a multilevel bfs to get the total time.

##### [Undirected graph cycle](https://www.geeksforgeeks.org/problems/detect-cycle-in-an-undirected-graph/1)

###### ⭐️

####### 🔁

######## ✅

######### Generic algo problem to find cycle in UG.

##### [0/1 matrix](https://leetcode.com/problems/01-matrix/description/)

###### ⭐️

####### ✅

##### [Surrounded regions](https://leetcode.com/problems/surrounded-regions/description/)

##### [Number of enclaves](https://leetcode.com/problems/number-of-enclaves/description/)

###### ⭐️

####### ✅

##### [Number of islands](https://leetcode.com/problems/number-of-islands/description/)

###### ⭐️

####### ✅

##### [Number of distinct islands](https://www.geeksforgeeks.org/problems/number-of-distinct-islands/1)

###### ⭐️

####### 🔁

######## ✅

##### [Max area of island](https://leetcode.com/problems/max-area-of-island/description/)

###### ⭐️

####### ✅

##### [Islands and treasure](https://neetcode.io/problems/islands-and-treasure?list=neetcode150)

##### [Pacific atlantic water flow](https://leetcode.com/problems/pacific-atlantic-water-flow/description/)

###### ⭐️

####### 🔁

######## ✅

##### [Is graph bipartite?](https://leetcode.com/problems/is-graph-bipartite/description/)

###### ⭐️

####### 🔁

######## ✅

##### [Graph is tree or not](https://www.geeksforgeeks.org/problems/is-it-a-tree/1)

###### ⭐️

####### 🔁

######## ✅

##### [Clone graph](https://leetcode.com/problems/clone-graph/description/)

###### ⭐️

####### 🔁

######## ✅

##### [Time needed to inform all employees](https://leetcode.com/problems/time-needed-to-inform-all-employees/description/)

##### [All paths from source to target](https://leetcode.com/problems/all-paths-from-source-to-target/description/)

###### ⭐️

####### 🔁

######## ✅

##### [Open the lock](https://leetcode.com/problems/open-the-lock/description/)

###### ⭐️

##### [Snakes and ladders](https://leetcode.com/problems/snakes-and-ladders/description/)

###### ⭐️

##### [As far land as possible](https://leetcode.com/problems/as-far-from-land-as-possible/description/)

##### [Shortest bridge](https://leetcode.com/problems/shortest-bridge/description/)

###### ⭐️

####### 🔁

######## ✅

#### Hard

##### [Word ladder](https://leetcode.com/problems/word-ladder/description/)

###### ⭐️

####### 🔁

######## ✅

##### [Word ladder II](https://leetcode.com/problems/word-ladder-ii/description/)

###### ⭐️

####### ❌

##### [Bus routes](https://leetcode.com/problems/bus-routes/description/)

##### [Shortest path in a grid with obstacles elimination](https://leetcode.com/problems/shortest-path-in-a-grid-with-obstacles-elimination/description/)

### Topological Sort

#### Medium

##### [Topological sort](https://www.geeksforgeeks.org/problems/topological-sort/1)

###### ⭐️

####### 🔁

######## ✅

######### Generic topological sort problem.

##### [Directed graph cycle](https://www.geeksforgeeks.org/problems/detect-cycle-in-a-directed-graph/1)

###### ⭐️

####### 🔁

######## ✅

######### Generic algo to find cycle in DG.

##### [Course schedule](https://leetcode.com/problems/course-schedule/description/)

###### ⭐️

####### ✅

######## Check if the graph has cycle or not.

##### [Course schedule II](https://leetcode.com/problems/course-schedule-ii/description/)

###### ⭐️

####### 🔁

######## ✅

######### If the graph has cycle return an empty list else return the topological order of the vertices.

##### [Find eventual safe states](https://leetcode.com/problems/find-eventual-safe-states/description/)

###### ⭐️

####### 🔁

######## ✅

######### Find a vertex which is not a part of the cycle, but don’t mark it as visited initially; process all the neighbors from it and if if lands at  a terminal vertex, it is a safe vertex.

#### Hard

##### [Alien dictionary](https://www.geeksforgeeks.org/problems/alien-dictionary/1)

###### ⭐️

####### 🔁

######## ✅

######### Prepare an adjacency list where a character appears before a in topological ordering. Get the topological ordering of the characters only if there is no cycle.

##### [Sort items by groups respecting dependencies](https://leetcode.com/problems/sort-items-by-groups-respecting-dependencies/description/)

### Shortest Path

#### Medium

##### [Shortest path in undirected graph](https://www.geeksforgeeks.org/problems/shortest-path-in-undirected-graph-having-unit-distance/1)

###### ⭐️

####### 🔁

######## ✅

######### Run a bfs since the graph has unit weights. Get all shortest paths from source to all the vertices.

##### [Shortest path in directed acyclic graph](https://www.geeksforgeeks.org/problems/shortest-path-in-undirected-graph/1)

###### ⭐️

####### 🔁

######## ✅

######### Topologically sort the DAG. Then relax the edges and find the shortest paths from the source.

##### [Djisktra's algorithm](https://www.geeksforgeeks.org/problems/implementing-dijkstra-set-1-adjacency-matrix/1)

###### ⭐️

##### [Shortest path in a binary matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/description/)

###### ⭐️

##### [Path with minimum effort](https://leetcode.com/problems/path-with-minimum-effort/description/)

###### ⭐️

##### [Cheapest flights within k stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/description/)

###### ⭐️

##### [Network delay time](https://leetcode.com/problems/network-delay-time/description/)

###### ⭐️

##### [Minimum multiplications to reach end](https://www.geeksforgeeks.org/problems/minimum-multiplications-to-reach-end/1)

##### [Path with maximum probability](https://leetcode.com/problems/path-with-maximum-probability/description/)

##### [Find the city with the smallest number of neighbors at a threshold distance](https://leetcode.com/problems/find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance/description/)

###### ⭐️

##### [Evaluate division](https://leetcode.com/problems/evaluate-division/)

###### ⭐️

#### Hard

##### [Swim in rising water](https://leetcode.com/problems/swim-in-rising-water/description/)

###### ⭐️

##### [Longest path in a directed acyclic graph](https://www.geeksforgeeks.org/problems/longest-path-in-a-directed-acyclic-graph/1)

##### [Design graph with shortest path calculator](https://leetcode.com/problems/design-graph-with-shortest-path-calculator/description/)

### Minimum spanning tree / Disjoint set / Union find

#### Easy

##### [Union find](https://www.geeksforgeeks.org/problems/union-find/1)

#### Medium

##### [Minimum spanning tree](https://www.geeksforgeeks.org/problems/minimum-spanning-tree/1)

###### ⭐️

##### [Number of operations to make network connected](https://leetcode.com/problems/number-of-operations-to-make-network-connected/description/)

###### ⭐️

##### [Most stones removed with same row or column](https://leetcode.com/problems/most-stones-removed-with-same-row-or-column/description/)

###### ⭐️

##### [Accounts merge](https://leetcode.com/problems/accounts-merge/description/)

###### ⭐️

##### [Redundant connection](https://leetcode.com/problems/redundant-connection/description/)

###### ⭐️

##### [Min cost to connect all points](https://leetcode.com/problems/min-cost-to-connect-all-points/description/)

###### ⭐️

#### Hard

##### [Number of islands II](https://www.naukri.com/code360/problems/number-of-islands-ii_1266048)

##### [Making a large island](https://leetcode.com/problems/making-a-large-island/description/)

##### [Minimize malware spread](https://leetcode.com/problems/minimize-malware-spread/description/)

##### [Remove max number of edges to keep graph fully traversable](https://leetcode.com/problems/remove-max-number-of-edges-to-keep-graph-fully-traversable/description/)

##### [Checking existence of edge length limited paths](https://leetcode.com/problems/checking-existence-of-edge-length-limited-paths/description/)

##### [Find all people with secret](https://leetcode.com/problems/find-all-people-with-secret/description/)

###### ⭐️

### Eulerian circuit

#### Hard

##### [Reconstruct itinerary](https://leetcode.com/problems/reconstruct-itinerary/description/)

###### ⭐️

##### [Cracking the safe](https://leetcode.com/problems/cracking-the-safe/description/)

### Advanced

#### Hard

##### [Critical connections in a network](https://leetcode.com/problems/critical-connections-in-a-network/description/)

###### ⭐️

## Intervals

### Medium

#### [Insert Interval](https://leetcode.com/problems/insert-interval/description/)

#### [Merge Intervals](https://leetcode.com/problems/merge-intervals/description/)

#### [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/description/)

#### [Minimum number of arrows to burst balloons](https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/description/)

#### [Maximum number of events that can be attended](https://leetcode.com/problems/maximum-number-of-events-that-can-be-attended/description/)

### Easy

#### [Meeting rooms](https://www.geeksforgeeks.org/problems/attend-all-meetings/1)

### Hard

#### [Minimum interval to include each query](https://leetcode.com/problems/minimum-interval-to-include-each-query/description/)

## Dynamic Programming

### 1D

#### Easy

##### [Fibonacci number](https://leetcode.com/problems/fibonacci-number/description/)

##### [Climbing stairs](https://leetcode.com/problems/climbing-stairs/description/)

##### [Min cost climbing stairs](https://leetcode.com/problems/min-cost-climbing-stairs/description/)

#### Medium

##### [Frog jump](https://www.geeksforgeeks.org/problems/geek-jump/1)

##### [Frog Jump with k distances](https://takeuforward.org/plus/dsa/problems/frog-jump-with-k-distances)

##### [House robber](https://leetcode.com/problems/house-robber/description/)

##### [House robber II](https://leetcode.com/problems/house-robber-ii/description/)

#### Hard

##### [Maximum sum of subsequence with non-adjacent elements](https://leetcode.com/problems/maximum-sum-of-subsequence-with-non-adjacent-elements/description/)

### Knapsack

#### Medium

##### [Subset sum](https://www.geeksforgeeks.org/problems/subset-sum-problem-1611555638/1)

##### [Partition equal subset sum](https://leetcode.com/problems/partition-equal-subset-sum/description/)

##### [Target sum](https://leetcode.com/problems/target-sum/description/)

##### [Last stone weight II](https://leetcode.com/problems/last-stone-weight-ii/description/)

##### [Perfect sum problem](https://www.geeksforgeeks.org/problems/perfect-sum-problem5633/1)

### Unbounded Knapsack

#### Medium

##### [Coin change](https://leetcode.com/problems/coin-change/description/)

##### [Coin change II](https://leetcode.com/problems/coin-change-ii/description/)

##### [Perfect squares](https://leetcode.com/problems/perfect-squares/description/)

##### [Integer break](https://leetcode.com/problems/integer-break/description/)

### 2D

#### Medium

##### [Ninja's training](https://www.naukri.com/code360/problems/ninja-s-training_3621003)

##### [Unique paths](https://leetcode.com/problems/unique-paths/description/)

##### [Unique paths II](https://leetcode.com/problems/unique-paths-ii/description/)

##### [Minimum path sum](https://leetcode.com/problems/minimum-path-sum/description/)

##### [Triangle](https://leetcode.com/problems/triangle/description/)

##### [Minimum falling path sum](https://leetcode.com/problems/minimum-falling-path-sum/description/)

##### [Count square submatrices with all ones](https://leetcode.com/problems/count-square-submatrices-with-all-ones/description/)

##### [Maximum number of points with cost](https://leetcode.com/problems/maximum-number-of-points-with-cost/description/)

#### Hard

##### [Maximum profit in job scheduling](https://leetcode.com/problems/maximum-profit-in-job-scheduling/description/)

##### [Cherry pickup](https://leetcode.com/problems/cherry-pickup/description/)

##### [Cherry pickup II](https://leetcode.com/problems/cherry-pickup-ii/description/)

##### [Longest increasing path in a matrix](https://leetcode.com/problems/longest-increasing-path-in-a-matrix/description/)

### on Subsequences

#### Easy

##### [Assign cookies](https://leetcode.com/problems/assign-cookies/description/)

#### Medium

##### [Count subsets with sum k](https://www.naukri.com/code360/problems/count-subsets-with-sum-k_3952532)

##### [Partitions with given difference](https://www.geeksforgeeks.org/problems/partitions-with-given-difference/1)

##### [Knapsack with duplicate items](https://www.geeksforgeeks.org/problems/knapsack-with-duplicate-items4201/1)

##### [Rod cutting](https://www.geeksforgeeks.org/problems/rod-cutting0840/1)

#### Hard

##### [Distinct subsequences](https://leetcode.com/problems/distinct-subsequences/description/)

##### [Partition array into two arrays to minimize sum difference](https://leetcode.com/problems/partition-array-into-two-arrays-to-minimize-sum-difference/description/)

### on Strings

#### Medium

##### [Longest common subsequence](https://leetcode.com/problems/longest-common-subsequence/description/)

##### [Edit distance](https://leetcode.com/problems/edit-distance/description/)

##### [Longest common substring](https://www.geeksforgeeks.org/problems/longest-common-substring1452/1)

##### [Longest palindromic subsequence](https://leetcode.com/problems/longest-palindromic-subsequence/description/)

##### [Longest palindromic substring](https://leetcode.com/problems/longest-palindromic-substring/description/)

##### [Palindromic substrings](https://leetcode.com/problems/palindromic-substrings/description/)

##### [Delete operation for two strings](https://leetcode.com/problems/delete-operation-for-two-strings/description/)

##### [Decode ways](https://leetcode.com/problems/decode-ways/description/)

##### [Interleaving string](https://leetcode.com/problems/interleaving-string/description/)

##### [Word break](https://leetcode.com/problems/word-break/description/)

#### Hard

##### [Print all LCS sequences](https://www.geeksforgeeks.org/problems/print-all-lcs-sequences3413/1)

##### [Minimum insertions steps to make a string palindrome](https://leetcode.com/problems/minimum-insertion-steps-to-make-a-string-palindrome/description/)

##### [Shortest common supersequence](https://leetcode.com/problems/shortest-common-supersequence/description/)

##### [Wildcard matching](https://leetcode.com/problems/wildcard-matching/description/)

##### [Palindrome partitioning II](https://leetcode.com/problems/palindrome-partitioning-ii/description/)

### on Stocks

#### Easy

##### [Best time to buy and sell stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/description/)

#### Medium

##### [Best time to buy and sell stock II](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/description/)

##### [Best time to buy and sell stocks with cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/description/)

##### [Best time to buy and sell stocks with transaction fee](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-transaction-fee/description/)

#### Hard

##### [Best time to buy and sell stocks III](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/description/)

##### [Best time to buy and sell stock IV](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/description/)

### on Longest Increasing Subsequence

#### Medium

##### [Longest increasing subsequence](https://leetcode.com/problems/longest-increasing-subsequence/)

##### [Printing longest increasing subsequence](https://www.geeksforgeeks.org/problems/printing-longest-increasing-subsequence/1)

##### [Largest divisible subset](https://leetcode.com/problems/largest-divisible-subset/description/)

##### [Longest string chain](https://leetcode.com/problems/longest-string-chain/description/)

##### [Number of longest increasing subsequence](https://leetcode.com/problems/number-of-longest-increasing-subsequence/description/)

##### [Longest bitonic subsequence](https://www.geeksforgeeks.org/problems/longest-bitonic-subsequence0824/1)

#### Hard

##### [Russian doll envelopes](https://leetcode.com/problems/russian-doll-envelopes/description/)

##### [Longest increasing subsequence II](https://leetcode.com/problems/longest-increasing-subsequence-ii/description/)

### Matrix Chain Multiplication

#### Medium

##### [Partition array for maximum sum](https://leetcode.com/problems/partition-array-for-maximum-sum/description/)

##### [Palindrome partitioning](https://leetcode.com/problems/palindrome-partitioning/description/)

#### Hard

##### [Matrix chain multiplication](https://www.geeksforgeeks.org/problems/matrix-chain-multiplication0303/1)

##### [Minimum cost to cut a stick](https://leetcode.com/problems/minimum-cost-to-cut-a-stick/description/)

##### [Parsing a boolean expression](https://leetcode.com/problems/parsing-a-boolean-expression/description/)

##### [Regular expression matching](https://leetcode.com/problems/regular-expression-matching/description/)

##### [Burst balloons](https://leetcode.com/problems/burst-balloons/description/)

##### [Strange printer](https://leetcode.com/problems/strange-printer/description/)

### on Squares

#### Hard

##### [Maximal rectangle](https://leetcode.com/problems/maximal-rectangle/description/)

### on Tree / Graph

#### Medium

##### [House robber III](https://leetcode.com/problems/house-robber-iii/description/)

##### [Unique binary search trees II](https://leetcode.com/problems/unique-binary-search-trees-ii/description/)

##### [Number of ways to arrive at destination](https://leetcode.com/problems/number-of-ways-to-arrive-at-destination/description/)

#### Hard

##### [Binary tree cameras](https://leetcode.com/problems/binary-tree-cameras/description/)

##### [Sum of distances in tree](https://leetcode.com/problems/sum-of-distances-in-tree/description/)

### on Bitmask

#### Medium

##### [Minimum number of work sessions to finish the tasks](https://leetcode.com/problems/minimum-number-of-work-sessions-to-finish-the-tasks/description/)

##### [Fair distribution of cookies](https://leetcode.com/problems/fair-distribution-of-cookies/description/)

#### Hard

##### [Shortest path visiting all nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/description/)

##### [Find the shortest superstring](https://leetcode.com/problems/find-the-shortest-superstring/description/)

##### [Maximize score after N operations](https://leetcode.com/problems/maximize-score-after-n-operations/description/)

##### [Maximum students taking exam](https://leetcode.com/problems/maximum-students-taking-exam/description/)

##### [Number of ways to wear different hats to each other	](https://leetcode.com/problems/number-of-ways-to-wear-different-hats-to-each-other/description/)

### on Digit

#### Medium

##### [Count numbers with unique digits](https://leetcode.com/problems/count-numbers-with-unique-digits/description/)

##### [Sequential digits](https://leetcode.com/problems/sequential-digits/description/)

#### Hard

##### [Number of digit one](https://leetcode.com/problems/number-of-digit-one/description/)

##### [Numbers at most N given digit set](https://leetcode.com/problems/numbers-at-most-n-given-digit-set/description/)

##### [Count the number of powerful integers](https://leetcode.com/problems/count-the-number-of-powerful-integers/description/)

### on Probability

#### Medium

##### [Knight probability in chessboard](https://leetcode.com/problems/knight-probability-in-chessboard/description/)

##### [Soup servings](https://leetcode.com/problems/soup-servings/description/)

##### [New 21 game](https://leetcode.com/problems/new-21-game/description/)

### on Multi-dimensional states

#### Medium

##### [Count the number of inversions](https://leetcode.com/problems/count-the-number-of-inversions/)

## Greedy

### Easy

#### [Assign cookies](https://leetcode.com/problems/assign-cookies/description/)

#### [Minimum number of coins](https://www.geeksforgeeks.org/problems/-minimum-number-of-coins4426/1)

#### [Lemonade change](https://leetcode.com/problems/lemonade-change/description/)

#### [N meetings in one room](https://www.geeksforgeeks.org/problems/n-meetings-in-one-room-1587115620/1)

#### [Page faults in LRU](https://www.geeksforgeeks.org/problems/page-faults-in-lru5603/1)

### Medium

#### [Increasing triplet subsequence](https://leetcode.com/problems/increasing-triplet-subsequence/description/)

#### [Fractional knapsack](https://www.geeksforgeeks.org/problems/fractional-knapsack-1587115620/1)

#### [Jump game](https://leetcode.com/problems/jump-game/description/)

#### [Jump game II](https://leetcode.com/problems/jump-game-ii/description/)

#### [Minimum platforms](https://www.geeksforgeeks.org/problems/minimum-platforms-1587115620/1)

#### [Job sequencing problem](https://www.geeksforgeeks.org/problems/job-sequencing-problem-1587115620/1)

#### [Shortest job first](https://www.geeksforgeeks.org/problems/shortest-job-first/1)

#### [Gas station](https://leetcode.com/problems/gas-station/)

#### [Hands of straights](https://leetcode.com/problems/hand-of-straights/description/)

##### ⭐️

###### 🔴!

#### [Partition labels](https://leetcode.com/problems/partition-labels/)

#### [Valid paranthesis string](https://leetcode.com/problems/valid-parenthesis-string/description/)

#### [Minimum add to make parentheses valid](https://leetcode.com/problems/minimum-add-to-make-parentheses-valid/description/)

#### [Split array into consecutive subsequences](https://leetcode.com/problems/split-array-into-consecutive-subsequences/description/)

#### [Number of good ways to split a string](https://leetcode.com/problems/number-of-good-ways-to-split-a-string/description/)

### Hard

#### [Candy](https://leetcode.com/problems/candy/description/)

#### [Minimum cost to hire k workers](https://leetcode.com/problems/minimum-cost-to-hire-k-workers/description/)

#### [Minimum number of refueling stops](https://leetcode.com/problems/minimum-number-of-refueling-stops/description/)

#### [Reducing dishes](https://leetcode.com/problems/reducing-dishes/description/)

## Prefix Sum

### Easy

#### [Range Sum Query - Immutable](https://leetcode.com/problems/range-sum-query-immutable)

### Medium

#### [Range sum query 2D - immutable](https://leetcode.com/problems/range-sum-query-2d-immutable/description/)

#### [Product of array except self](https://leetcode.com/problems/product-of-array-except-self/)

#### [Product of last k numbers](https://leetcode.com/problems/product-of-the-last-k-numbers/description/)

#### [Longest subarray with sum ](https://www.geeksforgeeks.org/problems/longest-sub-array-with-sum-k0809/1)k

#### [Subarray sum equals k](https://leetcode.com/problems/subarray-sum-equals-k/description/)

#### [Subarray sum divisible by k](https://leetcode.com/problems/subarray-sums-divisible-by-k/description/)

#### [Continuous subarray sum](https://leetcode.com/problems/continuous-subarray-sum/description/)

#### [Contiguous array](https://leetcode.com/problems/contiguous-array/description/)

#### [Increment submatrices by one](https://leetcode.com/problems/increment-submatrices-by-one/description/)

#### [Count number of nice subarrays](https://leetcode.com/problems/count-number-of-nice-subarrays/description/)

#### [Maximum product subarray](https://leetcode.com/problems/maximum-product-subarray/)

## Kadane’s Algorithm

### Medium

#### [Maximum subarray](https://leetcode.com/problems/maximum-subarray/)

##### ⭐️

###### 🔴!

####### ✅

######## Iterate, accumulating sum; reset to zero if negative, and track the maximum at each step.

#### [Maximum sum circular subarray](https://leetcode.com/problems/maximum-sum-circular-subarray/description/)

#### [Maximum product subarray](https://leetcode.com/problems/maximum-product-subarray/description/)

#### [Best sightseeing pair](https://leetcode.com/problems/best-sightseeing-pair/description/)

## Bit Manipulation

### Easy

#### [Check k-th bit](https://www.geeksforgeeks.org/problems/check-whether-k-th-bit-is-set-or-not-1587115620/1)

#### [Odd or even](https://www.geeksforgeeks.org/problems/odd-or-even3618/1)

#### [Power of 2](https://www.geeksforgeeks.org/problems/power-of-2-1587115620/1)

#### [Counting bits](https://leetcode.com/problems/counting-bits/description/)

#### [Set the rightmost unset bit](https://www.geeksforgeeks.org/problems/set-the-rightmost-unset-bit4436/1)

#### [Swap two numbers](https://www.geeksforgeeks.org/problems/swap-two-numbers3844/1)

#### [Minimum bit flips to convert number](https://leetcode.com/problems/minimum-bit-flips-to-convert-number/description/)

#### [Single number](https://leetcode.com/problems/single-number/description/)

#### [Number of 1 bits](https://leetcode.com/problems/number-of-1-bits/description/)

#### [Reverse bits](https://leetcode.com/problems/reverse-bits/description/)

#### [Missing number](https://leetcode.com/problems/missing-number/description/)

#### [Find xor of numbers from L to R](https://www.geeksforgeeks.org/problems/find-xor-of-numbers-from-l-to-r/1)

### Medium

#### [Sum of two integers](https://leetcode.com/problems/sum-of-two-integers/description/)

#### [Reverse integer](https://leetcode.com/problems/reverse-integer/description/)

#### [Divide two integers](https://leetcode.com/problems/divide-two-integers/description/)

#### [Subsets](https://leetcode.com/problems/subsets/description/)

#### [Two odd occuring](https://www.geeksforgeeks.org/problems/two-numbers-with-odd-occurrences5846/1)

#### [Bitwise AND of numbers range](https://leetcode.com/problems/bitwise-and-of-numbers-range/description/)

#### [Single number III](https://leetcode.com/problems/single-number-iii/description/)

## K-Way Merge

### Hard

#### [Smallest range covering elements from k lists](https://leetcode.com/problems/smallest-range-covering-elements-from-k-lists/description/)

## Divide and Conquer

### Medium

#### [Convert sorted list to binary search tree](https://leetcode.com/problems/convert-sorted-list-to-binary-search-tree/description/)

#### [Construct quad tree](https://leetcode.com/problems/construct-quad-tree/description/)

#### [Maximum binary tree](https://leetcode.com/problems/maximum-binary-tree/description/)

### Hard

#### [Reverse pairs](https://leetcode.com/problems/reverse-pairs/)

## Tries

### Medium

#### [Implement Trie (prefix tree)](https://leetcode.com/problems/implement-trie-prefix-tree/description/)

#### [Longest valid word with all prefixes](https://www.geeksforgeeks.org/problems/longest-valid-word-with-all-prefixes/1)

#### [Count of distinct substrings](https://www.geeksforgeeks.org/problems/count-of-distinct-substrings/1)

#### [Bit’s basic operations](https://www.geeksforgeeks.org/problems/bits-basic-operations/1)

#### [Maximum xor of two numbers in an array](https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/description/)

#### [Design add and search words data structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/)

#### [Search suggestions system](https://leetcode.com/problems/search-suggestions-system/description/)

#### [Longest word in dictionary](https://leetcode.com/problems/longest-word-in-dictionary/description/)

### Hard

#### [Word search II](https://leetcode.com/problems/word-search-ii/)

#### [Maximum xor with an element from array](https://leetcode.com/problems/maximum-xor-with-an-element-from-array/description/)

#### [Longest common suffix queries](https://leetcode.com/problems/longest-common-suffix-queries/description/)

#### [Count prefix and suffix pairs II](https://leetcode.com/problems/count-prefix-and-suffix-pairs-ii/description/)

## Data structure design

### Medium

#### [Design browser history](https://leetcode.com/problems/design-browser-history/description/)

#### [Snapshot array](https://leetcode.com/problems/snapshot-array/description/)

#### [Design twitter](https://leetcode.com/problems/design-twitter/description/)

#### [Design a food rating system](https://leetcode.com/problems/design-a-food-rating-system/description/)

### Hard

#### [Maximum frequency stack](https://leetcode.com/problems/maximum-frequency-stack/description/)

## Maths and Geometry

### Easy

#### [Count digits](https://www.geeksforgeeks.org/problems/count-digits-1606889545/1)

#### [Palindrome number](https://leetcode.com/problems/palindrome-number/description/)

#### [Find greatest common divisor of array](https://leetcode.com/problems/find-greatest-common-divisor-of-array/description/)

#### [Armstrong numbers](https://www.geeksforgeeks.org/problems/armstrong-numbers2727/1)

#### [Happy number](https://leetcode.com/problems/happy-number)

##### ⭐️

###### 🔴!

#### [All divisors of a number](https://www.geeksforgeeks.org/problems/all-divisors-of-a-number/1)

#### [Prime number](https://www.geeksforgeeks.org/problems/prime-number2314/1)

#### [Plus one](https://leetcode.com/problems/plus-one/)

#### [Type of triangle](https://leetcode.com/problems/type-of-triangle/description/)

#### [Greatest common divisor of strings](https://leetcode.com/problems/greatest-common-divisor-of-strings/description/)

#### [Transpose matrix](https://leetcode.com/problems/transpose-matrix)

### Medium

#### [Prime factors](https://www.geeksforgeeks.org/problems/prime-factors5052/1)

#### [Count primes](https://leetcode.com/problems/count-primes/)

#### [Prime factorization using sieve](https://www.geeksforgeeks.org/problems/prime-factorization-using-sieve/1)

#### [All divisors of a number](https://www.geeksforgeeks.org/problems/all-divisors-of-a-number/1)

#### [Reverse integer](https://leetcode.com/problems/reverse-integer/description/)

#### [Pow(x, n)](https://leetcode.com/problems/powx-n/description/)

#### [Rotate image](https://leetcode.com/problems/rotate-image/)

#### [Spiral matrix](https://leetcode.com/problems/spiral-matrix/)

##### ⭐️

###### 🔴!

####### ✅

######## Iteratively traverse the matrix layer by layer in right, down, left, up order, adjusting boundaries each time.

#### [Set matrix zeroes](https://leetcode.com/problems/set-matrix-zeroes/)

#### [Multiply strings](https://leetcode.com/problems/multiply-strings/description/)

#### [Detect squares](https://leetcode.com/problems/detect-squares/description/)

#### [Factorial trailing zeroes](https://leetcode.com/problems/factorial-trailing-zeroes/description/)

#### [Valid square](https://leetcode.com/problems/valid-square/description/)

#### [Minimum area rectangle II](https://leetcode.com/problems/minimum-area-rectangle-ii/description/)

#### [Arithmetic subarrays](https://leetcode.com/problems/arithmetic-subarrays/description/)

#### [Largest number](https://leetcode.com/problems/largest-number/description/)

#### [Diagonal traverse](https://leetcode.com/problems/diagonal-traverse)

### Hard

#### [Max points on a line](https://leetcode.com/problems/max-points-on-a-line/description/)

#### [Count all valid pickup and delivery options](https://leetcode.com/problems/count-all-valid-pickup-and-delivery-options/description/)

#### [Minimize manhattan distances](https://leetcode.com/problems/minimize-manhattan-distances/description/)

## String matching

### Easy

#### [DI string match](https://leetcode.com/problems/di-string-match/description/)

### Medium

#### [Repeated string match](https://leetcode.com/problems/repeated-string-match/description/)

### Hard

#### [Shortest palindrome](https://leetcode.com/problems/shortest-palindrome/description/)

## Line sweep

### Easy

#### [Points that intersect with cars](https://leetcode.com/problems/points-that-intersect-with-cars/description/)

### Medium

#### [Car pooling](https://leetcode.com/problems/points-that-intersect-with-cars/description/)

#### [My calendar II](https://leetcode.com/problems/my-calendar-ii/description/)

### Hard

#### [Minimum interval to include each query](https://leetcode.com/problems/minimum-interval-to-include-each-query/description/)

#### [The skyline problem](https://leetcode.com/problems/the-skyline-problem/description/)

#### [Number of flowers in full bloom](https://leetcode.com/problems/number-of-flowers-in-full-bloom/description/)

## Suffix Array

### Hard

#### [Longest duplicate substring](https://leetcode.com/problems/longest-duplicate-substring/description/)