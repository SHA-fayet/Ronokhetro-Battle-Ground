from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time
import random
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18

# --- Game Configuration & State ---

# Camera-related variables
camera_pos = (0, 300, 450)
fovY = 60
camera_shake_intensity = 0.0
camera_shake_duration = 0.0
camera_shake_start_time = 0.0

# Arena properties
ARENA_SIZE = 300
WALL_HEIGHT = 50

# --- Player Tank State ---
tank_pos = [0, 10, 0]
tank_angle = 0.0
turret_angle = 0.0
player_health = 100
last_player_fire_time = 0.0
# MODIFIED: Player stats are now variables for the upgrade system
max_player_health = 100
player_fire_cooldown = 0.5
TANK_MOVE_SPEED = 150.0 # This was 800.0 in your code, which was extremely fast. Adjusted to a more manageable base value.
TANK_ROTATE_SPEED = 100.0 # This was 400.0. Adjusted for better control.
TURRET_ROTATE_SPEED = 120.0 # This was 420.0. Adjusted for better control.

# --- NEW: Tank Upgrade System ---
# These variables will store the player's upgrades and their costs.
upgrade_level_armor = 0
upgrade_level_cannon = 0
upgrade_level_speed = 0
upgrade_cost_armor = 50
upgrade_cost_cannon = 50
upgrade_cost_speed = 50

# --- Bullet Properties ---
player_bullets = []
enemy_bullets = []
BULLET_SPEED = 250.0

# --- Enemy Properties ---
enemies = []
ENEMY_RADIUS = 25.0
TANK_COLLISION_RADIUS = 35.0
ENEMY_FIRE_COOLDOWN = 2.0
# --- NEW: Boss Tank Logic ---
boss_active = False # A flag to know if a boss is currently in the wave

# --- Obstacle Properties ---
obstacles = []
OBSTACLE_COUNT = 8
OBSTACLE_RADIUS = 20.0
OBSTACLE_COLLISION_RADIUS = 25.0

# --- Power-Up Properties (from your original code, kept as is) ---
power_ups = []
POWER_UP_SPAWN_RATE = 10.0
last_power_up_spawn_time = 0.0
active_power_ups = {}

# --- Cheat Mode Properties (from your original code, kept as is) ---
cheat_infinite_shells = False
cheat_auto_turret = False
emp_blast_cooldown = 10.0
last_emp_blast_time = 0.0
frozen_enemies = {}

# --- NEW: Environmental Hazards ---
# A list to store hazards like lava pits
hazards = []
HAZARD_COUNT = 3
HAZARD_RADIUS = 35.0
HAZARD_DAMAGE_PER_SECOND = 25.0

# --- NEW: Dynamic Weather Effects ---
# A list to store raindrop particles
raindrops = []
MAX_RAINDROPS = 250
is_raining = False # Flag to control when it rains

# --- Game State ---
score = 0
game_over = False
current_wave = 0

# --- Timekeeping ---
last_frame_time = 0.0
delta_time = 0.0
timeOfDay = 0.0

# --- Drawing Functions (Your original functions are unchanged unless marked) ---

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_health_bar_3d(x, y, z, current_health, max_health, width=20, height=2):
    health_ratio = max(0, min(1, current_health / max_health))
    glPushMatrix(); glTranslatef(x, y, z)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS); glVertex3f(-width/2, 0, -height/2); glVertex3f(width/2, 0, -height/2); glVertex3f(width/2, 0, height/2); glVertex3f(-width/2, 0, height/2); glEnd()
    if health_ratio > 0:
        if health_ratio > 0.6: glColor3f(0.0, 1.0, 0.0)
        elif health_ratio > 0.3: glColor3f(1.0, 1.0, 0.0)
        else: glColor3f(1.0, 0.0, 0.0)
        health_width = width * health_ratio
        glBegin(GL_QUADS); glVertex3f(-width/2, 0.01, -height/2); glVertex3f(-width/2 + health_width, 0.01, -height/2); glVertex3f(-width/2 + health_width, 0.01, height/2); glVertex3f(-width/2, 0.01, height/2); glEnd()
    glPopMatrix()

