# Robocode Python Clone

Basic clone of Robocode focused on simulation speed when rendering is turned off.

![Battle Image](/docs/images/battle.png)

#### How to use:

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

To run the application:
```python
from robots.app import App, Battle
# Import the bot from wherever it was located
from robots.bots import MyFirstRobot, RandomRobot


app = App((600, 400))
app.battle = Battle(app, (600,400), [
    MyFirstRobot.MyFirstRobot,
    RandomRobot.RandomRobot
])

app.set_sim_rate(10) # Set the simulation rate
app.on_execute() # Start execution
```

### Multi Battles

It is also possible to run multiple battles simultaneously.
Useful when training reinforcement learning algorithms.

```python
from robots.app import App
from robots.battle import MultiBattle
from robots.bots import MyFirstRobot, RandomRobot


app = App((1200, 800))
app.battle = MultiBattle(app, (600,400), [
    MyFirstRobot.MyFirstRobot,
    RandomRobot.RandomRobot
], 16)
app.on_execute()
```
![Multi_Battle Image](/docs/images/multi_battle.png)

### Todo
* ~~Add a `robot.Robot` subclass that uses `moving`, `turing` to move, instead of using allocated amounts.~~
* Add interrupt current command stack.
* Implement movement as a proper stack of commands that have decreasing amounts.
* ~~Remove bullets on round end~~
* Abstract out the canvas drawable setup and resizing to a canvas class
* Fully document all methods that are intended to be part of the public API.
* Decide on whether to use degrees or radians for rotation.
* Convert to a Data Oriented Programming model (should allow for multi-battle speedup):
    * Create robot data containers similar to `Bullets`
    * Refer Robot classes back to these data containers
    * Gracefully handle alive/dead, adding removing 
