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

# FUNCTIONS ####################################################################
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


# PODSIXNET ####################################################################
class GameClient(ConnectionListener):

    def __init__(self, host, port):
        self.Connect((host, port))
        self.run = False

	### Network event/message callbacks ###
    def Network_connected(self, data):
        self.run = True
        print('client connecte au serveur !')

    def Network_error(self, data):
        print('error: %s', data['error'][1])
        connection.Close()
                            
    def Network_disconnected(self, data):
        print('Server disconnected')
        sys.exit()

    def Network_gameover(self, data):
        print('GAME OVER')
        sys.exit()


# CLASSES ####################################################################
class Soldier(pygame.sprite.Sprite, ConnectionListener):
    """Class for the player"""

    def __init__(self):
	pygame.sprite.Sprite.__init__(self)
	self.image,self.rect=load_png("Pics/soldier_n.png")
        self.image_n, _ = load_png("Pics/soldier_n.png")
        self.image_s, _ = load_png("Pics/soldier_s.png")
        self.image_e, _ = load_png("Pics/soldier_e.png")
        self.image_w, _ = load_png("Pics/soldier_w.png")
        self.image_ne, _ = load_png("Pics/soldier_ne.png")
        self.image_nw, _ = load_png("Pics/soldier_nw.png")
        self.image_se, _ = load_png("Pics/soldier_se.png")
        self.image_sw, _ = load_png("Pics/soldier_sw.png")
        self.rect.center = [ SCREEN_WIDTH/2, SCREEN_HEIGHT/2 ]
        self.orientation = 'n'

    def Network_soldier(self,data):
        self.rect.center = data['rect'] 
        self.orientation = data['orientation']
        if self.orientation == 'n':
            self.image = self.image_n
        elif self.orientation == 's':
            self.image = self.image_s
        elif self.orientation == 'e':
            self.image = self.image_e
        elif self.orientation == 'w':
            self.image = self.image_w
        elif self.orientation == 'ne':
            self.image = self.image_ne
        elif self.orientation == 'nw':
            self.image = self.image_nw
        elif self.orientation == 'se':
            self.image = self.image_se
        elif self.orientation == 'sw':
            self.image = self.image_sw

    def update(self):
        self.Pump()

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
        elif self.action == 'mechs':
            self.add(Mech())

    def update(self):
        self.Pump()

class Shot(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_png('Pics/shot.png')

    def update(self, position):
        self.rect.center = position

class Mech(pygame.sprite.Sprite):
    '''
    The foes
    '''
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_png('Pics/mech_n.png')
        self.image_n, _ = load_png('Pics/mech_n.png')
        self.image_s, _ = load_png('Pics/mech_s.png')
        self.image_e, _ = load_png('Pics/mech_e.png')
        self.image_w, _ = load_png('Pics/mech_w.png')

    def update(self, position):
        self.rect.center = position[0:2]
        self.orientation = position[2]
        if self.orientation == 'n':
            self.image = self.image_n
        elif self.orientation == 's':
            self.image = self.image_s
        elif self.orientation == 'e':
            self.image = self.image_e
        elif self.orientation == 'w':
            self.image = self.image_w

# MAIN #####################################################################
if __name__ == '__main__':
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768

    # PodSixNet init
    game_client = GameClient(sys.argv[1],int(sys.argv[2]))

    # Init Pygame
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    pygame.key.set_repeat(1,1)

    # Elements
    background_image, background_rect = load_png('Pics/background.jpg')
    screen.blit(background_image, background_rect)
    soldier = Soldier()
    soldier_sprite = pygame.sprite.RenderClear(soldier)
    shots_group = SpriteGroup('shots')
    mechs_group = SpriteGroup('mechs')

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
            soldier_sprite.update()
            shots_group.update()
            mechs_group.update()

            # drawings
            soldier_sprite.clear(screen, background_image)
            soldier_sprite.draw(screen)

            shots_group.clear(screen, background_image)
            shots_group.draw(screen)

            mechs_group.clear(screen, background_image)
            mechs_group.draw(screen)

        else: # game is not running 
            screen.blit(wait_image, wait_rect)
            
        pygame.display.flip()  