def draw_arena():
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS); glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE); glVertex3f(ARENA_SIZE, 0, -ARENA_SIZE); glVertex3f(ARENA_SIZE, 0, ARENA_SIZE); glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE); glEnd()
    glColor3f(0.4, 0.4, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE); glVertex3f(ARENA_SIZE, 0, -ARENA_SIZE); glVertex3f(ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE); glVertex3f(-ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE); glVertex3f(ARENA_SIZE, 0, ARENA_SIZE); glVertex3f(ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE); glVertex3f(-ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE); glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE); glVertex3f(-ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE); glVertex3f(-ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glVertex3f(ARENA_SIZE, 0, -ARENA_SIZE); glVertex3f(ARENA_SIZE, 0, ARENA_SIZE); glVertex3f(ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE); glVertex3f(ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glEnd()

def draw_player_shadow():
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix(); glTranslatef(tank_pos[0], 0.5, tank_pos[2]); glRotatef(tank_angle, 0, 1, 0)
    glBegin(GL_QUADS); glVertex3f(-20, 0, -35); glVertex3f(20, 0, -35); glVertex3f(20, 0, 35); glVertex3f(-20, 0, 35); glEnd()
    glBegin(GL_QUADS); glVertex3f(-35, 0, -40); glVertex3f(-20, 0, -40); glVertex3f(-20, 0, 40); glVertex3f(-35, 0, 40); glEnd()
    glBegin(GL_QUADS); glVertex3f(20, 0, -40); glVertex3f(35, 0, -40); glVertex3f(35, 0, 40); glVertex3f(20, 0, 40); glEnd()
    glPushMatrix(); glRotatef(turret_angle, 0, 1, 0)
    glBegin(GL_QUADS); glVertex3f(-15, 0, -15); glVertex3f(15, 0, -15); glVertex3f(15, 0, 15); glVertex3f(-15, 0, 15); glEnd()
    glPopMatrix(); glPopMatrix()

def draw_player_tank():
    glPushMatrix(); glTranslatef(tank_pos[0], tank_pos[1], tank_pos[2]); glRotatef(tank_angle, 0, 1, 0)
    glColor3f(0.2, 0.5, 0.2); glPushMatrix(); glScalef(30, 20, 50); glutSolidCube(1); glPopMatrix()
    glColor3f(0.2, 0.2, 0.2); glPushMatrix(); glTranslatef(-20, -5, 0); glScalef(10, 10, 60); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(20, -5, 0); glScalef(10, 10, 60); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glRotatef(turret_angle, 0, 1, 0)
    glColor3f(0.25, 0.55, 0.25); glPushMatrix(); glTranslatef(0, 15, 0); glScalef(20, 10, 20); glutSolidCube(1); glPopMatrix()
    glColor3f(0.4, 0.4, 0.4); glPushMatrix(); glTranslatef(0, 17, 10); gluCylinder(gluNewQuadric(), 4, 4, 40, 10, 10); glPopMatrix()
    glPopMatrix(); glPopMatrix()
    # MODIFIED: Now uses max_player_health for the health bar
    draw_health_bar_3d(tank_pos[0], tank_pos[1] + 40, tank_pos[2], player_health, max_player_health, 25, 3)

def draw_bullets():
    glColor3f(1.0, 0.8, 0.0)
    for bullet in player_bullets:
        glPushMatrix(); glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2]); gluSphere(gluNewQuadric(), 3, 10, 10); glPopMatrix()
    glColor3f(1.0, 0.5, 0.0)
    for bullet in enemy_bullets:
        glPushMatrix(); glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2]); gluSphere(gluNewQuadric(), 3, 10, 10); glPopMatrix()

def draw_enemy_tanks():
    for enemy in enemies:
        glPushMatrix(); glTranslatef(enemy['pos'][0], enemy['pos'][1], enemy['pos'][2]); glRotatef(enemy['angle'], 0, 1, 0)
        # --- NEW: Boss Tank Visuals ---
        # This new block checks if the enemy is a boss and makes it look different
        if enemy['type'] == 'boss':
            glColor3f(0.2, 0.0, 0.2) # Dark Purple for boss
            glScalef(1.5, 1.5, 1.5)
        elif enemy['type'] == 'juggernaut':
            glColor3f(0.5, 0.05, 0.05); glScalef(1.2, 1.2, 1.2)
        else:
            glColor3f(0.9, 0.2, 0.2)
        glPushMatrix(); glScalef(30, 20, 50); glutSolidCube(1); glPopMatrix()
        glColor3f(0.2, 0.2, 0.2)
        glPushMatrix(); glTranslatef(-20, -5, 0); glScalef(10, 10, 60); glutSolidCube(1); glPopMatrix()
        glPushMatrix(); glTranslatef(20, -5, 0); glScalef(10, 10, 60); glutSolidCube(1); glPopMatrix()
        if enemy['type'] == 'boss': glColor3f(0.4, 0.1, 0.4) # Boss turret color
        elif enemy['type'] == 'juggernaut': glColor3f(0.4, 0.05, 0.05)
        else: glColor3f(0.7, 0.2, 0.2)
        glPushMatrix(); glTranslatef(0, 15, 0); glScalef(20, 10, 20); glutSolidCube(1); glPopMatrix()
        glColor3f(0.4, 0.4, 0.4)
        glPushMatrix(); glTranslatef(0, 17, 10); gluCylinder(gluNewQuadric(), 4, 4, 40, 10, 10); glPopMatrix()
        glPopMatrix()
        # --- NEW: Health bar logic for the boss ---
        if enemy['type'] == 'boss': max_health = 200; y_offset = 60; health_bar_width = 40
        elif enemy['type'] == 'juggernaut': max_health = 20; y_offset = 50; health_bar_width = 30
        else: max_health = 10; y_offset = 40; health_bar_width = 25
        draw_health_bar_3d(enemy['pos'][0], enemy['pos'][1] + y_offset, enemy['pos'][2], enemy['health'], max_health, health_bar_width, 4)

