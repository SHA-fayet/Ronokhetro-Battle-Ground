from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random

# --- Game Configuration & State ---

# Camera-related variables
camera_pos = (0, 250, 450) 
fovY = 60

# Arena properties
ARENA_SIZE = 300
WALL_HEIGHT = 50

# --- Player Tank State ---
tank_pos = [0, 10, 0] 
tank_angle = 0.0 
turret_angle = 0.0 
TANK_MOVE_SPEED = 800.0 
TANK_ROTATE_SPEED = 400.0 
TURRET_ROTATE_SPEED = 420.0 
player_health = 100
player_fire_cooldown = 0.5

# --- Bullet Properties ---
player_bullets = [] 
enemy_bullets = []
BULLET_SPEED = 250.0 

# --- Enemy Properties ---
enemies = [] 
ENEMY_RADIUS = 25.0 
TANK_COLLISION_RADIUS = 35.0
ENEMY_FIRE_COOLDOWN = 2.0

# --- Obstacle Properties ---
obstacles = []
OBSTACLE_COUNT = 8
OBSTACLE_RADIUS = 20.0
OBSTACLE_COLLISION_RADIUS = 25.0

# --- Power-Up Properties ---
power_ups = []
POWER_UP_SPAWN_RATE = 10.0
last_power_up_spawn_time = 0.0
active_power_ups = {}

# --- NEW: Cheat Mode Properties ---
cheat_infinite_shells = False
cheat_auto_turret = False
emp_blast_cooldown = 10.0
last_emp_blast_time = 0.0
frozen_enemies = {} # To track frozen enemies and their unfreeze time

# --- Game State ---
score = 0
game_over = False
current_wave = 0
last_player_fire_time = 0.0

# --- Timekeeping ---
last_frame_time = 0.0
delta_time = 0.0

# --- Drawing Functions ---

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draws text on the screen at a fixed 2D position."""
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_arena():
    """Draws the arena floor and the four surrounding walls."""
    # Draw the floor
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE)
    glEnd()

    # Draw the walls
    glColor3f(0.4, 0.4, 0.5)
    glBegin(GL_QUADS)
    # Far wall
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    # Near wall
    glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f(ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f(ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    # Left wall
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    # Right wall
    glVertex3f(ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f(ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    glVertex3f(ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glEnd()

def draw_player_tank():
    """Draws the player's tank using basic shapes."""
    glPushMatrix()
    glTranslatef(tank_pos[0], tank_pos[1], tank_pos[2])
    glRotatef(tank_angle, 0, 1, 0)

    # Tank Body
    glColor3f(0.2, 0.5, 0.2)
    glPushMatrix()
    glScalef(30, 20, 50)
    glutSolidCube(1)
    glPopMatrix()

    # Tank Treads
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(-20, -5, 0)
    glScalef(10, 10, 60)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glTranslatef(20, -5, 0)
    glScalef(10, 10, 60)
    glutSolidCube(1)
    glPopMatrix()

    # Turret and Cannon
    glPushMatrix()
    glRotatef(turret_angle, 0, 1, 0) 
    # Turret
    glColor3f(0.25, 0.55, 0.25)
    glPushMatrix()
    glTranslatef(0, 15, 0)
    glScalef(20, 10, 20)
    glutSolidCube(1)
    glPopMatrix()
    # Cannon
    glColor3f(0.4, 0.4, 0.4)
    glPushMatrix()
    glTranslatef(0, 17, 10)
    gluCylinder(gluNewQuadric(), 4, 4, 40, 10, 10)
    glPopMatrix()
    glPopMatrix() 
    
    glPopMatrix() 

def draw_bullets():
    """Draws all active bullets from both player and enemies."""
    # Player bullets (Yellow)
    glColor3f(1.0, 0.8, 0.0) 
    for bullet in player_bullets:
        glPushMatrix()
        glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2])
        gluSphere(gluNewQuadric(), 3, 10, 10) 
        glPopMatrix()
    
    # Enemy bullets (Orange)
    glColor3f(1.0, 0.5, 0.0)
    for bullet in enemy_bullets:
        glPushMatrix()
        glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2])
        gluSphere(gluNewQuadric(), 3, 10, 10)
        glPopMatrix()

