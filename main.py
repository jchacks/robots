from robots.app import App, Battle
from robots.bots import MyFirstRobot, RandomRobot

app = App((600, 400), battle=Battle(
    size=(600, 400),
    robots=[
        MyFirstRobot.MyFirstRobot,
        RandomRobot.RandomRobot
    ]))
app.set_sim_rate(10)
app.run()