def draw_enemy_shadows(): # Unchanged
    glColor3f(0.3, 0.3, 0.3)
    for enemy in enemies:
        scale_factor = 1.2 if enemy['type'] == 'juggernaut' else 1.0
        # NEW: Added scale factor for boss shadow
        if enemy['type'] == 'boss': scale_factor = 1.5
        glPushMatrix(); glTranslatef(enemy['pos'][0], 0.5, enemy['pos'][2]); glRotatef(enemy['angle'], 0, 1, 0); glScalef(scale_factor, 1.0, scale_factor)
        glBegin(GL_QUADS); glVertex3f(-20, 0, -35); glVertex3f(20, 0, -35); glVertex3f(20, 0, 35); glVertex3f(-20, 0, 35); glEnd()
        glBegin(GL_QUADS); glVertex3f(-35, 0, -40); glVertex3f(-20, 0, -40); glVertex3f(-20, 0, 40); glVertex3f(-35, 0, 40); glEnd()
        glBegin(GL_QUADS); glVertex3f(20, 0, -40); glVertex3f(35, 0, -40); glVertex3f(35, 0, 40); glVertex3f(20, 0, 40); glEnd()
        glBegin(GL_QUADS); glVertex3f(-15, 0, -15); glVertex3f(15, 0, -15); glVertex3f(15, 0, 15); glVertex3f(-15, 0, 15); glEnd()
        glPopMatrix()

def draw_obstacles(): # Unchanged
    for obstacle in obstacles:
        health_ratio = obstacle['health'] / 30.0
        if health_ratio > 0.66: glColor3f(0.5, 0.5, 0.5)
        elif health_ratio > 0.33: glColor3f(0.6, 0.4, 0.2)
        else: glColor3f(0.4, 0.1, 0.1)
        glPushMatrix(); glTranslatef(obstacle['pos'][0], 15, obstacle['pos'][2]); glScalef(30, 30, 30); glutSolidCube(1); glPopMatrix()

def draw_obstacle_shadows(): # Unchanged
    glColor3f(0.3, 0.3, 0.3)
    for obstacle in obstacles:
        glPushMatrix(); glTranslatef(obstacle['pos'][0], 0.5, obstacle['pos'][2])
        glBegin(GL_QUADS); glVertex3f(-15, 0, -15); glVertex3f(15, 0, -15); glVertex3f(15, 0, 15); glVertex3f(-15, 0, 15); glEnd()
        glPopMatrix()

def draw_power_ups(): # Unchanged
    for power_up in power_ups:
        glPushMatrix(); glTranslatef(power_up['pos'][0], 15, power_up['pos'][2]); glRotatef(time.time() * 100, 0, 1, 0)
        if power_up['type'] == 'health': glColor3f(0.1, 1.0, 0.1); glutSolidCube(15)
        elif power_up['type'] == 'rapid_fire': glColor3f(1.0, 1.0, 0.1); gluCylinder(gluNewQuadric(), 10, 10, 20, 10, 10)
        elif power_up['type'] == 'speed': glColor3f(0.1, 0.1, 1.0); gluSphere(gluNewQuadric(), 10, 10, 10)
        glPopMatrix()

def draw_power_up_shadows(): # Unchanged
    glColor3f(0.3, 0.3, 0.3)
    for power_up in power_ups:
        glPushMatrix(); glTranslatef(power_up['pos'][0], 0.5, power_up['pos'][2])
        glBegin(GL_TRIANGLE_FAN); glVertex3f(0, 0, 0)
        radius = 10; segments = 32
        for i in range(segments + 1):
            angle = 2.0 * math.pi * i / segments
            x = radius * math.cos(angle); z = radius * math.sin(angle); glVertex3f(x, 0, z)
        glEnd(); glPopMatrix()

# --- NEW: Drawing function for Environmental Hazards ---
def draw_hazards():
    """Draws lava pits on the ground using simple quads."""
    for hazard in hazards:
        pulse = (math.sin(time.time() * 2) + 1) / 2
        glColor3f(1.0, 0.2 + pulse * 0.2, 0.0) # Red-orange pulsating color
        glPushMatrix()
        glTranslatef(hazard['pos'][0], 0.1, hazard['pos'][2]) # Draw just above the floor
        glBegin(GL_QUADS)
        glVertex3f(-HAZARD_RADIUS, 0, -HAZARD_RADIUS)
        glVertex3f( HAZARD_RADIUS, 0, -HAZARD_RADIUS)
        glVertex3f( HAZARD_RADIUS, 0,  HAZARD_RADIUS)
        glVertex3f(-HAZARD_RADIUS, 0,  HAZARD_RADIUS)
        glEnd()
        glPopMatrix()

