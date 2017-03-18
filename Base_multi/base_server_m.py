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
class Vaisseau(pygame.sprite.Sprite):
    """Class for the player"""

    def __init__(self, number):
        pygame.sprite.Sprite.__init__(self)
        self.shot_group = pygame.sprite.RenderClear()
        self.image, self.rect = load_png('Pics/soldier_n.png')
        self.life = 3
        self.dead = False

        if number == 1:
            self.rect.center = [SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT/2]
        elif number == 2:
            self.rect.center = [SCREEN_WIDTH/2 + 100, SCREEN_HEIGHT/2]

    def update(self, keys):
        if self.dead == False:
            if keys[K_UP]:
                if self.rect.center[1] >= 0:
                    self.rect = self.rect.move([0,-10])
            elif keys[K_DOWN]:
                if self.rect.center[1] <= SCREEN_HEIGHT:
                    self.rect = self.rect.move([0,10])
            elif keys[K_LEFT]:
                if self.rect.center[0] >= 0:
                    self.rect = self.rect.move([-10,0])
            elif keys[K_RIGHT]:
                if self.rect.center[0] <= SCREEN_WIDTH:
                    self.rect = self.rect.move([10,0])

    def killVaisseau(self):
        self.dead = True
        self.kill()

class Chicken(pygame.sprite.Sprite):
    """Class for the player"""
    coord_x = 50
    coord_y = 50

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        #self.shot_group = pygame.sprite.RenderClear()

        self.image,self.rect=load_png("Pics/chicken.png")
        #coord_x = random.randrange(100, SCREEN_WIDTH, 100)
        #coord_y = random.randrange(100, 250, 72)
        self.rect.center = [Chicken.coord_x, Chicken.coord_y]
        Chicken.coord_x += 100
        if(Chicken.coord_x >= SCREEN_WIDTH):
            Chicken.coord_x = 50
            Chicken.coord_y += 72


    def update(self):
        #self.Pump()
        ''' '''

class Shot(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self,center,orientation,speed):
        pygame.sprite.Sprite.__init__(self)
        self.image,self.rect=load_png("Pics/shot.png")
        self.rect.center = center
        speeds = {'nw':[-1,-1], 'ne':[1,-1], 'n':[0,-1], 'sw':[-1,1], 'se':[1,1], 's':[0,1], 'w':[-1,0], 'e':[1,0]}
        self.vector = [speed * x for x in speeds[orientation]]

    def update(self):
        self.rect=self.rect.move(self.vector)
        if((self.rect.top>SCREEN_WIDTH) or (self.rect.bottom<0)):
            self.kill()
        if((self.rect.left>SCREEN_WIDTH) or (self.rect.right<0)):
            self.kill()


# PODSIXNET *********************
class ClientChannel(Channel):

    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.shot_group = pygame.sprite.RenderClear()
        self.shooting = 0

    def create_vaisseau(self, number):
        self.vaisseau = Vaisseau(number)

    def create_chicken(self):
        self.chicken = Chicken()

    def Close(self):
        self._server.del_client(self)

    def Network_keys(self,data):
        keys = data['keystrokes']
        if self.shooting != 0:
            self.shooting -= 1
        if keys[K_SPACE]:
            if self.shooting == 0:
                self.shot_group.add(Shot(self.vaisseau.rect.center, 'n', 15))
                self.shooting = 12
        self.vaisseau.update(keys)

    def update(self, chicken_group):
        self.shot_group.update()

        pygame.sprite.groupcollide(chicken_group, self.shot_group, True, True, pygame.sprite.collide_circle_ratio(0.85))
        #collision = pygame.sprite.spritecollide(self.vaisseau, chicken_group, False, pygame.sprite.collide_circle_ratio(0.5))

        self.send_chickens(chicken_group)


    def send_chickens(self, chicken_group):
        chickens = []
        for chicken in chicken_group.sprites():
            chickens.append([chicken.rect.centerx, chicken.rect.centery])

        self.Send({"action":'chickens', 'chickens': chickens})



# SERVER
class MyServer(Server):

    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.clients = []
        self.run = False
        pygame.init()
        self.shot_group = pygame.sprite.RenderClear()

        self.screen = pygame.display.set_mode((128, 128))
        print('Server launched')

    def Connected(self, channel, addr):
        self.clients.append(channel)
        channel.create_vaisseau(len(self.clients))
        channel.create_chicken()
        print('New connection: %d client(s) connected' % len(self.clients))

        if len(self.clients) == 2:
            for client in self.clients:
                client.Send({'action':'start'})
            self.run = True
            wheels_image, wheels_rect = load_png('Pics/wheels.png')
            self.screen.blit(wheels_image, wheels_rect)

    def del_client(self,channel):
        print('client deconnecte')
        self.clients.remove(channel)

    # SENDING FUNCTIONS
    def send_vaisseaux(self):
        message1 = ""
        message2 = ""
        vaisseau1 = self.clients[0].vaisseau
        vaisseau2 = self.clients[1].vaisseau

        self.shot1 = self.clients[0].shot_group
        self.shot2 = self.clients[1].shot_group

        collision = pygame.sprite.spritecollide(vaisseau1, self.shot_group, True, pygame.sprite.collide_circle_ratio(0.8))
        collision2 = pygame.sprite.spritecollide(vaisseau2, self.shot_group, True, pygame.sprite.collide_circle_ratio(0.8))

        if len(collision) != 0:
            vaisseau1.life -= 1
            if vaisseau1.life == 0:
                vaisseau1.killVaisseau()
                message1 = "kill"

        if len(message1) == 0:
            message1 = [ vaisseau1.rect.centerx, vaisseau1.rect.centery ]


        if len(collision2) != 0:
            vaisseau2.life -= 1
            if vaisseau2.life == 0:
                vaisseau2.killVaisseau()
                message2 = "kill"

        if len(message2) == 0:
            message2 = [ vaisseau2.rect.centerx, vaisseau2.rect.centery ]



        for client in self.clients:
            client.Send({'action':'vaisseau', 'vaisseau1':message1, 'vaisseau2':message2})



    def send_shots(self):
        shots = []
        for shot in self.shot1:
            shots.append(shot.rect.center)
        for shot in self.shot2:
            shots.append(shot.rect.center)
        for shot in self.shot_group:
            shots.append(shot.rect.center)
        for client in self.clients:
            client.Send({"action":'shots', 'shots': shots})

    def update_channels(self, chicken_group):
        for client in self.clients:
            client.update(chicken_group)

    # MAIN LOOP
    def launch_game(self):
        """Main function of the game"""
        test = 0

        # Init Pygame
        pygame.display.set_caption('Server')
        clock = pygame.time.Clock()
        pygame.key.set_repeat(1,1)

        # Elements
        wait_image, wait_rect = load_png('Pics/wait.png')
        self.screen.blit(wait_image, wait_rect)
        self.chicken_group = pygame.sprite.RenderClear()

        while True:
            clock.tick(60)
            self.Pump()

            if self.run:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return

                # updates
                self.send_vaisseaux()
                self.update_channels(self.chicken_group)
                if test < 25:
                    self.chicken_group.add(Chicken())
                    test = test + 1


                for chicken in self.chicken_group:
                    egg = random.randint(1, 4000)
                    if egg == 42:
                        self.shot_group.add(Shot(chicken.rect.center, 's', 1))
                self.send_shots()
                self.shot_group.update()


            pygame.display.flip()


# PROGRAMME INIT
if __name__ == '__main__':
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    my_server = MyServer(localaddr = (sys.argv[1],int(sys.argv[2])))
    my_server.launch_game()
