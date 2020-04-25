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
from robots import AdvancedRobot


class MyFirstRobot(AdvancedRobot):
    def __init__(self, *args, **kwargs):
        super(MyFirstRobot, self).__init__(*args, **kwargs)
        self.radar.locked = True
        self.gun.locked = True

    def do(self):
        self.move_forward(1000)
        self.turn_left(360)

    def on_scanned(self, scanned):
        self.fire(1)
```

Simple spin and shoot when a robot is scanned.

### Todo
* Add a `robot.Robot` subclass that uses `moving`, `turing` to move, instead of using allocated amounts.
* Add interrupt current command stack.
* Impelement movement as a proper stack of commands that have decreasing amounts.
* Remove bullets on round end
* Abstract out the canvas drawable setup and resizing to a canvas class