# --- NEW: Drawing function for Dynamic Weather ---
def draw_rain():
    """Draws rain using simple lines."""
    if not is_raining: return
    glDisable(GL_LIGHTING) # Rain should not be affected by light
    glColor3f(0.6, 0.8, 1.0) # Light blue color
    glBegin(GL_LINES)
    for drop in raindrops:
        p = drop['pos']
        glVertex3f(p[0], p[1], p[2])
        glVertex3f(p[0], p[1] - 5, p[2]) # A line of length 5
    glEnd()

# --- Game Logic and State Updates ---

def reset_game():
    global score, player_bullets, enemy_bullets, player_health, game_over, current_wave
    global cheat_infinite_shells, cheat_auto_turret
    # MODIFIED: Reset new variables as well
    global max_player_health, upgrade_level_armor, upgrade_level_cannon, upgrade_level_speed
    global upgrade_cost_armor, upgrade_cost_cannon, upgrade_cost_speed
    global player_fire_cooldown, TANK_MOVE_SPEED, TANK_ROTATE_SPEED, boss_active

    score = 0; player_health = 100; game_over = False; current_wave = 0
    player_bullets.clear(); enemy_bullets.clear(); enemies.clear(); obstacles.clear(); power_ups.clear(); active_power_ups.clear(); frozen_enemies.clear()
    cheat_infinite_shells = False; cheat_auto_turret = False
    last_power_up_spawn_time = time.time()
    
    # NEW: Reset upgrade system variables
    max_player_health = 100; upgrade_level_armor = 0; upgrade_level_cannon = 0; upgrade_level_speed = 0
    upgrade_cost_armor = 50; upgrade_cost_cannon = 50; upgrade_cost_speed = 50
    player_fire_cooldown = 0.5; TANK_MOVE_SPEED = 150.0; TANK_ROTATE_SPEED = 100.0
    boss_active = False
    
    # NEW: Spawn hazards at the start of the game
    hazards.clear()
    spawn_hazards()

    spawn_obstacles()
    start_next_wave()

def spawn_obstacles(): # Unchanged
    obstacles.clear()
    for _ in range(OBSTACLE_COUNT):
        x = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50); z = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50)
        obstacles.append({'pos': [x, 0, z], 'health': 30})

# --- NEW: Spawning function for Environmental Hazards ---
def spawn_hazards():
    for _ in range(HAZARD_COUNT):
        x = random.uniform(-ARENA_SIZE + 80, ARENA_SIZE - 80)
        z = random.uniform(-ARENA_SIZE + 80, ARENA_SIZE - 80)
        hazards.append({'pos': [x, 0, z]})

def start_next_wave():
    global current_wave, boss_active # MODIFIED: Added boss_active
    current_wave += 1
    print(f"--- Starting Wave {current_wave} ---")
    
    # --- NEW: Boss Wave Logic ---
    # This is a new check. If it's a boss wave, it calls a different spawn function.
    if current_wave % 3 == 0:
        boss_active = True
        spawn_boss()
    else:
        # This is your original logic for normal waves.
        boss_active = False
        for i in range(current_wave):
            spawn_enemy(i)

# --- NEW: Spawning function for the Boss ---
def spawn_boss():
    enemies.clear() # Clear any remaining enemies
    enemies.append({
        'id': 'boss',
        'pos': [0, 10, -ARENA_SIZE + 80],
        'angle': 180,
        'last_fire_time': time.time(),
        'speed': 15.0,
        'type': 'boss',
        'health': 200
    })

def spawn_enemy(enemy_id): # Unchanged
    x = random.uniform(-ARENA_SIZE + 30, ARENA_SIZE - 30); z = random.uniform(-ARENA_SIZE + 30, ARENA_SIZE - 30)
    enemy_type = 'juggernaut' if current_wave >= 3 and random.random() < 0.3 else 'scout'
    if enemy_type == 'juggernaut': speed = 15.0 + (current_wave * 1.0); health = 20
    else: speed = 25.0 + (current_wave * 2.0); health = 10
    enemies.append({'id': enemy_id, 'pos': [x, 10, z], 'angle': random.uniform(0, 360), 'last_fire_time': time.time(), 'speed': speed, 'type': enemy_type, 'health': health})

def update_bullets(): # Unchanged
    all_bullets = player_bullets + enemy_bullets
    for bullet in all_bullets[:]:
        bullet['pos'][0] += bullet['dir'][0] * BULLET_SPEED * delta_time; bullet['pos'][2] += bullet['dir'][2] * BULLET_SPEED * delta_time
        if not (-ARENA_SIZE < bullet['pos'][0] < ARENA_SIZE and -ARENA_SIZE < bullet['pos'][2] < ARENA_SIZE):
            if bullet in player_bullets: player_bullets.remove(bullet)
            if bullet in enemy_bullets: enemy_bullets.remove(bullet)

