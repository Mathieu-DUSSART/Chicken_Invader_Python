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
from math import sqrt



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
            self.rect.center = [SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT - 100]
        elif number == 2:
            self.rect.center = [SCREEN_WIDTH/2 + 100, SCREEN_HEIGHT - 100]

    def update(self, keys):
        if self.dead == False:
            if keys[K_UP] and keys[K_LEFT]:
                if self.rect.center[1] >= 0 and self.rect.center[0] >= 0:
                    self.rect = self.rect.move([-7,-7])
            elif keys[K_UP] and keys[K_RIGHT]:
                if self.rect.center[1] >= 0 and self.rect.center[0] <= SCREEN_WIDTH:
                    self.rect = self.rect.move([7,-7])
            elif keys[K_DOWN] and keys[K_RIGHT]:
                if self.rect.center[1] <= SCREEN_HEIGHT and self.rect.center[0] <= SCREEN_WIDTH:
                    self.rect = self.rect.move([7,7])
            elif keys[K_DOWN] and keys[K_LEFT]:
                if self.rect.center[1] <= SCREEN_HEIGHT and self.rect.center[0] >= 0:
                    self.rect = self.rect.move([-7,7])
            elif keys[K_UP]:
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
        self.rect.center = [-200, -200]

class Chicken(pygame.sprite.Sprite):
    """Class for the player"""
    coord_x = 50
    coord_y = 150

    def __init__(self, difficulte):
        pygame.sprite.Sprite.__init__(self)
        #self.shot_group = pygame.sprite.RenderClear()
        self.vie = 10 * difficulte
        self.difficulte = difficulte
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

    def __del__(self):
        ClientChannel.score += int(100 * (self.difficulte / 2))

class Shot(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self,typeShot,center,orientation,speed):
        pygame.sprite.Sprite.__init__(self)
        if typeShot == 0:
            self.image, self.rect = load_png('Pics/shot.png')
        elif typeShot == 1:
            self.image, self.rect = load_png('Pics/egg.png')
        self.rect.center = center
        speeds = {'nw':[-0.1,-1], 'ne':[0.1,-1], 'n':[0,-1], 'sw':[-1,1], 'se':[1,1], 's':[0,1], 'w':[-1,0], 'e':[1,0]}
        self.vector = [speed * x for x in speeds[orientation]]

    def update(self):
        self.rect=self.rect.move(self.vector)
        if((self.rect.top>SCREEN_WIDTH) or (self.rect.bottom<0)):
            self.kill()
        if((self.rect.left>SCREEN_WIDTH) or (self.rect.right<0)):
            self.kill()

class Vague(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self, numero, chicken_group):
        pygame.sprite.Sprite.__init__(self)
        '''On définit la difficulté'''
        self.difficulte = numero * 0.7
        '''Booléen qui définit si la vague est finie ou non'''
        self.enCours = True

        '''On reset les coordonnées de de début de la vague'''
        Chicken.coord_x = 50
        Chicken.coord_y = 100

        '''On fait apparaitre 30 poulets par vague '''
        for nbPoulet in range(0, 30):
            chicken_group.add(Chicken(self.difficulte))

    def update(self):
        ''''''

    def terminerVague(self):
        self.enCours = False

class Cadeau(pygame.sprite.Sprite):
    '''
    The player's shots
    '''
    def __init__(self,center):
        pygame.sprite.Sprite.__init__(self)
        self.image,self.rect=load_png("Pics/cadeau.png")
        self.rect.center = center
        speeds = {'nw':[-1,-1], 'ne':[1,-1], 'n':[0,-1], 'sw':[-1,1], 'se':[1,1], 's':[0,1], 'w':[-1,0], 'e':[1,0]}
        self.vector = [1 * x for x in speeds['s']]

    def update(self):
        self.rect=self.rect.move(self.vector)
        if((self.rect.top>SCREEN_WIDTH) or (self.rect.bottom<0)):
            self.kill()
        if((self.rect.left>SCREEN_WIDTH) or (self.rect.right<0)):
            self.kill()

