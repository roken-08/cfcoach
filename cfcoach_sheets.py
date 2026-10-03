"""Curated practice sheets: two LeetCode interview sheets in sheet order, and CP-31.

Each entry is (sheet section, Codeforces tags that section trains, LeetCode title slugs).
A "*" marks a mixed section: its problems are matched by their LeetCode topics instead.
NEETCODE: NeetCode 150, from github.com/dipjul/NeetCode-150.
STRIVER: the Striver A2Z problems that exist on LeetCode, from
github.com/Codensity30/Strivers-A2Z-DSA-Sheet (its other problems are GeeksforGeeks-only).
"""

NEETCODE = [
    ("Arrays & Hashing", "hashing", """
contains-duplicate valid-anagram two-sum group-anagrams top-k-frequent-elements
product-of-array-except-self valid-sudoku encode-and-decode-strings
longest-consecutive-sequence
"""),
    ("Two Pointers", "two pointers", """
valid-palindrome two-sum-ii-input-array-is-sorted 3sum container-with-most-water
trapping-rain-water
"""),
    ("Sliding Window", "two pointers", """
best-time-to-buy-and-sell-stock longest-substring-without-repeating-characters
longest-repeating-character-replacement permutation-in-string minimum-window-substring
sliding-window-maximum
"""),
    ("Stack", "data structures", """
valid-parentheses min-stack evaluate-reverse-polish-notation generate-parentheses
daily-temperatures car-fleet largest-rectangle-in-histogram
"""),
    ("Binary Search", "binary search", """
binary-search search-a-2d-matrix koko-eating-bananas search-in-rotated-sorted-array
find-minimum-in-rotated-sorted-array time-based-key-value-store median-of-two-sorted-arrays
"""),
    ("Linked List", "", """
reverse-linked-list merge-two-sorted-lists reorder-list remove-nth-node-from-end-of-list
copy-list-with-random-pointer add-two-numbers linked-list-cycle find-the-duplicate-number
lru-cache merge-k-sorted-lists reverse-nodes-in-k-group
"""),
    ("Trees", "trees,dfs and similar", """
invert-binary-tree maximum-depth-of-binary-tree diameter-of-binary-tree balanced-binary-tree
same-tree subtree-of-another-tree lowest-common-ancestor-of-a-binary-search-tree
binary-tree-level-order-traversal binary-tree-right-side-view
count-good-nodes-in-binary-tree validate-binary-search-tree kth-smallest-element-in-a-bst
construct-binary-tree-from-preorder-and-inorder-traversal binary-tree-maximum-path-sum
serialize-and-deserialize-binary-tree
"""),
    ("Tries", "strings,data structures", """
implement-trie-prefix-tree design-add-and-search-words-data-structure word-search-ii
"""),
    ("Heap / PriorityQueue", "data structures", """
kth-largest-element-in-a-stream last-stone-weight k-closest-points-to-origin
kth-largest-element-in-an-array task-scheduler design-twitter find-median-from-data-stream
"""),
    ("Backtracking", "brute force", """
subsets combination-sum permutations subsets-ii combination-sum-ii word-search
palindrome-partitioning letter-combinations-of-a-phone-number n-queens
"""),
    ("Graphs", "graphs,dfs and similar", """
number-of-islands clone-graph max-area-of-island pacific-atlantic-water-flow
surrounded-regions rotting-oranges walls-and-gates course-schedule course-schedule-ii
redundant-connection number-of-connected-components-in-an-undirected-graph graph-valid-tree
word-ladder
"""),
    ("Advanced Graphs", "graphs,shortest paths", """
reconstruct-itinerary min-cost-to-connect-all-points network-delay-time swim-in-rising-water
alien-dictionary cheapest-flights-within-k-stops
"""),
    ("1-D Dynamic Programming", "dp", """
climbing-stairs min-cost-climbing-stairs house-robber house-robber-ii
longest-palindromic-substring palindromic-substrings decode-ways coin-change
maximum-product-subarray word-break longest-increasing-subsequence
partition-equal-subset-sum
"""),
    ("2-D Dynamic Programming", "dp", """
unique-paths longest-common-subsequence best-time-to-buy-and-sell-stock-with-cooldown
coin-change-ii target-sum interleaving-string longest-increasing-path-in-a-matrix
distinct-subsequences edit-distance burst-balloons regular-expression-matching
"""),
    ("Greedy", "greedy", """
maximum-subarray jump-game jump-game-ii gas-station hand-of-straights
merge-triplets-to-form-target-triplet partition-labels valid-parenthesis-string
"""),
    ("Intervals", "sortings,greedy", """
insert-interval merge-intervals non-overlapping-intervals meeting-rooms meeting-rooms-ii
minimum-interval-to-include-each-query
"""),
    ("Math & Geometry", "math,implementation", """
rotate-image spiral-matrix set-matrix-zeroes happy-number plus-one powx-n multiply-strings
detect-squares
"""),
    ("Bit Manipulation", "bitmasks", """
single-number number-of-1-bits counting-bits reverse-bits missing-number sum-of-two-integers
reverse-integer
"""),
]

