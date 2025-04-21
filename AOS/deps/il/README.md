# il - the indigo logger

### Installation

```sh
uv add git+https://github.com/iiPythonx/il
pip install git+https://github.com/iiPythonx/il
# ...
```

### Importing

```py
import il
il.request(...)
```

### Methods

`il.request` generates a log fit for an HTTP request.

```py
il.request(
    path = "/abc/def",
    remote_ip = "1.1.1.1",
    summary = "200 OK",
    summary_color = 32,
    time_taken_seconds = 0.2,
    # detail_text = "Extra details to be logged",
    # verb = "GET"
)
```

`il.box` generates a unicode based box.

```py
il.box(
    size = 38,
    left = "Some text",
    right = "More text",
    # color = 34
)
```

`il.rule` generates a line similar to an HTML horizontal rule.

```py
il.rule(
    size = 38,
    # color = 34
)
```

`il.indent` generates indented text with a given color.

```py
il.rule(
    text = "Hello, world!",
    # color = 34,
    # indent = 2
)
```

`il.cprint` generates a single line of colored text.

```py
il.cprint(text = "Hello, world!", color = 32)
```

### Contributing

Before making a pull request, please note this library is not meant to compete with something like [rich](https://github.com/Textualize/rich), and I don't plan on adding features such as tables/markdown/etc.
