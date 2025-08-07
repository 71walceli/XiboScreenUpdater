# Coding conventions
## Functions
Tt's strongly preferred for functions, method args list or calls, and data structs to use *Hanging indent with extra indentation*, and not be visually aligned to function name or opening parenthesis. E.g.

```py
# Discouraged
def function(arg1,
             arg2,
             arg3
            )

# Acceptable
def function(
    arg1, 
    arg2, 
    arg3
)
```

Argument or param lists should be kept on same line, as long as all fits in up to 100 characters, otherwise indent as proposed.

It's aldo applicable for lists, dicts, sets type definitions, among any data structure.

In methods, Python requires methods to have self. That arg can be on the same file as the function, as it's mandatoy by Python.

## Typing
- As long as possible, types are expected to be defined, especially for functions' params and return type
- If a type is unknown, avoid merely using `any`, but it's fine to have compound types that include it, e.g. `list[tuple[str, any]]`

## Imports
All imports should be listed at the top and properly sorted, unless it's accompained with some comment jusifying why it's not at top of function.