STRIVER = [
    ("Arrays", "*", """
check-if-array-is-sorted-and-rotated remove-duplicates-from-sorted-array rotate-array
move-zeroes missing-number max-consecutive-ones single-number two-sum sort-colors
majority-element maximum-subarray subarray-sum-equals-k best-time-to-buy-and-sell-stock
rearrange-array-elements-by-sign next-permutation longest-consecutive-sequence
set-matrix-zeroes rotate-image spiral-matrix pascals-triangle majority-element-ii 3sum 4sum
merge-intervals merge-sorted-array set-mismatch reverse-pairs maximum-product-subarray
"""),
    ("Binary Search", "binary search", """
binary-search search-insert-position find-first-and-last-position-of-element-in-sorted-array
find-peak-element search-in-rotated-sorted-array search-in-rotated-sorted-array-ii
find-minimum-in-rotated-sorted-array single-element-in-a-sorted-array search-a-2d-matrix
search-a-2d-matrix-ii find-a-peak-element-ii sqrtx koko-eating-bananas
minimum-number-of-days-to-make-m-bouquets find-the-smallest-divisor-given-a-threshold
capacity-to-ship-packages-within-d-days magnetic-force-between-two-balls
split-array-largest-sum kth-missing-positive-number median-of-two-sorted-arrays
"""),
    ("Strings", "strings", """
remove-outermost-parentheses reverse-words-in-a-string largest-odd-number-in-string
longest-common-prefix isomorphic-strings rotate-string valid-anagram
sort-characters-by-frequency maximum-nesting-depth-of-the-parentheses roman-to-integer
string-to-integer-atoi longest-palindromic-substring sum-of-beauty-of-all-substrings
"""),
    ("Linked List", "", """
middle-of-the-linked-list reverse-linked-list linked-list-cycle linked-list-cycle-ii
palindrome-linked-list odd-even-linked-list remove-nth-node-from-end-of-list
delete-the-middle-node-of-a-linked-list sort-list add-two-numbers reverse-nodes-in-k-group
rotate-list copy-list-with-random-pointer
"""),
    ("Recursion", "brute force", """
count-good-numbers generate-parentheses subsets-ii combination-sum combination-sum-ii
combination-sum-iii letter-combinations-of-a-phone-number palindrome-partitioning
word-search n-queens word-break sudoku-solver
"""),
    ("Bit Manipulation", "bitmasks", """
power-of-two divide-two-integers minimum-bit-flips-to-convert-number
"""),
    ("Maths", "math,number theory", """
count-primes powx-n
"""),
    ("Stack and Queues", "data structures", """
implement-stack-using-queues implement-queue-using-stacks valid-parentheses min-stack
next-greater-element-i next-greater-element-ii trapping-rain-water sum-of-subarray-minimums
sum-of-subarray-ranges remove-k-digits largest-rectangle-in-histogram maximal-rectangle
asteroid-collision sliding-window-maximum online-stock-span lru-cache
"""),
    ("Sliding Window", "two pointers", """
longest-substring-without-repeating-characters max-consecutive-ones-iii fruit-into-baskets
longest-repeating-character-replacement binary-subarrays-with-sum
count-number-of-nice-subarrays number-of-substrings-containing-all-three-characters
maximum-points-you-can-obtain-from-cards subarrays-with-k-different-integers
minimum-window-substring
"""),
    ("Heaps", "data structures", """
kth-largest-element-in-an-array merge-k-sorted-lists rank-transform-of-an-array
task-scheduler divide-array-in-sets-of-k-consecutive-numbers design-twitter
kth-largest-element-in-a-stream find-median-from-data-stream top-k-frequent-elements
"""),
    ("Greedy Approach", "greedy", """
assign-cookies lemonade-change valid-parenthesis-string jump-game jump-game-ii candy
insert-interval non-overlapping-intervals
"""),
    ("Binary Trees", "trees,dfs and similar", """
binary-tree-preorder-traversal binary-tree-inorder-traversal binary-tree-postorder-traversal
binary-tree-level-order-traversal maximum-depth-of-binary-tree balanced-binary-tree
diameter-of-binary-tree binary-tree-maximum-path-sum same-tree
binary-tree-zigzag-level-order-traversal vertical-order-traversal-of-a-binary-tree
binary-tree-right-side-view symmetric-tree lowest-common-ancestor-of-a-binary-tree
maximum-width-of-binary-tree all-nodes-distance-k-in-binary-tree
amount-of-time-for-binary-tree-to-be-infected count-complete-tree-nodes
construct-binary-tree-from-preorder-and-inorder-traversal
construct-binary-tree-from-inorder-and-postorder-traversal
flatten-binary-tree-to-linked-list serialize-and-deserialize-binary-tree
"""),
    ("Binary Search Trees", "trees", """
search-in-a-binary-search-tree insert-into-a-binary-search-tree delete-node-in-a-bst
kth-smallest-element-in-a-bst validate-binary-search-tree
lowest-common-ancestor-of-a-binary-search-tree
construct-binary-search-tree-from-preorder-traversal binary-search-tree-iterator
two-sum-iv-input-is-a-bst recover-binary-search-tree
"""),
    ("Graphs", "graphs,dfs and similar", """
number-of-provinces rotting-oranges flood-fill 01-matrix surrounded-regions
number-of-enclaves word-ladder is-graph-bipartite course-schedule course-schedule-ii
find-eventual-safe-states
"""),
    ("Graphs: Shortest Paths", "graphs,shortest paths", """
shortest-path-in-binary-matrix path-with-minimum-effort cheapest-flights-within-k-stops
network-delay-time
find-the-city-with-the-smallest-number-of-neighbors-at-a-threshold-distance
number-of-ways-to-arrive-at-destination
"""),
    ("Graphs: MST and DSU", "graphs,dsu", """
number-of-operations-to-make-network-connected most-stones-removed-with-same-row-or-column
accounts-merge making-a-large-island swim-in-rising-water
"""),
    ("Graphs", "graphs,dfs and similar", """
critical-connections-in-a-network
"""),
    ("Dynamic Programming", "dp", """
fibonacci-number climbing-stairs house-robber house-robber-ii unique-paths unique-paths-ii
minimum-path-sum triangle minimum-falling-path-sum partition-equal-subset-sum coin-change
target-sum coin-change-ii longest-common-subsequence longest-palindromic-subsequence
minimum-insertion-steps-to-make-a-string-palindrome delete-operation-for-two-strings
shortest-common-supersequence distinct-subsequences wildcard-matching
best-time-to-buy-and-sell-stock-ii best-time-to-buy-and-sell-stock-iii
best-time-to-buy-and-sell-stock-iv best-time-to-buy-and-sell-stock-with-cooldown
best-time-to-buy-and-sell-stock-with-transaction-fee longest-increasing-subsequence
largest-divisible-subset number-of-longest-increasing-subsequence
minimum-cost-to-cut-a-stick burst-balloons palindrome-partitioning-ii
partition-array-for-maximum-sum maximal-square count-square-submatrices-with-all-ones
"""),
    ("Tries", "strings,data structures", """
implement-trie-prefix-tree maximum-xor-of-two-numbers-in-an-array
"""),
    ("Strings (Hard)", "strings", """
minimum-add-to-make-parentheses-valid count-and-say
find-the-index-of-the-first-occurrence-in-a-string longest-happy-prefix shortest-palindrome
"""),
]