# PODSIXNET *********************
class ClientChannel(Channel):
    score = 0


    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.shot_group = pygame.sprite.RenderClear()
        self.shooting = 0
        self.vie = 3
        self.force = 10
        self.nbTir = 1

    def create_vaisseau(self, number):
        self.vaisseau = Vaisseau(number)
        MyServer.vaisseau_group.add(self.vaisseau)

    def create_chicken(self, diff):
        self.chicken = Chicken(diff)

    def Close(self):
        self._server.del_client(self)

    def Network_keys(self,data):
        keys = data['keystrokes']
        if self.shooting != 0:
            self.shooting -= 1
        if keys[K_SPACE]:
            if self.shooting == 0 and self.vaisseau.alive():
                if self.nbTir == 1:
                    self.shot_group.add(Shot(0, self.vaisseau.rect.center, 'n', 15))
                elif self.nbTir == 2:
                    '''1er tir'''
                    centerTir = self.vaisseau.rect
                    centerTir[0] = centerTir[0] - 16
                    self.shot_group.add(Shot(0, centerTir.center, 'n', 15))
                    '''2eme tir'''
                    centerTir = self.vaisseau.rect
                    centerTir[0] = centerTir[0] + 16
                    self.shot_group.add(Shot(0, centerTir.center, 'n', 15))
                elif self.nbTir == 3:
                    '''1er tir'''
                    self.shot_group.add(Shot(0, [self.vaisseau.rect.center[0] - 16, self.vaisseau.rect.center[1]], 'nw', 15))
                    '''2eme tir'''
                    self.shot_group.add(Shot(0, self.vaisseau.rect.center, 'n', 15))
                    '''3eme tir'''
                    self.shot_group.add(Shot(0, [self.vaisseau.rect.center[0] + 16, self.vaisseau.rect.center[1]], 'ne', 15))
                elif self.nbTir >= 4:
                    '''1er tir'''
                    self.shot_group.add(Shot(0, [self.vaisseau.rect.center[0] - 16, self.vaisseau.rect.center[1]], 'nw', 15))
                    '''2eme tir'''
                    self.shot_group.add(Shot(0, [self.vaisseau.rect.center[0] - 8, self.vaisseau.rect.center[1]], 'n', 15))
                    '''3eme tir'''
                    self.shot_group.add(Shot(0, [self.vaisseau.rect.center[0] + 8, self.vaisseau.rect.center[1]], 'n', 15))
                    '''4eme tir'''
                    self.shot_group.add(Shot(0, [self.vaisseau.rect.center[0] + 16, self.vaisseau.rect.center[1]], 'ne', 15))
                self.shooting = 12
        self.vaisseau.update(keys)

    def update(self, chicken_group):
        self.shot_group.update()

        """ Collision entre tir du joueur et poulets"""
        chickenHit = pygame.sprite.groupcollide(chicken_group, self.shot_group, False, True, pygame.sprite.collide_circle_ratio(0.85))
        for chicken in chickenHit.keys():
            '''Quand un poulet est touché, on diminue sa vie en fonction de la puissance du joueur'''
            if len(chickenHit) != 0:
                chicken.vie -= self.force
                if chicken.vie <= 0:
                    chicken.kill()

        self.send_chickens(chicken_group)
        self.send_score()
        self.vie = self.vaisseau.life



    def send_chickens(self, chicken_group):
        chickens = []
        for chicken in chicken_group.sprites():
            chickens.append([chicken.rect.centerx, chicken.rect.centery])

        self.Send({"action":'chickens', 'chickens': chickens})

    def send_score(self):
        self.Send({"action":'score', 'score':ClientChannel.score})