def draw_enemy_tanks():
    """Draws all enemy tanks with a proper model."""
    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy['pos'][0], enemy['pos'][1], enemy['pos'][2])
        glRotatef(enemy['angle'], 0, 1, 0)

        # Set color and size based on type
        if enemy['type'] == 'juggernaut':
            glColor3f(0.5, 0.05, 0.05) # Dark Red
            glScalef(1.2, 1.2, 1.2)
        else: # Scout
            glColor3f(0.9, 0.2, 0.2) # Lighter Red

        # Enemy Body
        glPushMatrix()
        glScalef(30, 20, 50)
        glutSolidCube(1)
        glPopMatrix()

        # Enemy Treads
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(-20, -5, 0)
        glScalef(10, 10, 60)
        glutSolidCube(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(20, -5, 0)
        glScalef(10, 10, 60)
        glutSolidCube(1)
        glPopMatrix()

        # Enemy Turret
        if enemy['type'] == 'juggernaut':
            glColor3f(0.4, 0.05, 0.05)
        else:
            glColor3f(0.7, 0.2, 0.2)
        glPushMatrix()
        glTranslatef(0, 15, 0)
        glScalef(20, 10, 20)
        glutSolidCube(1)
        glPopMatrix()

        # Enemy Cannon
        glColor3f(0.4, 0.4, 0.4)
        glPushMatrix()
        glTranslatef(0, 17, 10)
        gluCylinder(gluNewQuadric(), 4, 4, 40, 10, 10)
        glPopMatrix()

        glPopMatrix()

def draw_obstacles():
    """Draws all destructible obstacles."""
    for obstacle in obstacles:
        health_ratio = obstacle['health'] / 30.0
        if health_ratio > 0.66:
            glColor3f(0.5, 0.5, 0.5)
        elif health_ratio > 0.33:
            glColor3f(0.6, 0.4, 0.2)
        else:
            glColor3f(0.4, 0.1, 0.1)

        glPushMatrix()
        glTranslatef(obstacle['pos'][0], 15, obstacle['pos'][2])
        glScalef(30, 30, 30)
        glutSolidCube(1)
        glPopMatrix()

def draw_power_ups():
    """Draws all active power-ups."""
    for power_up in power_ups:
        glPushMatrix()
        glTranslatef(power_up['pos'][0], 15, power_up['pos'][2])
        glRotatef(time.time() * 100, 0, 1, 0) 

        if power_up['type'] == 'health':
            glColor3f(0.1, 1.0, 0.1)
            glutSolidCube(15)
        elif power_up['type'] == 'rapid_fire':
            glColor3f(1.0, 1.0, 0.1)
            gluCylinder(gluNewQuadric(), 10, 10, 20, 10, 10)
        elif power_up['type'] == 'speed':
            glColor3f(0.1, 0.1, 1.0)
            gluSphere(gluNewQuadric(), 10, 10, 10)
        
        glPopMatrix()

# --- Game Logic and State Updates ---

def reset_game():
    """Resets the game to its initial state."""
    global score, player_bullets, enemy_bullets, player_health, game_over, current_wave, obstacles, power_ups, active_power_ups, last_power_up_spawn_time, cheat_infinite_shells, cheat_auto_turret
    score = 0
    player_health = 100
    game_over = False
    player_bullets.clear()
    enemy_bullets.clear()
    enemies.clear()
    obstacles.clear()
    power_ups.clear()
    active_power_ups.clear()
    frozen_enemies.clear()
    cheat_infinite_shells = False
    cheat_auto_turret = False
    current_wave = 0
    last_power_up_spawn_time = time.time()
    spawn_obstacles()
    start_next_wave()

def spawn_obstacles():
    """Creates a set of destructible obstacles."""
    for _ in range(OBSTACLE_COUNT):
        x = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50)
        z = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50)
        obstacles.append({'pos': [x, 0, z], 'health': 30})