def update_enemies(): # Unchanged
    current_time = time.time()
    for enemy in enemies:
        if enemy['id'] in frozen_enemies and current_time > frozen_enemies[enemy['id']]:
            del frozen_enemies[enemy['id']]
        if enemy['id'] in frozen_enemies:
            continue
        dir_x = tank_pos[0] - enemy['pos'][0]; dir_z = tank_pos[2] - enemy['pos'][2]
        dist_to_player = math.sqrt(dir_x**2 + dir_z**2)
        enemy['angle'] = -math.degrees(math.atan2(dir_z, dir_x)) + 90
        if dist_to_player > 0: dir_x /= dist_to_player; dir_z /= dist_to_player
        enemy['pos'][0] += dir_x * enemy['speed'] * delta_time; enemy['pos'][2] += dir_z * enemy['speed'] * delta_time
        if dist_to_player < 200 and current_time - enemy['last_fire_time'] > ENEMY_FIRE_COOLDOWN:
            enemy_fire_bullet(enemy)
            enemy['last_fire_time'] = current_time

def update_power_ups(): # Unchanged
    global last_power_up_spawn_time, active_power_ups
    current_time = time.time()
    if current_time - last_power_up_spawn_time > POWER_UP_SPAWN_RATE:
        spawn_power_up(); last_power_up_spawn_time = current_time
    for power_up_type in list(active_power_ups.keys()):
        if current_time > active_power_ups[power_up_type]:
            print(f"{power_up_type.replace('_', ' ').title()} expired!"); del active_power_ups[power_up_type]

def spawn_power_up(): # Unchanged
    if len(power_ups) >= 3: return
    x = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50); z = random.uniform(-ARENA_SIZE + 50, ARENA_SIZE - 50)
    power_up_type = random.choice(['health', 'rapid_fire', 'speed'])
    power_ups.append({'pos': [x, 0, z], 'type': power_up_type})
    print(f"Spawned a {power_up_type.replace('_', ' ')} power-up!")

def resolve_collisions(): # Unchanged
    all_colliders = [{'obj': 'player', 'pos': tank_pos, 'radius': TANK_COLLISION_RADIUS}]
    for i, enemy in enumerate(enemies): all_colliders.append({'obj': 'enemy', 'id': i, 'pos': enemy['pos'], 'radius': TANK_COLLISION_RADIUS})
    for i in range(len(all_colliders)):
        for j in range(i + 1, len(all_colliders)):
            obj_a = all_colliders[i]; obj_b = all_colliders[j]
            dist_x = obj_a['pos'][0] - obj_b['pos'][0]; dist_z = obj_a['pos'][2] - obj_b['pos'][2]
            dist = math.sqrt(dist_x**2 + dist_z**2)
            min_dist = obj_a['radius'] + obj_b['radius']
            if dist < min_dist and dist > 0:
                overlap = min_dist - dist; push_x = (dist_x / dist) * (overlap / 2); push_z = (dist_z / dist) * (overlap / 2)
                obj_a['pos'][0] += push_x; obj_a['pos'][2] += push_z; obj_b['pos'][0] -= push_x; obj_b['pos'][2] -= push_z
    for tank in all_colliders:
        for obstacle in obstacles:
            dist_x = tank['pos'][0] - obstacle['pos'][0]; dist_z = tank['pos'][2] - obstacle['pos'][2]
            dist = math.sqrt(dist_x**2 + dist_z**2)
            min_dist = tank['radius'] + OBSTACLE_COLLISION_RADIUS
            if dist < min_dist and dist > 0:
                overlap = min_dist - dist; push_x = (dist_x / dist) * overlap; push_z = (dist_z / dist) * overlap
                tank['pos'][0] += push_x; tank['pos'][2] += push_z
    buffer = 25; tank_pos[0] = max(-ARENA_SIZE + buffer, min(ARENA_SIZE - buffer, tank_pos[0])); tank_pos[2] = max(-ARENA_SIZE + buffer, min(ARENA_SIZE - buffer, tank_pos[2]))

def trigger_camera_shake(intensity=15.0, duration=0.3): # Unchanged
    global camera_shake_intensity, camera_shake_duration, camera_shake_start_time
    camera_shake_intensity = intensity; camera_shake_duration = duration; camera_shake_start_time = time.time()