# SERVER
class MyServer(Server):
    vaisseau_group = pygame.sprite.RenderClear()
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
        channel.create_chicken(3)
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

        collision = pygame.sprite.spritecollide(vaisseau1, self.shot_group, True, pygame.sprite.collide_circle_ratio(0.5))
        collision2 = pygame.sprite.spritecollide(vaisseau2, self.shot_group, True, pygame.sprite.collide_circle_ratio(0.5))

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

        collisionCadeau1 = pygame.sprite.spritecollide(vaisseau1, self.cadeau_group, True, pygame.sprite.collide_circle_ratio(0.5))
        collisionCadeau2 = pygame.sprite.spritecollide(vaisseau2, self.cadeau_group, True, pygame.sprite.collide_circle_ratio(0.5))


        if len(collisionCadeau1) != 0:
            self.clients[0].force += 10
            if self.clients[0].force == 40 and self.clients[0].nbTir <= 4:
                self.clients[0].nbTir += 1
                self.clients[0].force = 10


        if len(collisionCadeau2) != 0:
            self.clients[1].force += 10
            if self.clients[1].force == 40 and self.clients[1].nbTir <= 4:
                self.clients[1].nbTir += 1
                self.clients[1].force = 10




        for client in self.clients:
            client.Send({'action':'vaisseau', 'vaisseau1':message1, 'vaisseau2':message2})

    def send_vie(self):
        vie1 = self.clients[0].vie
        vie2 = self.clients[1].vie

        for client in self.clients:
            client.Send({"action":'vie', 'vie1':vie1, 'vie2':vie2})

    def send_shots(self):
        shotsJoueur = []
        for shot in self.shot1:
            shotsJoueur.append(shot.rect.center)
        for shot in self.shot2:
            shotsJoueur.append(shot.rect.center)

        shotsChicken = []
        for shot in self.shot_group:
            shotsChicken.append(shot.rect.center)

        for client in self.clients:
            client.Send({"action":'shotsJoueur', 'shotsJoueur': shotsJoueur})
            client.Send({"action":'shotsChicken', 'shotsChicken': shotsChicken})

    def send_numVague(self):
        for client in self.clients:
            client.Send({"action":'numVague', 'numVague': self.numVague})

    def send_cadeaux(self):
        cadeaux = []
        for cadeau in self.cadeau_group:
            cadeaux.append(cadeau.rect.center)
        for client in self.clients:
            client.Send({"action":'cadeau', 'cadeau': cadeaux})

    def send_puissaceTir(self):
        puiss1 = str(self.clients[0].nbTir) + "x" + str(self.clients[0].force)
        puiss2 = str(self.clients[1].nbTir) + "x" + str(self.clients[1].force)

        for client in self.clients:
            client.Send({"action":'puissanceTir', 'puissanceTir1':puiss1, 'puissanceTir2':puiss2})

    def update_channels(self, chicken_group):
        self.send_vie()
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
        self.cadeau_group = pygame.sprite.RenderClear()
        self.numVague = 1
        vague = Vague(1, self.chicken_group)

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

                '''Si la vague actuelle est terminée, on relance une nouvelle vague '''
                if vague.enCours == False:
                    print(str(self.numVague) + " " + str(vague.enCours))
                    vague = Vague(self.numVague, self.chicken_group)


                '''Si tous les poulets de la vague sont mort, on termine la vague '''
                if len(self.chicken_group) == 0:
                    vague.terminerVague()
                    self.numVague += 1
                    self.send_numVague()

                for chicken in self.chicken_group:
                    egg = random.randint(1, 4000)
                    cadeau = random.randint(1, 2000)
                    if egg == 42:
                        self.shot_group.add(Shot(1, chicken.rect.center, 's', 1))
                    if cadeau == 42:
                        self.cadeau_group.add(Cadeau(chicken.rect.center))
                self.send_shots()
                self.shot_group.update()

                self.send_cadeaux()
                self.cadeau_group.update()
                self.send_puissaceTir()


            pygame.display.flip()


# PROGRAMME INIT
if __name__ == '__main__':
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    my_server = MyServer(localaddr = (sys.argv[1],int(sys.argv[2])))
    my_server.launch_game()