def start_next_wave():
    """Starts the next wave of enemies."""
    global current_wave
    current_wave += 1
    print(f"--- Starting Wave {current_wave} ---")
    
    for i in range(current_wave):
        spawn_enemy(i)

def spawn_enemy(enemy_id):
    """Spawns a single enemy with stats based on the current wave."""
    x = random.uniform(-ARENA_SIZE + 30, ARENA_SIZE - 30)
    z = random.uniform(-ARENA_SIZE + 30, ARENA_SIZE - 30)
    
    # Juggernauts start appearing from wave 3
    enemy_type = 'scout'
    if current_wave >= 3 and random.random() < 0.3: # 30% chance for a Juggernaut
        enemy_type = 'juggernaut'

    if enemy_type == 'juggernaut':
        speed = 15.0 + (current_wave * 1.0)
        health = 20 # Takes 2 hits
    else: # Scout
        speed = 25.0 + (current_wave * 2.0)
        health = 10 # Takes 1 hit

    enemies.append({
        'id': enemy_id,
        'pos': [x, 10, z],
        'angle': random.uniform(0, 360),
        'last_fire_time': time.time(),
        'speed': speed,
        'type': enemy_type,
        'health': health
    })

def update_bullets():
    """Updates the position of all bullets."""
    all_bullets = player_bullets + enemy_bullets
    for bullet in all_bullets[:]:
        bullet['pos'][0] += bullet['dir'][0] * BULLET_SPEED * delta_time
        bullet['pos'][2] += bullet['dir'][2] * BULLET_SPEED * delta_time
        
        if not (-ARENA_SIZE < bullet['pos'][0] < ARENA_SIZE and -ARENA_SIZE < bullet['pos'][2] < ARENA_SIZE):
            if bullet in player_bullets: player_bullets.remove(bullet)
            if bullet in enemy_bullets: enemy_bullets.remove(bullet)

def update_enemies():
    """Updates enemy AI: movement and firing."""
    current_time = time.time()
    for enemy in enemies:
        # Unfreeze enemy if its time is up
        if enemy['id'] in frozen_enemies and current_time > frozen_enemies[enemy['id']]:
            del frozen_enemies[enemy['id']]
        
        # If frozen, skip all logic
        if enemy['id'] in frozen_enemies:
            continue

        dir_x = tank_pos[0] - enemy['pos'][0]
        dir_z = tank_pos[2] - enemy['pos'][2]
        dist_to_player = math.sqrt(dir_x**2 + dir_z**2)

        enemy['angle'] = -math.degrees(math.atan2(dir_z, dir_x)) + 90

        if dist_to_player > 0:
            dir_x /= dist_to_player
            dir_z /= dist_to_player
        
        enemy['pos'][0] += dir_x * enemy['speed'] * delta_time
        enemy['pos'][2] += dir_z * enemy['speed'] * delta_time
        
        if dist_to_player < 200 and current_time - enemy['last_fire_time'] > ENEMY_FIRE_COOLDOWN:
            enemy_fire_bullet(enemy)
            enemy['last_fire_time'] = current_time

def update_power_ups():
    """Handles power-up spawning and expiration."""
    global last_power_up_spawn_time, active_power_ups
    current_time = time.time()
    
    if current_time - last_power_up_spawn_time > POWER_UP_SPAWN_RATE:
        spawn_power_up()
        last_power_up_spawn_time = current_time
    
    for power_up_type in list(active_power_ups.keys()):
        if current_time > active_power_ups[power_up_type]:
            print(f"{power_up_type.replace('_', ' ').title()} expired!")
            del active_power_ups[power_up_type]

