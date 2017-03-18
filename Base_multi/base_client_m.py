#!/usr/bin/python2
# -*- coding: utf-8 -*-

"""
    Very simple game with Pygame
"""
import sys, pygame
import os
import time
from pygame.locals import *
import random
from PodSixNet.Connection import connection, ConnectionListener

# FUNCTIONS
def load_png(name):
    """Load image and return image object"""
    fullname=os.path.join('.',name)
    try:
        image=pygame.image.load(fullname)
        if image.get_alpha is None:
            image=image.convert()
        else:
            image=image.convert_alpha()
    except pygame.error:
        print('Cannot load image: %s' % name)
        raise SystemExit
    return image,image.get_rect()


# PODSIXNET
class GameClient(ConnectionListener):

    def __init__(self, host, port):
        self.Connect((host, port))
        self.run = False

	### Network event/message callbacks ###
    def Network_connected(self, data):
        print('client connecte au serveur !')

    def Network_start(self, data):
        self.run = True
        screen.blit(background_image, background_rect)

    def Network_error(self, data):
        print('error: %s', data['error'][1])
        connection.Close()

    def Network_disconnected(self, data):
        print('Server disconnected')
        sys.exit()


# CLASSES
class Vaisseau(pygame.sprite.Sprite, ConnectionListener):
    """Class for the player"""

    def __init__(self, number):
        pygame.sprite.Sprite.__init__(self)
        self.shot_group = pygame.sprite.RenderClear()

	self.number = number
        if number == 1:
            self.image,self.rect=load_png("Pics/vaisseau_r.png")
            self.image_n,_ = load_png("Pics/vaisseau_r.png")
            self.rect.center = [SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2]
        elif number == 2:
            self.image,self.rect=load_png("Pics/vaisseau_b.png")
            self.image_n,_ = load_png("Pics/vaisseau_b.png")
            self.rect.center = [SCREEN_WIDTH/2 + 100, SCREEN_HEIGHT/2]

    def Network_vaisseau(self,data):
        self.image = self.image_n
        if data['vaisseau' + str(self.number)] == "kill":
            print("mort")
            self.kill()
        else:
            self.rect.center = data['vaisseau' + str(self.number)][0:2]

    def update(self):
        self.Pump()

class Chicken(pygame.sprite.Sprite):
    """Class for the player"""

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        #self.shot_group = pygame.sprite.RenderClear()

        self.image,self.rect=load_png("Pics/chicken.png")
        self.rect.center = [100, 100]

    def Network_chicken(self,data):
        self.rect.center = data['chicken'][0:2]

    def update(self, position):
        self.rect.center = position[0:2]

class Shot(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_png('Pics/shot.png')

    def update(self, position):
        self.rect.center = position


class SpriteGroup(pygame.sprite.RenderClear, ConnectionListener):
    '''
    Sprite groups (shots, mechs)
    '''
    def __init__(self, action):
        pygame.sprite.RenderClear.__init__(self)
        self.action = action

    def Network(self, data):
        if data['action'] == self.action:
            elems = data[self.action]
            num_sprites = len(self.sprites())

            if num_sprites < len(elems): # we're missing sprites
                for additional_sprite in range(len(elems) - num_sprites):
                    self.add_elem()
            elif num_sprites > len(elems): # we've got too many
                deleted = 0
                to_delete = num_sprites - len(elems)
                for sprite in self.sprites():
                    self.remove(sprite)
                    deleted += 1
                    if deleted == to_delete:
                        break

            for indice, sprite in enumerate(self.sprites()):
                sprite.update(elems[indice])

    def add_elem(self):
        if self.action == 'shots':
            self.add(Shot())
        elif self.action == 'chickens':
            self.add(Chicken())

    def update(self):
        self.Pump()


# MAIN
if __name__ == '__main__':
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600

    # PodSixNet init
    game_client = GameClient(sys.argv[1],int(sys.argv[2]))

    # Init Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    pygame.key.set_repeat(1,1)

    # Elements
    background_image, background_rect = load_png('Pics/background.jpg')
    wait_image, wait_rect = load_png('Pics/wait1.png')
    wait_rect.center = [ SCREEN_WIDTH/2, SCREEN_HEIGHT/2 ]
    screen.blit(background_image, background_rect)
    vaisseau_sprite = pygame.sprite.RenderClear()
    vaisseau_sprite.add(Vaisseau(1))
    vaisseau_sprite.add(Vaisseau(2))
    shot_group = SpriteGroup('shots')
    chicken_group = SpriteGroup('chickens')

    while True:
        clock.tick(60)
        connection.Pump()
        game_client.Pump()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit(0)

        if game_client.run:
            keys = pygame.key.get_pressed()
            if keys[K_q]:
                sys.exit(0)
            connection.Send({'action':'keys','keystrokes':keys})

            # updates
            vaisseau_sprite.update()
            shot_group.update()
            chicken_group.update()

            # drawings
            vaisseau_sprite.clear(screen, background_image)
            vaisseau_sprite.draw(screen)
            shot_group.clear(screen, background_image)
            shot_group.draw(screen)
            chicken_group.clear(screen, background_image)
            chicken_group.draw(screen)

        else: # game is not running
            screen.blit(wait_image, wait_rect)

        pygame.display.flip()
