# Default high-quality Stack Overflow Python Questions and Answers
# Used for instant, zero-setup out-of-the-box system demo and testing.

DEFAULT_QA_DATA = [
    {
        "id": 1,
        "text": (
            "Question: How do I merge two dictionaries in Python? (Python 3.5+ and 3.9+ syntax)\n\n"
            "Answer:\n"
            "For Python 3.9 and above, you can use the merge operator `|`:\n"
            "```python\nx = {'a': 1, 'b': 2}\ny = {'b': 3, 'c': 4}\nz = x | y\n# z is {'a': 1, 'b': 3, 'c': 4}\n```\n"
            "For Python 3.5 to 3.8, you can use dictionary unpacking `**`:\n"
            "```python\nz = {**x, **y}\n```\n"
            "Both methods create a new dictionary and override keys from left to right."
        ),
        "metadata": {
            "title": "How do I merge two dictionaries in Python?",
            "score": 25000,
            "url": "https://stackoverflow.com/questions/38987/how-do-i-merge-two-dictionaries-in-python"
        }
    },
    {
        "id": 2,
        "text": (
            "Question: What is the difference between list.append() and list.extend()?\n\n"
            "Answer:\n"
            "`append()` adds its argument as a single element to the end of a list. The length of the list increases by one.\n"
            "```python\nx = [1, 2]\nx.append([3, 4])  # x is now [1, 2, [3, 4]]\n```\n"
            "`extend()` iterates over its argument adding each element to the list, extending the list.\n"
            "```python\nx = [1, 2]\nx.extend([3, 4])  # x is now [1, 2, 3, 4]\n```"
        ),
        "metadata": {
            "title": "What is the difference between list.append and list.extend?",
            "score": 18500,
            "url": "https://stackoverflow.com/questions/252703/what-is-the-difference-between-list-append-and-list-extend"
        }
    },
    {
        "id": 3,
        "text": (
            "Question: How do I read a file line by line in Python into a list?\n\n"
            "Answer:\n"
            "The standard, memory-efficient way to read a file line by line is to iterate over the file object inside a `with` block:\n"
            "```python\nwith open('file.txt', 'r', encoding='utf-8') as f:\n"
            "    lines = [line.strip() for line in f]\n"
            "```\n"
            "Using `line.strip()` removes whitespace and trailing newlines (`\\n`)."
        ),
        "metadata": {
            "title": "How do I read a file line-by-line into a list?",
            "score": 12000,
            "url": "https://stackoverflow.com/questions/15233340/how-do-i-read-a-file-line-by-line-into-a-list"
        }
    },
    {
        "id": 4,
        "text": (
            "Question: How do I convert a string to datetime in Python?\n\n"
            "Answer:\n"
            "Use Python's built-in `datetime.strptime()` function from the datetime module:\n"
            "```python\nfrom datetime import datetime\n"
            "date_string = '2023-10-27 15:30:00'\n"
            "format_str = '%Y-%m-%d %H:%M:%S'\n"
            "dt_object = datetime.strptime(date_string, format_str)\n"
            "```"
        ),
        "metadata": {
            "title": "How do I convert a string to datetime in Python?",
            "score": 9800,
            "url": "https://stackoverflow.com/questions/466345/converting-string-into-datetime"
        }
    },
    {
        "id": 5,
        "text": (
            "Question: What does the `yield` keyword do in Python?\n\n"
            "Answer:\n"
            "`yield` is used like a return statement, but the function returns a generator.\n"
            "When a generator function is called, it returns a generator object without starting execution. "
            "When the generator is iterated (e.g. in a loop or with `next()`), execution proceeds until the first `yield` where it pauses and yields the value. "
            "It remembers state for subsequent calls.\n"
            "```python\ndef my_generator():\n"
            "    yield 1\n"
            "    yield 2\n"
            "```"
        ),
        "metadata": {
            "title": "What does the yield keyword do in Python?",
            "score": 32000,
            "url": "https://stackoverflow.com/questions/231767/what-does-the-yield-keyword-do-in-python"
        }
    },
    {
        "id": 6,
        "text": (
            "Question: How do I check if a list is empty in Python?\n\n"
            "Answer:\n"
            "The most Pythonic way (PEP 8 recommended) is to check the list's truthiness directly because empty collections are falsy in Python:\n"
            "```python\nmy_list = []\nif not my_list:\n"
            "    print('List is empty!')\n"
            "```\n"
            "Avoid comparing length `len(my_list) == 0` or comparing with list literals `my_list == []`."
        ),
        "metadata": {
            "title": "How to check if a list is empty in Python?",
            "score": 14000,
            "url": "https://stackoverflow.com/questions/53513/how-do-i-check-if-a-list-is-empty"
        }
    },
    {
        "id": 7,
        "text": (
            "Question: How do I create a list compression / list comprehension in Python?\n\n"
            "Answer:\n"
            "List comprehensions provide a concise way to create lists.\n"
            "Syntax: `[expression for item in iterable if condition]`\n"
            "Example:\n"
            "```python\nsquares = [x**2 for x in range(10) if x % 2 == 0]\n# squares: [0, 4, 16, 36, 64]\n```"
        ),
        "metadata": {
            "title": "How do I create a list comprehension in Python?",
            "score": 8500,
            "url": "https://stackoverflow.com/questions/205634/list-comprehension-syntax"
        }
    },
    {
        "id": 8,
        "text": (
            "Question: How to write a decorator in Python?\n\n"
            "Answer:\n"
            "A decorator is a function that takes another function as an argument, extends its behavior, and returns a new function:\n"
            "```python\ndef my_decorator(func):\n"
            "    def wrapper(*args, **kwargs):\n"
            "        print('Before function execution')\n"
            "        result = func(*args, **kwargs)\n"
            "        print('After function execution')\n"
            "        return result\n"
            "    return wrapper\n"
            "\n"
            "@my_decorator\n"
            "def say_hello():\n"
            "    print('Hello!')\n"
            "```"
        ),
        "metadata": {
            "title": "How to write a custom decorator in Python?",
            "score": 11000,
            "url": "https://stackoverflow.com/questions/739654/understanding-decorators-in-python"
        }
    }
]