def spawn_power_up():
    """Spawns a new random power-up."""
    if len(power_ups) >= 3: return
    
    x = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50)
    z = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50)
    power_up_type = random.choice(['health', 'rapid_fire', 'speed'])
    
    power_ups.append({'pos': [x, 0, z], 'type': power_up_type})
    print(f"Spawned a {power_up_type.replace('_', ' ')} power-up!")


def resolve_collisions():
    """Checks and resolves overlaps between all tanks and obstacles."""
    all_tanks = [{'pos': tank_pos, 'radius': TANK_COLLISION_RADIUS}] + [{'pos': e['pos'], 'radius': TANK_COLLISION_RADIUS} for e in enemies]
    
    # Tank vs Tank
    for i in range(len(all_tanks)):
        for j in range(i + 1, len(all_tanks)):
            obj_a = all_tanks[i]
            obj_b = all_tanks[j]
            dist_x = obj_a['pos'][0] - obj_b['pos'][0]
            dist_z = obj_a['pos'][2] - obj_b['pos'][2]
            dist = math.sqrt(dist_x**2 + dist_z**2)
            
            if dist < obj_a['radius'] + obj_b['radius'] and dist > 0:
                overlap = (obj_a['radius'] + obj_b['radius']) - dist
                push_x = (dist_x / dist) * (overlap / 2)
                push_z = (dist_z / dist) * (overlap / 2)
                obj_a['pos'][0] += push_x
                obj_a['pos'][2] += push_z
                obj_b['pos'][0] -= push_x
                obj_b['pos'][2] -= push_z
    
    # Tanks vs Obstacles
    for tank in all_tanks:
        for obstacle in obstacles:
            dist_x = tank['pos'][0] - obstacle['pos'][0]
            dist_z = tank['pos'][2] - obstacle['pos'][2]
            dist = math.sqrt(dist_x**2 + dist_z**2)
            
            if dist < tank['radius'] + OBSTACLE_COLLISION_RADIUS and dist > 0:
                overlap = (tank['radius'] + OBSTACLE_COLLISION_RADIUS) - dist
                push_x = (dist_x / dist) * overlap
                push_z = (dist_z / dist) * overlap
                tank['pos'][0] += push_x
                tank['pos'][2] += push_z

def check_bullet_collisions():
    """Checks for all bullet-related collisions."""
    global score, player_health
    
    # Check player bullets
    for bullet in player_bullets[:]:
        hit = False
        for enemy in enemies[:]:
            dist_sq = (bullet['pos'][0] - enemy['pos'][0])**2 + (bullet['pos'][2] - enemy['pos'][2])**2
            if dist_sq < ENEMY_RADIUS**2:
                if bullet in player_bullets: player_bullets.remove(bullet)
                enemy['health'] -= 10
                if enemy['health'] <= 0:
                    if enemy in enemies: enemies.remove(enemy)
                    score += 10
                hit = True; break
        if hit: continue
        for obstacle in obstacles[:]:
            dist_sq = (bullet['pos'][0] - obstacle['pos'][0])**2 + (bullet['pos'][2] - obstacle['pos'][2])**2
            if dist_sq < OBSTACLE_RADIUS**2:
                if bullet in player_bullets: player_bullets.remove(bullet)
                obstacle['health'] -= 10
                if obstacle['health'] <= 0: obstacles.remove(obstacle)
                break
    
    # Check enemy bullets
    player_radius_sq = 25.0**2
    for bullet in enemy_bullets[:]:
        hit = False
        dist_sq = (bullet['pos'][0] - tank_pos[0])**2 + (bullet['pos'][2] - tank_pos[2])**2
        if dist_sq < player_radius_sq:
            if bullet in enemy_bullets: enemy_bullets.remove(bullet)
            player_health -= 10
            hit = True
        if hit: continue
        for obstacle in obstacles[:]:
            dist_sq = (bullet['pos'][0] - obstacle['pos'][0])**2 + (bullet['pos'][2] - obstacle['pos'][2])**2
            if dist_sq < OBSTACLE_RADIUS**2:
                if bullet in enemy_bullets: enemy_bullets.remove(bullet)
                obstacle['health'] -= 10
                if obstacle['health'] <= 0: obstacles.remove(obstacle)
                break
    
    if not enemies and not game_over:
        start_next_wave()

