# Phase 2: Raw SQL Results

Revalidated on September 17, 2026 against the 30,006-row PostgreSQL database.
Every result below was produced by the executable SQL in `query_data.py`.

## Question 1

How many entries are from applicants who applied for Fall 2026?

**Result:** Fall 2026 applicant count: 29,586

## Question 2

Among entries that provide a nationality classification, what percentage are
international students?

**Result:** Percent international: 46.34%

The denominator excludes only missing and blank classifications. American and
Other entries remain in the denominator but not the numerator, as required.

## Question 3

What are the average GPA, GRE Quantitative, GRE Verbal, and GRE Analytical
Writing scores among applicants who provide each metric?

**Results:**

- Average GPA: 3.80
- Average GRE Quantitative: 260.47
- Average GRE Verbal: 161.53
- Average GRE Analytical Writing: 8.34

Each `AVG` operates on its own column, so a missing value in one metric does
not exclude a supplied value in another metric. The relatively high GRE
Quantitative and Analytical Writing averages reflect the values actually
stored from the anonymous, self-reported source. The query does not silently
remove unusual values or impose a score range not specified by the assignment.

## Question 4

What is the average GPA of American applicants who applied for Fall 2026?

**Result:** Average GPA, American Fall 2026 applicants: 3.79

## Question 5

What percentage of Fall 2025 entries are acceptances?

**Result:** Fall 2025 acceptance percentage: 47.92%

## Question 6

What is the average GPA of accepted applicants who applied for Fall 2026?

**Result:** Average GPA, accepted Fall 2026 applicants: 3.79

## Question 7

How many entries are from applicants who applied to Johns Hopkins University
for a master's degree in Computer Science?

**Result:** JHU Computer Science master's applicant count: 8

Source-record inspection confirmed that all eight matches have the original
program value `Computer Science, Johns Hopkins University` and the original
degree value `Masters`.

## Question 8

How many Fall 2026 entries are acceptances from applicants applying for a PhD
in Computer Science at Georgetown, MIT, Stanford, or Carnegie Mellon using the
original program field?

**Result:** Original-field count: 28

## Question 9

Repeat Question 8 using the LLM-generated program and university fields, and
compare the counts.

**Results:**

- Original-field count: 28
- LLM-field count: 28
- Difference: +0

The two queries matched the same 28 GradCafe URLs. In this subset, the original
combined program strings already used recognizable university and Computer
Science names, and the LLM-generated fields standardized them without changing
which records qualified.

## Question 10 - Original Question

For Fall 2026, what are the applicant counts and acceptance percentages for
American and international entries?

**Results:**

- American: 15,449 entries, 38.53% accepted (5,952 acceptances)
- International: 13,499 entries, 34.59% accepted (4,669 acceptances)

The SQL filters to Fall 2026 and the two specified classifications, groups by
classification, counts all entries in each group, and divides accepted entries
by the corresponding group count. The result describes entries in this
self-selected dataset and should not be interpreted as a population-level
admission-rate comparison.

## Question 11 - Original Question

Which five LLM-standardized universities have the most Fall 2026 entries, and
what percentage of each university's entries are acceptances?

**Results:**

1. Stanford University: 718 entries, 19.08% accepted (137 acceptances)
2. University of California, Berkeley: 615 entries, 25.20% accepted (155
   acceptances)
3. Yale University: 573 entries, 14.14% accepted (81 acceptances)
4. Princeton University: 556 entries, 20.86% accepted (116 acceptances)
5. University of Washington: 547 entries, 27.97% accepted (153 acceptances)

The SQL filters to Fall 2026, removes missing university names, groups the
standardized university values, and orders the groups by entry count before
selecting the top five. Each percentage uses that university's total displayed
entry count as its denominator.
