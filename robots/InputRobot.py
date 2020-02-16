from robot import Robot
import pygame as pg


class InputRobot(Robot):
    def do(self):
        pg.mouse.get_pos()
        if pg.KEYDOWN