def check_power_up_collection():
    """Checks if the player has collected a power-up."""
    global player_health
    for power_up in power_ups[:]:
        dist_sq = (tank_pos[0] - power_up['pos'][0])**2 + (tank_pos[2] - power_up['pos'][2])**2
        if dist_sq < 30**2:
            apply_power_up(power_up['type'])
            power_ups.remove(power_up)

def apply_power_up(power_up_type):
    """Applies the effect of a collected power-up."""
    global player_health
    print(f"Collected {power_up_type.replace('_', ' ')}!")
    if power_up_type == 'health':
        player_health = min(100, player_health + 25)
    else:
        active_power_ups[power_up_type] = time.time() + 10

def fire_bullet():
    """Creates a new player bullet."""
    final_angle = tank_angle + turret_angle
    final_angle_rad = math.radians(final_angle)
    dir_x, dir_z = math.sin(final_angle_rad), math.cos(final_angle_rad)
    cannon_length = 50.0
    offset_x, offset_z = cannon_length * dir_x, cannon_length * dir_z
    start_x, start_z, start_y = tank_pos[0] + offset_x, tank_pos[2] + offset_z, 17
    player_bullets.append({'pos': [start_x, start_y, start_z], 'dir': [dir_x, 0, dir_z]})

def enemy_fire_bullet(enemy):
    """Creates a new enemy bullet."""
    angle_rad = math.radians(enemy['angle'])
    dir_x, dir_z = math.sin(angle_rad), math.cos(angle_rad)
    cannon_length = 50.0
    offset_x, offset_z = cannon_length * dir_x, cannon_length * dir_z
    start_x, start_z, start_y = enemy['pos'][0] + offset_x, enemy['pos'][2] + offset_z, 17
    enemy_bullets.append({'pos': [start_x, start_y, start_y], 'dir': [dir_x, 0, dir_z]})

# --- Input Handlers ---

def keyboardListener(key, x, y):
    """Handles keyboard inputs for tank movement."""
    global tank_pos, tank_angle, cheat_infinite_shells, cheat_auto_turret, last_emp_blast_time
    if game_over: return
    
    speed_multiplier = 1.5 if 'speed' in active_power_ups else 1.0
    move_amount = TANK_MOVE_SPEED * delta_time * speed_multiplier
    rotate_amount = TANK_ROTATE_SPEED * delta_time * speed_multiplier
    
    angle_rad = math.radians(tank_angle)
    
    if key == b'w':
        tank_pos[0] += math.sin(angle_rad) * move_amount
        tank_pos[2] += math.cos(angle_rad) * move_amount
    if key == b's':
        tank_pos[0] -= math.sin(angle_rad) * move_amount
        tank_pos[2] -= math.cos(angle_rad) * move_amount
    
    buffer = 25
    tank_pos[0] = max(-ARENA_SIZE + buffer, min(ARENA_SIZE - buffer, tank_pos[0]))
    tank_pos[2] = max(-ARENA_SIZE + buffer, min(ARENA_SIZE - buffer, tank_pos[2]))

    if key == b'a':
        tank_angle += rotate_amount
    if key == b'd':
        tank_angle -= rotate_amount
    
    # --- NEW: Cheat Mode Toggles ---
    if key == b'1':
        cheat_infinite_shells = not cheat_infinite_shells
        print(f"Cheat - Infinite Shells: {'ON' if cheat_infinite_shells else 'OFF'}")
    if key == b'2':
        current_time = time.time()
        if current_time - last_emp_blast_time > emp_blast_cooldown:
            print("Cheat - EMP Blast Activated!")
            for enemy in enemies:
                frozen_enemies[enemy['id']] = current_time + 3 # Freeze for 3 seconds
            last_emp_blast_time = current_time
        else:
            print("EMP Blast on cooldown.")
    if key == b'3':
        cheat_auto_turret = not cheat_auto_turret
        print(f"Cheat - Auto Turret: {'ON' if cheat_auto_turret else 'OFF'}")