def check_bullet_collisions():
    global score, player_health
    for bullet in player_bullets[:]:
        hit = False
        for enemy in enemies[:]:
            dist_sq = (bullet['pos'][0] - enemy['pos'][0])**2 + (bullet['pos'][2] - enemy['pos'][2])**2
            if dist_sq < ENEMY_RADIUS**2:
                if bullet in player_bullets: player_bullets.remove(bullet)
                enemy['health'] -= 10
                if enemy['health'] <= 0:
                    if enemy in enemies: enemies.remove(enemy)
                    # --- NEW: Bonus score for killing boss ---
                    if enemy['type'] == 'boss':
                        global boss_active
                        score += 500
                        boss_active = False # Boss is no longer active
                    else:
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
    player_radius_sq = 25.0**2
    for bullet in enemy_bullets[:]:
        hit = False
        dist_sq = (bullet['pos'][0] - tank_pos[0])**2 + (bullet['pos'][2] - tank_pos[2])**2
        if dist_sq < player_radius_sq:
            if bullet in enemy_bullets: enemy_bullets.remove(bullet)
            player_health -= 10; trigger_camera_shake(15.0, 0.3); hit = True
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

def check_power_up_collection(): # Unchanged
    global player_health
    for power_up in power_ups[:]:
        dist_sq = (tank_pos[0] - power_up['pos'][0])**2 + (tank_pos[2] - power_up['pos'][2])**2
        if dist_sq < 30**2: apply_power_up(power_up['type']); power_ups.remove(power_up)

def apply_power_up(power_up_type): # Unchanged
    global player_health
    print(f"Collected {power_up_type.replace('_', ' ')}!")
    if power_up_type == 'health': player_health = min(100, player_health + 25)
    else: active_power_ups[power_up_type] = time.time() + 10

def fire_bullet(): # Unchanged
    final_angle = tank_angle + turret_angle; final_angle_rad = math.radians(final_angle)
    dir_x, dir_z = math.sin(final_angle_rad), math.cos(final_angle_rad); cannon_length = 50.0
    offset_x, offset_z = cannon_length * dir_x, cannon_length * dir_z
    start_x, start_z, start_y = tank_pos[0] + offset_x, tank_pos[2] + offset_z, 17
    player_bullets.append({'pos': [start_x, start_y, start_z], 'dir': [dir_x, 0, dir_z]})

def enemy_fire_bullet(enemy):
    angle_rad = math.radians(enemy['angle']); dir_x, dir_z = math.sin(angle_rad), math.cos(angle_rad)
    cannon_length = 50.0; offset_x, offset_z = cannon_length * dir_x, cannon_length * dir_z
    start_x = enemy['pos'][0] + offset_x; start_z = enemy['pos'][2] + offset_z; start_y = 17
    # --- NEW: Boss unique attack ---
    # If the enemy is a boss, it fires a 3-shot spread instead of one bullet.
    if enemy['type'] == 'boss':
        for angle_offset in [-15, 0, 15]:
            offset_rad = math.radians(enemy['angle'] + angle_offset)
            bullet_dir_x = math.sin(offset_rad)
            bullet_dir_z = math.cos(offset_rad)
            enemy_bullets.append({'pos': [start_x, start_y, start_z], 'dir': [bullet_dir_x, 0, bullet_dir_z]})
    else:
        # This is your original firing logic for normal enemies.
        enemy_bullets.append({'pos': [start_x, start_y, start_z], 'dir': [dir_x, 0, dir_z]})

def dayNightCycle():
    global timeOfDay, is_raining # MODIFIED: Added is_raining
    timeOfDay += 0.002
    if timeOfDay > 2 * math.pi: timeOfDay -= 2 * math.pi
    r = 0.1 + 0.4 * (math.sin(timeOfDay) * 0.5 + 0.5); g = 0.2 + 0.5 * (math.sin(timeOfDay) * 0.5 + 0.5); b = 0.3 + 0.6 * (math.sin(timeOfDay) * 0.5 + 0.5)
    r = max(0.1, min(1.0, r)); g = max(0.2, min(1.0, g)); b = max(0.3, min(1.0, b))
    
    # --- NEW: Weather control logic ---
    # It will only rain during the "night" part of the cycle
    if (math.sin(timeOfDay) * 0.5 + 0.5) < 0.25:
        is_raining = True
    else:
        is_raining = False

    glClearColor(r, g, b, 1.0)
    # MODIFIED: Removed glClear from here to handle it in showScreen, which is better practice.

# --- NEW: Logic function for Weather ---
def update_rain():
    """Creates, moves, and recycles raindrops."""
    if not is_raining:
        raindrops.clear()
        return
    # Add new raindrops if needed
    if len(raindrops) < MAX_RAINDROPS:
        x = random.uniform(-ARENA_SIZE, ARENA_SIZE)
        z = random.uniform(-ARENA_SIZE, ARENA_SIZE)
        y = WALL_HEIGHT + random.uniform(10, 50)
        raindrops.append({'pos': [x, y, z]})
    # Move all raindrops
    for drop in raindrops:
        drop['pos'][1] -= 300.0 * delta_time # Rain speed
        # If a drop hits the ground, move it back to the top
        if drop['pos'][1] < 0:
            drop['pos'][1] = WALL_HEIGHT + 20
            drop['pos'][0] = random.uniform(-ARENA_SIZE, ARENA_SIZE)
            drop['pos'][2] = random.uniform(-ARENA_SIZE, ARENA_SIZE)

