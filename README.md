# Robocode Python Clone

Basic clone of Robocode

### Todo
* Move `parts.Base.coll` bounding rect to `robot.Robot`
* Add a `robot.Robot` subclass that uses `moving`, `turing` to move, instead of using allocated amounts.
* Add interrupt current command stack.
* Impelement movement as a proper stack of commands that have decreasing amounts.