def specialKeyListener(key, x, y):
    """Handles special key inputs for turret rotation."""
    global turret_angle
    if game_over: return
    rotate_amount = TURRET_ROTATE_SPEED * delta_time
    if key == GLUT_KEY_LEFT: turret_angle += rotate_amount
    if key == GLUT_KEY_RIGHT: turret_angle -= rotate_amount

def mouseListener(button, state, x, y):
    """Handles mouse inputs for firing bullets."""
    global last_player_fire_time
    if game_over: return
    
    current_time = time.time()
    cooldown = 0 if cheat_infinite_shells else (player_fire_cooldown / 2.0 if 'rapid_fire' in active_power_ups else player_fire_cooldown)

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and current_time - last_player_fire_time > cooldown:
        fire_bullet()
        last_player_fire_time = current_time

# --- Core OpenGL Functions ---

def reshape(w, h):
    """Called when the window is resized."""
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    aspect_ratio = w / h
    gluPerspective(fovY, aspect_ratio, 1.0, 1000.0)
    glMatrixMode(GL_MODELVIEW)

def setupCamera():
    """Configures the camera's view matrix (point of view)."""
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], 0, 0, 0, 0, 1, 0)

def idle():
    """Idle function that runs continuously."""
    global last_frame_time, delta_time, game_over, turret_angle
    
    current_time = time.time()
    if last_frame_time == 0: last_frame_time = current_time
    delta_time = current_time - last_frame_time
    last_frame_time = current_time
    
    if not game_over:
        # Auto-turret logic
        if cheat_auto_turret and enemies:
            # Find the closest enemy
            closest_enemy = min(enemies, key=lambda e: (tank_pos[0] - e['pos'][0])**2 + (tank_pos[2] - e['pos'][2])**2)
            dir_x = closest_enemy['pos'][0] - tank_pos[0]
            dir_z = closest_enemy['pos'][2] - tank_pos[2]
            target_angle = -math.degrees(math.atan2(dir_z, dir_x)) + 90
            turret_angle = target_angle - tank_angle


        update_bullets()
        update_enemies()
        update_power_ups()
        
        for _ in range(5):
            resolve_collisions()
            
        check_bullet_collisions()
        check_power_up_collection()
    
    if player_health <= 0 and not game_over:
        game_over = True
        print("Game Over!")

    glutPostRedisplay()

def showScreen():
    """Display function to render the entire game scene."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    setupCamera()

    # Draw all game elements
    draw_arena()
    if not game_over:
        draw_player_tank()
    draw_bullets()
    draw_enemy_tanks()
    draw_obstacles()
    draw_power_ups()

    # Display game info text
    draw_text(10, 770, f"Score: {score}")
    draw_text(10, 740, f"Health: {player_health}")
    draw_text(10, 710, f"Wave: {current_wave}")

    # Display active power-ups
    y_offset = 680
    for power_up, end_time in active_power_ups.items():
        remaining_time = max(0, end_time - time.time())
        draw_text(10, y_offset, f"{power_up.replace('_', ' ').title()}: {remaining_time:.1f}s")
        y_offset -= 30

    if game_over:
        draw_text(450, 400, "GAME OVER")

    glutSwapBuffers()

# --- Main Function ---

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Ronokhetro")

    glClearColor(0.1, 0.2, 0.35, 1.0)
    glEnable(GL_DEPTH_TEST)

    glutReshapeFunc(reshape)
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    global last_frame_time
    last_frame_time = time.time()

    reset_game()

    glutMainLoop()

if __name__ == "__main__":
    main()