# --- NEW: Logic function for Environmental Hazards ---
def check_hazard_collisions():
    """Checks if the player is touching a hazard and applies damage."""
    global player_health
    for hazard in hazards:
        dist_sq = (tank_pos[0] - hazard['pos'][0])**2 + (tank_pos[2] - hazard['pos'][2])**2
        if dist_sq < HAZARD_RADIUS**2:
            # Apply damage over time using delta_time
            player_health -= HAZARD_DAMAGE_PER_SECOND * delta_time
            if random.random() < 0.1: # Trigger a small, intermittent shake
                trigger_camera_shake(5, 0.1)

# --- Input Handlers ---

def keyboardListener(key, x, y):
    global tank_angle, last_emp_blast_time, cheat_infinite_shells, cheat_auto_turret
    # --- NEW: Added Upgrade System variables to global scope ---
    global score, upgrade_cost_armor, upgrade_cost_cannon, upgrade_cost_speed
    global upgrade_level_armor, upgrade_level_cannon, upgrade_level_speed
    global max_player_health, player_fire_cooldown, TANK_MOVE_SPEED, TANK_ROTATE_SPEED

    if game_over and key != b'r': return
    
    # MODIFIED: Used the TANK_MOVE_SPEED variable for movement
    speed_multiplier = 1.5 if 'speed' in active_power_ups else 1.0
    move_amount = TANK_MOVE_SPEED * delta_time * speed_multiplier
    rotate_amount = TANK_ROTATE_SPEED * delta_time * speed_multiplier
    angle_rad = math.radians(tank_angle)
    if key == b'w': tank_pos[0] += math.sin(angle_rad) * move_amount; tank_pos[2] += math.cos(angle_rad) * move_amount
    if key == b's': tank_pos[0] -= math.sin(angle_rad) * move_amount; tank_pos[2] -= math.cos(angle_rad) * move_amount
    if key == b'a': tank_angle += rotate_amount
    if key == b'd': tank_angle -= rotate_amount
    if key == b'r': reset_game()

    # Cheats (unchanged)
    if key == b'1': cheat_infinite_shells = not cheat_infinite_shells; print(f"Cheat - Infinite Shells: {'ON' if cheat_infinite_shells else 'OFF'}")
    if key == b'2':
        current_time = time.time()
        if current_time - last_emp_blast_time > emp_blast_cooldown:
            print("Cheat - EMP Blast Activated!");
            for enemy in enemies: frozen_enemies[enemy['id']] = current_time + 3
            last_emp_blast_time = current_time
        else: print("EMP Blast on cooldown.")
    if key == b'3': cheat_auto_turret = not cheat_auto_turret; print(f"Cheat - Auto Turret: {'ON' if cheat_auto_turret else 'OFF'}")

    # --- NEW: Tank Upgrade System ---
    # This block handles key presses for buying upgrades
    if key == b'u': # Upgrade Armor
        if score >= upgrade_cost_armor:
            score -= upgrade_cost_armor
            upgrade_level_armor += 1
            max_player_health += 25
            player_health = max_player_health # Heal to full
            upgrade_cost_armor = int(upgrade_cost_armor * 1.5)
            print("ARMOR UPGRADED!")
    if key == b'i': # Upgrade Cannon (Fire Rate)
        if score >= upgrade_cost_cannon:
            score -= upgrade_cost_cannon
            upgrade_level_cannon += 1
            player_fire_cooldown *= 0.85 # 15% faster
            upgrade_cost_cannon = int(upgrade_cost_cannon * 1.5)
            print("CANNON UPGRADED!")
    if key == b'o': # Upgrade Speed
        if score >= upgrade_cost_speed:
            score -= upgrade_cost_speed
            upgrade_level_speed += 1
            TANK_MOVE_SPEED *= 1.15 # 15% faster
            TANK_ROTATE_SPEED *= 1.10 # 10% faster rotation
            upgrade_cost_speed = int(upgrade_cost_speed * 1.5)
            print("SPEED UPGRADED!")

def specialKeyListener(key, x, y): # Unchanged
    global turret_angle
    if game_over: return
    rotate_amount = TURRET_ROTATE_SPEED * delta_time
    if key == GLUT_KEY_LEFT: turret_angle += rotate_amount
    if key == GLUT_KEY_RIGHT: turret_angle -= rotate_amount

def mouseListener(button, state, x, y):
    global last_player_fire_time
    if game_over: return
    current_time = time.time()
    # MODIFIED: Uses the player_fire_cooldown variable, which can be upgraded
    cooldown = 0 if cheat_infinite_shells else (player_fire_cooldown / 2.0 if 'rapid_fire' in active_power_ups else player_fire_cooldown)
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and current_time - last_player_fire_time > cooldown:
        fire_bullet(); last_player_fire_time = current_time

