# Python Q&A Assistant - Evaluation Results

This document presents the evaluation of the Python Q&A Assistant RAG Pipeline on the **Golden Dataset** (8 diverse queries representing typical user questions).

## Executive Summary

- **Total Queries Tested**: 8
- **Average Response Latency**: 1155.11 ms
- **Average Faithfulness Score (LLM-as-a-Judge)**: 0.94 / 1.00
- **Average Answer Relevance Score (LLM-as-a-Judge)**: 1.00 / 1.00

---

## Evaluation Metric Definitions

1. **Faithfulness (Groundedness)**: Checks if the generated answer is strictly supported by the retrieved context. A score of `1.0` indicates zero hallucination.
2. **Answer Relevance**: Measures how well the generated answer addresses the question and aligns with the ground-truth standard.
3. **Self-RAG Guardrails**: Active in the production API pipeline; intentionally skipped during offline evaluation to conserve API quota.

---

## Detailed Test Logs

### Query 1: How do I merge two dictionaries in Python?

**Ground Truth Standard:**  
*Use the | operator in Python 3.9+ (e.g. dict1 | dict2) or dictionary unpacking ** in Python 3.5+ (e.g. {**dict1, **dict2}).*

**Generated Answer:**  
```
You can combine two dictionaries by creating a new one that contains the keys‑and‑values from both sources.  
The syntax you choose depends on the Python version you are using.

### Python 3.9 and newer – merge operator `|`

```python
# Example dictionaries
x = {'a': 1, 'b': 2}
y = {'b': 3, 'c': 4}

# Merge, with values from the right‑hand dict overriding duplicates
z = x | y
print(z)          # {'a': 1, 'b': 3, 'c': 4}
```

The `|` operator returns a **new** dictionary; the original `x` and `y` remain unchanged. Keys that appear in both dictionaries are taken from the right‑hand side (`y` in the example)【Source 1】.

### Python 3.5 to 3.8 – dictionary unpacking `**`

```python
x = {'a': 1, 'b': 2}
y = {'b': 3, 'c': 4}

# Unpack both dicts into a new literal
z = {**x, **y}
print(z)          # {'a': 1, 'b': 3, 'c': 4}
```

The `{**x, **y}` syntax also creates a new dictionary, applying the same left‑to‑right overriding rule【Source 1】.

Both approaches give you a merged dictionary without mutating the originals. Choose the operator that matches the minimum Python version you need to support.
```

**Metrics:**
- **Response Latency**: 917.54 ms
- **Faithfulness**: 1.00/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The generated answer accurately restates the two merging methods (| operator for Python 3.9+ and ** unpacking for Python 3.5-3.8) that are present in the retrieved context, without adding any unsupported or fabricated details. It directly answers the user’s question about merging dictionaries and aligns perfectly with the ground truth reference, making it both faithful to the source and fully relevant.

---
### Query 2: What is the difference between append and extend on a list?

**Ground Truth Standard:**  
*append() adds the argument as a single element to the end of the list. extend() iterates over the argument and adds each element to the list.*

**Generated Answer:**  
```
`list.append` and `list.extend` both add data to a list, but they do it in different ways:

| Method | What it does | Resulting list length |
|--------|--------------|-----------------------|
| **`append(item)`** | Inserts the *entire* argument as a **single element** at the end of the list. | Increases by **one**. |
| **`extend(iterable)`** | Iterates over the argument and adds each element individually to the list. | Increases by the number of elements in the iterable. |

**Example**

```python
# Using append
x = [1, 2]
x.append([3, 4])      # x becomes [1, 2, [3, 4]]
# The list [3, 4] is added as one element (a nested list).

# Using extend
y = [1, 2]
y.extend([3, 4])      # y becomes [1, 2, 3, 4]
# Each element of the iterable [3, 4] is added separately.
```

So, `append` is appropriate when you want to add a single object (even if that object is itself a list), while `extend` is used to concatenate the contents of another iterable onto the existing list.  

Source: [Source 1]
```

**Metrics:**
- **Response Latency**: 1092.79 ms
- **Faithfulness**: 0.80/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The answer correctly explains the difference between list.append and list.extend, matching the ground truth and using examples consistent with the retrieved context. However, it adds an unsupported citation ('Source: [Source 1]') that was not present in the context, indicating a slight fabrication, which lowers the faithfulness score.

---
### Query 3: How do I read a file line by line in Python into a list?