# CP-31 by TLE Eliminators: 31 chosen Codeforces problems for every rating from 800 to
# 1900, as Codeforces problem ids (a problem that ran in two parallel contests has both ids).
# Recovered from github.com/virajchandra51/TLE_CP_31 and
# github.com/Tejas-Santosh-Nalawade/CP-31-Sheet, which agree on every position; each name was
# matched to a Codeforces problem of exactly that rating.
CP31 = frozenset("""
1903A 1901A 1900A 1899A 1896A 1890A 1881A 1878A 1877A 1873C 1866A 1862B 2164A 1859A 1858A
1857A 2191A 1853A 1845A 1837A 1834A 1831A 1829B 1061A 1814A 1806A 1805A 1791C 1789A 1788A
1783A 1777A 1766A 1761A 1904A 1883B 1878C 1875A 1869A 1855B 1850D 1837B 1828B 1807D 1794B
1726A 1696B 1679A 1675B 1666D 1665B 1624B 1607B 1606A 1593B 1582B 1559A 1543A 1537B 1475A
1471A 1440B 1380A 1373B 1374B 1913B 1883C 1876A 1859B 1849B 1840C 1831B 1791D 1765M 1744C
1725B 1715B 1704B 1691B 1690D 1659A 1632B 1620B 1614B 1567B 1506C 1485A 1474B 1447B 1438B
1418A 1411B 1374C 1362A 1312B 1155A 1917B 1914C 1904B 1899C 1899B 1891B 1873E 1869B 1850E
1842B 1832B 1946B 1827A 1826B 1821B 1820B 1807G2 1797B 1791G1 1791E 1780B 1742D 1731B 1708B
1682B 1673B 1669F 1656B 1631B 1618C 1610B 1511C 1914D 1909B 1872D 1857C 1848B 1832C 1808B
1793C 1790D 1742E 1734C 1729D 1704C 1703E 1692E 1679B 1671C 1635C 1154B 1594C 1582C 1541B
1539C 1536B 1527B1 1520D 1514B 1504B 1497B 1487B 1433D 1420B 1931D 1927D 1915E 1881D 1879C
1857D 1846E1 1794C 1775B 1703F 1676G 1669H 1612C 1601A 1561C 1498B 1470A 1459B 1372B 1366B
1364B 1360D 1294C 1285B 1237B 1178B 1119B 1077C 862B 808B 665C 1931E 1919C 1907D 1904C
1883G1 1878E 1837D 1830A 1771B 1759D 1714E 1701C 1692G 1648A 1634B 1520E 1519C 1513B 1475C
1374D 1362C 1350B 1320A 1215B 1195C 1183D 1167C 1167B 1143C 1110B 414B 1915F 1891C 1881E
1872E 1795C 1776L 1673C 1659C 1646C 1516B 1486B 1466D 1418C 1416A 1404A 1338A 1332C 1325C
1323B 1201B 1139C 1133D 1106D 1101C 1084C 982C 976C 960B 891A 845C 276C 1920C 1907E 1886C
1856C 1843E 1833E 1829G 1798D 1795D 1781C 1778C 1775C 1741E 1730B 1702E 1698D 1660D 1633D
1610C 1555D 1537E1 1528A 1498C 1475E 1458A 1407C 1398C 1389B 1349A 1336A 1305C 2050F 2041D
2018C 2006A 1999G2 1983D 1982D 1948D 1931F 1893B 1879D 1833F 1829H 1826D 1822G1 1792D 1777C
1760G 1735D 1731C 1715C 1709D 1695C 1692H 1690F 1625C 1598D 1594D 1557C 1528B 1516C 2022C
2014E 1974E 1935D 1915G 1912K 1824B1 1805D 1775D 1768D 1732C1 1725M 1709C 1691D 1517D 1509C
1491D 1468J 1466E 1462F 1446B 1442B 1437C 1401D 1396B 1355C 1338B 1335E2 1290B 1286B 1283D
2044F 2042D 2036F 2014H 2009G1 2001D 1994D 1992F 1986F 1957D 1950G 1932F 1925D 1918D 1912A
1906E 1902E 1898D 1882D 1842D 1819B 1817B 1799D1 1794D 1777D 1759G 1747D 1744E2 1739D 1715D
1700D
""".split())