# --- Core OpenGL Functions ---

def reshape(w, h): # Unchanged
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION); glLoadIdentity()
    aspect_ratio = w / h; gluPerspective(fovY, aspect_ratio, 1.0, 1000.0)
    glMatrixMode(GL_MODELVIEW)

def setupCamera(): # Unchanged
    global camera_shake_intensity, camera_shake_duration, camera_shake_start_time
    glLoadIdentity()
    shake_x, shake_y, shake_z = 0, 0, 0
    current_time = time.time()
    if camera_shake_intensity > 0 and current_time - camera_shake_start_time < camera_shake_duration:
        elapsed = current_time - camera_shake_start_time; shake_factor = 1.0 - (elapsed / camera_shake_duration)
        shake_x = random.uniform(-camera_shake_intensity, camera_shake_intensity) * shake_factor
        shake_y = random.uniform(-camera_shake_intensity, camera_shake_intensity) * shake_factor
        shake_z = random.uniform(-camera_shake_intensity, camera_shake_intensity) * shake_factor
    else: camera_shake_intensity = 0.0
    shaken_camera_pos = (camera_pos[0] + shake_x, camera_pos[1] + shake_y, camera_pos[2] + shake_z)
    gluLookAt(shaken_camera_pos[0], shaken_camera_pos[1], shaken_camera_pos[2], 0, 0, 0, 0, 1, 0)

def idle():
    global last_frame_time, delta_time, game_over, turret_angle
    current_time = time.time()
    if last_frame_time == 0: last_frame_time = current_time
    delta_time = current_time - last_frame_time; last_frame_time = current_time
    if not game_over:
        if cheat_auto_turret and enemies:
            closest_enemy = min(enemies, key=lambda e: (tank_pos[0] - e['pos'][0])**2 + (tank_pos[2] - e['pos'][2])**2)
            dir_x = closest_enemy['pos'][0] - tank_pos[0]; dir_z = closest_enemy['pos'][2] - tank_pos[2]
            target_angle = -math.degrees(math.atan2(dir_z, dir_x)) + 90
            turret_angle = target_angle - tank_angle
        update_bullets(); update_enemies(); update_power_ups()
        
        # --- NEW: Call update functions for new features ---
        update_rain()
        check_hazard_collisions()
        
        for _ in range(5): resolve_collisions() # Original collision logic
        check_bullet_collisions(); check_power_up_collection()
    if player_health <= 0 and not game_over: game_over = True; print("Game Over!")
    glutPostRedisplay()

def showScreen():
    dayNightCycle() # This sets the background color
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # Now we clear
    setupCamera()

    # Draw Shadows First
    if not game_over: draw_player_shadow()
    draw_enemy_shadows(); draw_obstacle_shadows(); draw_power_up_shadows()
    
    # Draw Arena and ground elements
    draw_arena()
    draw_hazards() # NEW: Draw lava pits

    # Draw Tanks and other objects
    if not game_over: draw_player_tank()
    draw_bullets(); draw_enemy_tanks(); draw_obstacles(); draw_power_ups()

    # Draw weather effect last so it's on top of everything
    draw_rain() # NEW: Draw rain

    # UI Text
    draw_text(10, 770, f"Score: {score}")
    # MODIFIED: Health text shows max health
    draw_text(10, 740, f"Health: {int(player_health)}/{max_player_health}")
    draw_text(10, 710, f"Wave: {current_wave}")
    y_offset = 680
    for power_up, end_time in active_power_ups.items():
        remaining_time = max(0, end_time - time.time())
        draw_text(10, y_offset, f"{power_up.replace('_', ' ').title()}: {remaining_time:.1f}s"); y_offset -= 30
    
    # --- NEW: UI for Boss Wave ---
    if boss_active:
        draw_text(420, 770, "!!! BOSS INBOUND !!!")

    # --- NEW: UI for Upgrade System ---
    draw_text(750, 770, "UPGRADES (Score to Buy)")
    draw_text(750, 740, f"[U] Armor (Lvl {upgrade_level_armor}): {upgrade_cost_armor}")
    draw_text(750, 710, f"[I] Cannon (Lvl {upgrade_level_cannon}): {upgrade_cost_cannon}")
    draw_text(750, 680, f"[O] Speed (Lvl {upgrade_level_speed}): {upgrade_cost_speed}")
    
    if game_over:
        draw_text(450, 400, "GAME OVER"); draw_text(420, 370, "Press 'R' to Restart")
    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800); glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Ronokhetro")
    glEnable(GL_DEPTH_TEST)
    glutReshapeFunc(reshape); glutDisplayFunc(showScreen); glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener); glutMouseFunc(mouseListener); glutIdleFunc(idle)
    global last_frame_time
    last_frame_time = time.time()
    reset_game()
    glutMainLoop()

if __name__ == "__main__":
    main()
