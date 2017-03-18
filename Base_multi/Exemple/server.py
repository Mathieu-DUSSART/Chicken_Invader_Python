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
from PodSixNet.Channel import Channel
from PodSixNet.Server import Server
import time,sys



# FUNCTIONS *******************
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

# GAME CLASSES ****************
class Soldier(pygame.sprite.Sprite):
    """Class for the player"""

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_png('Pics/soldier_n.png')
	self.orientation = 'n' 
        self.rect.center = [SCREEN_WIDTH/2, SCREEN_HEIGHT/2]
        self.speeds = {'nw':[-1,-1], 'ne':[1,-1], 'n':[0,-1], 'sw':[-1,1], 'se':[1,1], 's':[0,1], 'w':[-1,0], 'e':[1,0]}   
        self.speed = 8

    def update(self, keys):
        move = False
        if keys[K_UP]:
            move = True
            if keys[K_LEFT]:
                self.orientation = 'nw'
            elif keys[K_RIGHT]:
                self.orientation = 'ne'
            else:
                self.orientation = 'n'
        elif keys[K_DOWN]:
            move = True
            if keys[K_LEFT]:
                self.orientation = 'sw'
            elif keys[K_RIGHT]:
                self.orientation = 'se'
            else:
                self.orientation = 's'
        elif keys[K_LEFT]:
            move = True
            self.orientation = 'w'
        elif keys[K_RIGHT]:
            move = True
            self.orientation = 'e'

        if move:
            self.rect = self.rect.move([self.speed * self.speeds[self.orientation][0], self.speed * self.speeds[self.orientation][1]])

class Shot(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self,center,orientation):
        pygame.sprite.Sprite.__init__(self)
        self.image,self.rect=load_png("Pics/shot.png")
        self.rect.center = center
        speeds = {'nw':[-1,-1], 'ne':[1,-1], 'n':[0,-1], 'sw':[-1,1], 'se':[1,1], 's':[0,1], 'w':[-1,0], 'e':[1,0]}   
        self.vector = [15 * x for x in speeds[orientation]]

    def update(self):
        self.rect=self.rect.move(self.vector)
        if((self.rect.top>SCREEN_WIDTH) or (self.rect.bottom<0)):
            self.kill()
        if((self.rect.left>SCREEN_WIDTH) or (self.rect.right<0)):
            self.kill()

class Mech(pygame.sprite.Sprite):
    '''
    The foes ...
    '''
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 2
        side = random.randint(1,4)
        if side == 1:
            self.image,self.rect=load_png("Pics/mech_n.png")
            coord_x = random.randint(1, SCREEN_WIDTH)
            self.rect.center = [ coord_x, SCREEN_HEIGHT]
            self.orientation = 'n'
        elif side == 2:
            self.image,self.rect=load_png("Pics/mech_s.png")
            coord_x = random.randint(1, SCREEN_WIDTH)
            self.rect.center = [ coord_x, 1]
            self.orientation = 's'
        elif side == 3:
            self.image,self.rect=load_png("Pics/mech_e.png")
            coord_y = random.randint(1, SCREEN_HEIGHT)
            self.rect.center = [ 1, coord_y]
            self.orientation = 'e'
        else:
            self.image,self.rect=load_png("Pics/mech_w.png")
            coord_y = random.randint(1, SCREEN_HEIGHT)
            self.rect.center = [ SCREEN_WIDTH, coord_y]
            self.orientation = 'w'

    def update(self, coords_soldier):
        delta_x = coords_soldier[0] - self.rect.centerx
        delta_y = coords_soldier[1] - self.rect.centery
        move_x = self.speed * delta_x / (abs(delta_x) + abs(delta_y))
        move_y = self.speed * delta_y / (abs(delta_x) + abs(delta_y))
        self.rect = self.rect.move([move_x, move_y])

# PODSIXNET *********************
class ClientChannel(Channel):

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.soldier = Soldier()
        self.shot_group = pygame.sprite.RenderClear()
        self.shooting = 0

    def Close(self):
        self._server.del_client(self)

    def Network_keys(self,data):
        keys = data['keystrokes']
        if self.shooting != 0:
            self.shooting -= 1
        if keys[K_SPACE]:
            if self.shooting == 0:
                self.shot_group.add(Shot(self.soldier.rect.center, self.soldier.orientation))
                self.shooting = 12
        self.soldier.update(keys)

    def update(self, mech_group):
        self.shot_group.update()
        pygame.sprite.groupcollide(mech_group, self.shot_group, True, True, pygame.sprite.collide_circle_ratio(0.7))
        collision = pygame.sprite.spritecollide(self.soldier, mech_group, False, pygame.sprite.collide_circle_ratio(0.5))
        if len(collision) != 0:
            self.Send({"action":"gameover"})
            self._server.Pump()
            print('gameover')
            sys.exit(0)
        else:
            self.send_soldier()
            self.send_shots()
            self.send_mechs(mech_group)

    def send_soldier(self):
        self.Send({"action":"soldier", "rect":self.soldier.rect.center, "orientation": self.soldier.orientation})

    def send_shots(self):
        shots = []
        for shot in self.shot_group.sprites():
            shots.append(shot.rect.center)
        self.Send({"action":'shots', 'shots': shots})

    def send_mechs(self, mech_group):
        mechs = []
        for mech in mech_group.sprites():
            mechs.append([mech.rect.center[0], mech.rect.center[1], (mech.orientation)])
        self.Send({"action":'mechs', 'mechs': mechs})


# SERVER
class MyServer(Server):
    
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.clients = []
        self.run = False
        pygame.init()
        self.screen = pygame.display.set_mode((128, 128))
        print('Server launched')

    def Connected(self, channel, addr):
        self.clients.append(channel)
        print('New connection: %d client(s) connected' % len(self.clients))
        if len(self.clients) == 1:
            self.run = True
            wheels_image, wheels_rect = load_png('Pics/wheels.png')
            self.screen.blit(wheels_image, wheels_rect)

    def del_client(self,channel):
        print('client deconnecte')
        self.clients.remove(channel)

    # UPDATE FUNCTIONS
    def update_channels(self, mech_group):
        for client in self.clients:
            client.update(mech_group)

    # MAIN LOOP
    def launch_game(self):
        """Main function of the game"""
        rythm = 60
        counter = 0

        # Init Pygame
        pygame.display.set_caption('Server')
        clock = pygame.time.Clock()
        pygame.key.set_repeat(1,1)

        # Elements
        wait_image, wait_rect = load_png('Pics/wait.png')
        self.screen.blit(wait_image, wait_rect)
        self.mech_group = pygame.sprite.RenderClear()

        while True:
            clock.tick(60)
            self.Pump()

            if self.run:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return

                # updates
                self.update_channels(self.mech_group)
                self.mech_group.update(self.clients[0].soldier.rect.center)

                counter += 1
                if counter == rythm:
                    self.mech_group.add(Mech())
                    counter = 0
                    rythm -= 1 if rythm > 20 else 0

            pygame.display.flip()
            

# PROGRAMME INIT
if __name__ == '__main__':
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    my_server = MyServer(localaddr = (sys.argv[1],int(sys.argv[2])))
    my_server.launch_game()
