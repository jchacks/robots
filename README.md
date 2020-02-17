# Robocode Python Clone

Basic clone of Robocode focused on simulation speed when rendering is turned off.

[Battle Image](/docs/images/battle.png)

#### How to use:
To run the application:
```python
from robots.app import App

app = App((1920, 1080))
app.on_execute()
```
To build your own robot:
```python
from robots.app import App

app = App((1920, 1080))
app.on_execute()
```

### Todo
* Move `parts.Base.coll` bounding rect to `robot.Robot`
* Add a `robot.Robot` subclass that uses `moving`, `turing` to move, instead of using allocated amounts.
* Add interrupt current command stack.
* Impelement movement as a proper stack of commands that have decreasing amounts.