**Ground Truth Standard:**  
*Open the file with a context manager (with open) and use a list comprehension with line.strip() to read it line-by-line.*

**Generated Answer:**  
```
You can read a text file line‑by‑line and collect the lines into a list by iterating over the file object inside a `with` block.  
A list comprehension (see [Source 2]) makes the code concise, and `line.strip()` removes the trailing newline and any surrounding whitespace.

```python
# Read the whole file into a list of stripped lines
with open('file.txt', 'r', encoding='utf-8') as f:
    lines = [line.strip() for line in f]
```

- `open(..., 'r')` opens the file for reading.  
- The `with` statement ensures the file is closed automatically.  
- Iterating over `f` yields one line at a time, which is memory‑efficient.  
- The list comprehension builds `lines`, a list where each element is a line without the newline character (`\n`) or extra spaces.

This approach follows the standard, memory‑efficient pattern described in the Stack Overflow answer [Source 1].
```

**Metrics:**
- **Response Latency**: 920.98 ms
- **Faithfulness**: 1.00/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The generated answer accurately restates the method from the provided context—using a with open block and a list comprehension with line.strip()—without adding any unsupported information. It directly answers the user’s question about reading a file line by line into a list, matching the ground truth.

---
### Query 4: How do I convert a string to datetime in Python?

**Ground Truth Standard:**  
*Use the datetime.strptime(date_string, format_string) function from the datetime module.*

**Generated Answer:**  
```
You can parse a date‑time string with the standard library’s **`datetime.strptime`** function.  
Provide the string and a format string that matches its layout:

```python
from datetime import datetime

date_string = '2023-10-27 15:30:00'   # the string you want to convert
format_str = '%Y-%m-%d %H:%M:%S'      # format that matches the string

dt_object = datetime.strptime(date_string, format_str)

print(dt_object)          # 2023-10-27 15:30:00
print(type(dt_object))    # <class 'datetime.datetime'>
```

- `datetime.strptime()` parses the string according to the `format_str`.
- The format codes (`%Y`, `%m`, `%d`, `%H`, `%M`, `%S`) correspond to year, month, day, hour, minute, and second respectively.

This approach works for any pattern as long as you supply the correct format string. [Source 1]
```

**Metrics:**
- **Response Latency**: 1166.01 ms
- **Faithfulness**: 1.00/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The generated answer accurately restates the method from the retrieved context (datetime.strptime) without adding any unsupported information, and it directly answers the user’s query about converting a string to a datetime object, matching the ground truth.

---
### Query 5: What does the yield keyword do in Python?

**Ground Truth Standard:**  
*yield is used in generator functions. It pauses function execution and returns a value to the caller, retaining the function state for subsequent iterations.*

**Generated Answer:**  
```
`yield` turns a normal function into a **generator function**.  
When the function is called it does **not** run immediately; instead it returns a generator object.  
Iterating over that generator (e.g., in a `for` loop or by calling `next()`) starts execution until the first `yield` statement. At that point the function **pauses**, returns the yielded value to the caller, and remembers its local state so that the next iteration can resume right after the `yield`.

```python
def my_generator():
    yield 1          # pause here, output 1
    yield 2          # pause here, output 2

gen = my_generator()   # returns a generator, no code runs yet
print(next(gen))        # prints 1
print(next(gen))        # prints 2
# next(gen) would raise StopIteration
```

Thus, `yield` works like `return` but produces a lazy sequence of values, allowing the function to maintain its execution context between yields. [Source 1]
```

**Metrics:**
- **Response Latency**: 874.86 ms
- **Faithfulness**: 0.90/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The generated answer correctly explains that `yield` turns a function into a generator, that the function returns a generator object, and that execution pauses at each `yield` while preserving state—exactly matching the retrieved context and ground‑truth. It adds a minor detail about `StopIteration` that was not present in the provided context; while the detail is accurate, it is not sourced from the context, so the answer is not perfectly faithful. The answer is fully relevant to the user’s question.

---
### Query 6: How do I check if a list is empty in Python?

**Ground Truth Standard:**  
*The PEP 8 recommended way is to check the list's truthiness directly: if not my_list, because empty collections evaluate to False.*

**Generated Answer:**  
```
According to the provided context, the most Pythonic way to check if a list is empty is to check the list's truthiness directly. This is because empty collections are considered "falsy" in Python, and this approach is recommended by PEP 8 [Source 1].

Here is the recommended code snippet:

```python
my_list = []
if not my_list:
    print('List is empty!')
```

You should avoid comparing the length using `len(my_list) == 0` or comparing with list literals like `my_list == []` [Source 1].
```

**Metrics:**
- **Response Latency**: 2168.28 ms
- **Faithfulness**: 1.00/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The generated answer restates exactly the information provided in the retrieved context: it advises checking the list's truthiness (if not my_list) as the Pythonic, PEP 8‑recommended method, includes the same code snippet, and warns against using len() or comparing to [] as the context does. No additional or fabricated details are introduced, so the answer is fully faithful to the source. It also directly answers the user’s question about checking for an empty list, matching the ground truth, thus it is fully relevant.

---
### Query 7: How do I create a list compression / list comprehension in Python?

**Ground Truth Standard:**  
*Use the bracket syntax with an expression and loop: [expression for item in iterable if condition].*

**Generated Answer:**  
```
List comprehensions are a compact way to build new lists from existing iterables.  
The general form is:

```python
[ expression for item in iterable if condition ]
```

- **`expression`** – what you want each element of the new list to be (often a transformation of `item`).  
- **`item`** – each element taken from the **`iterable`** (e.g., a `range`, a list, a file object, etc.).  
- **`if condition`** – optional filter; only items for which the condition is true are included.

**Example – squares of even numbers from 0‑9**

```python
squares = [x**2 for x in range(10) if x % 2 == 0]
print(squares)   # Output: [0, 4, 16, 36, 64]
```

In this example:

- `range(10)` supplies the numbers 0‑9.  
- `x % 2 == 0` filters to keep only even numbers.  
- `x**2` computes the square for each kept `x`.

You can omit the `if` clause when you want to include every item:

```python
cubes = [x**3 for x in range(5)]
# cubes: [0, 1, 8, 27, 64]
```

List comprehensions can also be nested or used with more complex expressions, but the basic pattern above covers most everyday needs.  

*Source: [Source 1]*
```

**Metrics:**
- **Response Latency**: 1271.02 ms
- **Faithfulness**: 0.90/1.0
- **Answer Relevance**: 1.00/1.0
- **Judge Review**: The generated answer correctly restates the list comprehension syntax and example found in the retrieved context, directly answering the user query. It adds some extra, generally true commentary (e.g., about nesting) that is not present in the source but does not contradict it, so the answer is mostly faithful with minor unfounded elaboration, resulting in a high but not perfect faithfulness score. The relevance to the query is spot on, matching the ground truth.

---
### Query 8: How to write a decorator in Python?

**Ground Truth Standard:**  
*A decorator is a function that takes another function, wraps it to extend its behavior, and returns the wrapper function.*

**Generated Answer:**  
```
A decorator is simply a higher‑order function: it receives another function, adds some behavior, and returns a new callable (often the original function wrapped in another function).  

Here’s the minimal pattern:

```python
def my_decorator(func):
    """Wrap *func* with extra behavior."""
    def wrapper(*args, **kwargs):
        # Code executed **before** the original function
        print('Before function execution')

        # Call the original function and capture its result
        result = func(*args, **kwargs)

        # Code executed **after** the original function
        print('After function execution')
        return result
    return wrapper
```

You apply the decorator with the `@` syntax (or manually by calling `my_decorator`):

```python
@my_decorator
def say_hello():
    print('Hello!')

# Equivalent manual usage:
# say_hello = my_decorator(say_hello)

say_hello()
```

Output:

```
Before function execution
Hello!
After function execution
```

**Key points**

1. **`my_decorator`** takes a function (`func`) as its argument.  
2. Inside it defines **`wrapper`**, which forwards any positional (`*args`) and keyword (`**kwargs`) arguments to `func`.  
3. The wrapper can run code before and after the call to `func`, then returns whatever `func` returns.  
4. The decorator returns the `wrapper` function, which replaces the original function when the `@my_decorator` syntax is used.

This pattern works for any callable you want to augment.  (Source: [Source 1])
```

**Metrics:**
- **Response Latency**: 829.37 ms
- **Faithfulness**: 0.95/1.0
- **Answer Relevance**: 0.98/1.0
- **Judge Review**: The generated answer accurately restates the decorator definition and provides the same example code as the retrieved context, fully covering the ground truth. It adds some explanatory text and a generic source citation, which are not present in the source but do not introduce incorrect information. Thus, the answer is highly faithful and directly relevant to the user query.

---
