# Ronokhetro — Full merged game with:
# - Landmines (cones), lava pits, falling cubes (falling correctly)
# - Hazards disappear on touch and respawn
# - Ricochet shells, active shells count
# - Boss that moves (bounces) and shoots at player
# - Tank upgrades: 1=armor (reduces damage), 2=cannon (increases bullet damage), 3=speed (increase move step)
# - Weather toggle (v), boss toggle (c), reset (r)
# - Text-only HUD
#
# Requirements: PyOpenGL, GLUT
# Run: python ronokhetro.py

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math, time, random, sys

# -------------------------
# Window / camera
# -------------------------
WIN_W, WIN_H = 1000, 800
camera_pos = (0, 150, 400)
fovY = 60

# -------------------------
# Arena
# -------------------------
ARENA_SIZE = 300
WALL_HEIGHT = 50

# -------------------------
# Player / Tank
# -------------------------
tank_pos = [0.0, 10.0, 0.0]   # x, y, z  (y stays ~10)
tank_angle = 0.0              # body rotation (deg)
turret_angle = 0.0            # turret rotation relative to body (deg)

# Base movement per key-press (you can change this single variable)
BASE_MOVE_STEP = 10.0

# Upgrades
armor = 0       # reduces incoming damage (each point reduces damage by 1, min 1)
cannon = 0      # increases bullet damage (adds to bullet base damage)
speed = 0       # increases movement step

# Health
tank_health = 100

# -------------------------
# Bullets
# -------------------------
bullets = []            # player bullets: dict {'pos':[x,y,z], 'dir':[dx,dy,dz], 'damage':int}
ricochet_bullets = []   # optional secondary bullets (we'll use same struct)
boss_bullets = []       # boss-fired bullets
BULLET_SPEED = 300.0

MAX_BULLETS = 30

# -------------------------
# Boss
# -------------------------
boss_active = False
boss_hp = 100
boss_pos = [200.0, 30.0, 200.0]   # x, y, z
boss_dir = [1.0, 0.8]             # movement direction X, Z (normalized-ish)
boss_speed = 40.0                 # units / second (slow)
boss_shoot_interval = 1.25       # seconds
_last_boss_shot = 0.0

# -------------------------
# Hazards
# -------------------------
landmines = [(random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30),
              random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30)) for _ in range(5)]
lava_pits = [(random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30),
              random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30)) for _ in range(3)]
# falling cubes as list of [x, y, z]
falling_cubes = [[random.uniform(-ARENA_SIZE + 20, ARENA_SIZE - 20),
                  random.uniform(180.0, 330.0),
                  random.uniform(-ARENA_SIZE + 20, ARENA_SIZE - 20)] for _ in range(5)]
FALL_SPEED = 90.0   # units / second (sane)

# -------------------------
# Weather / misc
# -------------------------
weather_modes = ["day", "night", "fog", "rain"]
current_weather = "day"

# -------------------------
# Timing
# -------------------------
last_frame_time = 0.0
delta_time = 0.0

# -------------------------
# Draw helpers
# -------------------------
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    # Draw 2D text in screen coords. Push/pop projection and modelview.
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
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

# -------------------------
# Scene Drawing
# -------------------------
def draw_arena():
    # background color per weather
    if current_weather == "day":
        glClearColor(0.5, 0.7, 1.0, 1.0)
    elif current_weather == "night":
        glClearColor(0.02, 0.02, 0.08, 1.0)
    elif current_weather == "fog":
        glClearColor(0.6, 0.6, 0.6, 1.0)
    else:
        glClearColor(0.2, 0.2, 0.4, 1.0)

    # Floor
    glColor3f(0.6, 0.6, 0.6)
    glBegin(GL_QUADS)
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f( ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f( ARENA_SIZE, 0,  ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, 0,  ARENA_SIZE)
    glEnd()

    # Walls
    glColor3f(0.4, 0.4, 0.5)
    glBegin(GL_QUADS)
    # far
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f( ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f( ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    # near
    glVertex3f(-ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f( ARENA_SIZE, 0, ARENA_SIZE)
    glVertex3f( ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, ARENA_SIZE)
    # left
    glVertex3f(-ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, 0,  ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT,  ARENA_SIZE)
    glVertex3f(-ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    # right
    glVertex3f( ARENA_SIZE, 0, -ARENA_SIZE)
    glVertex3f( ARENA_SIZE, 0,  ARENA_SIZE)
    glVertex3f( ARENA_SIZE, WALL_HEIGHT,  ARENA_SIZE)
    glVertex3f( ARENA_SIZE, WALL_HEIGHT, -ARENA_SIZE)
    glEnd()

    # Hazards visuals:
    # Landmines -> cones
    glColor3f(1.0, 0.0, 0.0)
    for (mx, mz) in landmines:
        glPushMatrix()
        glTranslatef(mx, 5, mz)
        glutSolidCone(8, 15, 12, 6)
        glPopMatrix()

    # Lava pits -> orange quads
    glColor3f(1.0, 0.45, 0.0)
    for (lx, lz) in lava_pits:
        glBegin(GL_QUADS)
        glVertex3f(lx - 15, 0, lz - 15)
        glVertex3f(lx + 15, 0, lz - 15)
        glVertex3f(lx + 15, 0, lz + 15)
        glVertex3f(lx - 15, 0, lz + 15)
        glEnd()

    # Falling cubes
    glColor3f(0.3, 0.3, 1.0)
    for (cx, cy, cz) in falling_cubes:
        glPushMatrix()
        glTranslatef(cx, cy, cz)
        glutSolidCube(12)
        glPopMatrix()

def draw_player_tank():
    glPushMatrix()
    glTranslatef(tank_pos[0], tank_pos[1], tank_pos[2])
    glRotatef(tank_angle, 0, 1, 0)

    # body
    glColor3f(0.2, 0.5, 0.2)
    glPushMatrix()
    glScalef(30, 20, 50)
    glutSolidCube(1)
    glPopMatrix()

    # treads
    glColor3f(0.15, 0.15, 0.15)
    glPushMatrix(); glTranslatef(-20,-5,0); glScalef(10,10,60); glutSolidCube(1); glPopMatrix()
    glPushMatrix(); glTranslatef(20,-5,0);  glScalef(10,10,60); glutSolidCube(1); glPopMatrix()

    # turret
    glPushMatrix()
    glRotatef(turret_angle, 0, 1, 0)
    glColor3f(0.25,0.55,0.25)
    glPushMatrix(); glTranslatef(0, 15, 0); glScalef(20, 10, 20); glutSolidCube(1); glPopMatrix()
    # cannon
    glColor3f(0.4,0.4,0.4)
    glPushMatrix(); glTranslatef(0, 17, 10); gluCylinder(gluNewQuadric(), 4, 4, 40, 10, 6); glPopMatrix()
    glPopMatrix()

    glPopMatrix()

def draw_bullets_all():
    glColor3f(1.0, 0.8, 0.0)
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['pos'][0], b['pos'][1], b['pos'][2])
        gluSphere(gluNewQuadric(), 3, 8, 8)
        glPopMatrix()

    glColor3f(0.0, 1.0, 1.0)
    for rb in ricochet_bullets:
        glPushMatrix()
        glTranslatef(rb['pos'][0], rb['pos'][1], rb['pos'][2])
        gluSphere(gluNewQuadric(), 3, 8, 8)
        glPopMatrix()

    glColor3f(1.0, 0.0, 1.0)
    for bb in boss_bullets:
        glPushMatrix()
        glTranslatef(bb['pos'][0], bb['pos'][1], bb['pos'][2])
        gluSphere(gluNewQuadric(), 3, 8, 8)
        glPopMatrix()

# def draw_boss_vis():
#     if boss_active:
#         glColor3f(0.6, 0.0, 0.6)
#         glPushMatrix()
#         glTranslatef(boss_pos[0], boss_pos[1], boss_pos[2])
#         glScalef(60.0, 60.0, 60.0)
#         glutSolidCube(1)
#         glPopMatrix()

def draw_boss_vis():
    if boss_active:
        glPushMatrix()
        glTranslatef(boss_pos[0], boss_pos[1], boss_pos[2])

        # --- Main Body (villain cube) ---
        glColor3f(0.6, 0.0, 0.0)  # dark red for villain
        glPushMatrix()
        glScalef(60.0, 60.0, 60.0)  # same scale as previous
        glutSolidCube(1)
        glPopMatrix()

        # --- Turret on top ---
        glPushMatrix()
        glTranslatef(0, 35, 0)  # slightly above main body
        glColor3f(0.9, 0.0, 0.0)  # brighter red
        glScalef(30.0, 20.0, 30.0)
        glutSolidCube(1)
        glPopMatrix()

        # --- Evil Eyes (glowing red cubes in front) ---
        glPushMatrix()
        glTranslatef(-15, 30, 30)
        glColor3f(1.0, 0.0, 0.0)
        glScalef(8.0, 8.0, 8.0)
        glutSolidCube(1)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(15, 30, 30)
        glColor3f(1.0, 0.0, 0.0)
        glScalef(8.0, 8.0, 8.0)
        glutSolidCube(1)
        glPopMatrix()

        glPopMatrix()  # end boss
  



# -------------------------
# Game logic updates
# -------------------------
def update_bullets():
    global bullets, ricochet_bullets, boss_bullets, boss_hp

    # player bullets
    for b in bullets[:]:
        b['pos'][0] += b['dir'][0] * BULLET_SPEED * delta_time
        b['pos'][2] += b['dir'][2] * BULLET_SPEED * delta_time

        # ricochet on arena walls
        if b['pos'][0] <= -ARENA_SIZE or b['pos'][0] >= ARENA_SIZE:
            b['dir'][0] *= -1
        if b['pos'][2] <= -ARENA_SIZE or b['pos'][2] >= ARENA_SIZE:
            b['dir'][2] *= -1

        # boss hit check
        if boss_active:
            bx, by, bz = boss_pos
            half = 60.0 / 2.0
            if (bx - half) < b['pos'][0] < (bx + half) and (bz - half) < b['pos'][2] < (bz + half):
                # damage = base + cannon upgrade
                boss_hp -= b.get('damage', 5)
                try:
                    bullets.remove(b)
                except ValueError:
                    pass

        # remove bullets that somehow exceed a sane lifetime limit
        if abs(b['pos'][0]) > ARENA_SIZE*2 or abs(b['pos'][2]) > ARENA_SIZE*2:
            try:
                bullets.remove(b)
            except ValueError:
                pass

    # ricochet bullets (separate list)
    for rb in ricochet_bullets[:]:
        rb['pos'][0] += rb['dir'][0] * BULLET_SPEED * 0.9 * delta_time
        rb['pos'][2] += rb['dir'][2] * BULLET_SPEED * 0.9 * delta_time
        if rb['pos'][0] <= -ARENA_SIZE or rb['pos'][0] >= ARENA_SIZE:
            rb['dir'][0] *= -1
        if rb['pos'][2] <= -ARENA_SIZE or rb['pos'][2] >= ARENA_SIZE:
            rb['dir'][2] *= -1

        if boss_active:
            bx, by, bz = boss_pos
            half = 60.0 / 2.0
            if (bx - half) < rb['pos'][0] < (bx + half) and (bz - half) < rb['pos'][2] < (bz + half):
                boss_hp -= rb.get('damage', 3)
                try:
                    ricochet_bullets.remove(rb)
                except ValueError:
                    pass

        if abs(rb['pos'][0]) > ARENA_SIZE*2 or abs(rb['pos'][2]) > ARENA_SIZE*2:
            try:
                ricochet_bullets.remove(rb)
            except ValueError:
                pass

    # boss bullets
    for bb in boss_bullets[:]:
        bb['pos'][0] += bb['dir'][0] * BULLET_SPEED * 0.65 * delta_time
        bb['pos'][2] += bb['dir'][2] * BULLET_SPEED * 0.65 * delta_time

        # collision with player tank (simple overlap on X/Z)
        if abs(bb['pos'][0] - tank_pos[0]) < 18 and abs(bb['pos'][2] - tank_pos[2]) < 18:
            # boss bullet damage is fixed (can be tuned)
            damage = 8
            net = max(1, damage - armor)
            global tank_health
            tank_health = max(0, tank_health - net)
            try:
                boss_bullets.remove(bb)
            except ValueError:
                pass

        if abs(bb['pos'][0]) > ARENA_SIZE*2 or abs(bb['pos'][2]) > ARENA_SIZE*2:
            try:
                boss_bullets.remove(bb)
            except ValueError:
                pass

    # cap bullets
    if len(bullets) > MAX_BULLETS:
        del bullets[0: len(bullets) - MAX_BULLETS]
    if len(ricochet_bullets) > MAX_BULLETS:
        del ricochet_bullets[0: len(ricochet_bullets) - MAX_BULLETS]

# -------------------------
# Hazards: update, collision & respawn
# -------------------------
def check_hazard_collision():
    """Apply damage, remove touched hazard. Use armor to reduce damage."""
    global tank_health, landmines, lava_pits, falling_cubes

    tx = tank_pos[0]
    tz = tank_pos[2]

    # Landmines
    for (mx, mz) in landmines[:]:
        if abs(tx - mx) < 15 and abs(tz - mz) < 15:
            dmg = 15
            net = max(1, dmg - armor)
            tank_health = max(0, tank_health - net)
            try:
                landmines.remove((mx, mz))
            except ValueError:
                pass

    # Lava pits
    for (lx, lz) in lava_pits[:]:
        if abs(tx - lx) < 18 and abs(tz - lz) < 18:
            dmg = 10
            net = max(1, dmg - armor)
            tank_health = max(0, tank_health - net)
            try:
                lava_pits.remove((lx, lz))
            except ValueError:
                pass

    # Falling cubes (3D)
    for cube in falling_cubes[:]:
        cx, cy, cz = cube
        if cy < 20 and abs(tx - cx) < 15 and abs(tz - cz) < 15:
            dmg = 20
            net = max(1, dmg - armor)
            tank_health = max(0, tank_health - net)
            try:
                falling_cubes.remove(cube)
            except ValueError:
                pass

def respawn_hazards():
    """Ensure minimum counts for hazards — spawn randomly inside arena."""
    global landmines, lava_pits, falling_cubes
    target_mines = 5
    target_lavas = 3
    target_cubes = 5

    while len(landmines) < target_mines:
        landmines.append((random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30),
                          random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30)))
    while len(lava_pits) < target_lavas:
        lava_pits.append((random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30),
                          random.randint(-ARENA_SIZE + 30, ARENA_SIZE - 30)))
    while len(falling_cubes) < target_cubes:
        falling_cubes.append([random.uniform(-ARENA_SIZE + 20, ARENA_SIZE - 20),
                              random.uniform(180.0, 330.0),
                              random.uniform(-ARENA_SIZE + 20, ARENA_SIZE - 20)])

def update_hazards():
    """Move falling cubes down; wrap/respawn if needed; then check collisions & respawn."""
    # falling cubes drop
    for i in range(len(falling_cubes)):
        cx, cy, cz = falling_cubes[i]
        cy -= FALL_SPEED * delta_time
        if cy < -20.0:
            # respawn above
            cy = random.uniform(180.0, 330.0)
            cx = random.uniform(-ARENA_SIZE + 20, ARENA_SIZE - 20)
            cz = random.uniform(-ARENA_SIZE + 20, ARENA_SIZE - 20)
        falling_cubes[i] = (cx, cy, cz)

    # collisions and respawn
    check_hazard_collision()
    respawn_hazards()

# -------------------------
# Boss: movement & shooting
# -------------------------
def update_boss():
    global boss_pos, boss_dir, _last_boss_shot, boss_bullets, boss_hp
    if not boss_active:
        return

    # move boss — scaled by delta_time
    boss_pos[0] += boss_dir[0] * boss_speed * delta_time
    boss_pos[2] += boss_dir[1] * boss_speed * delta_time

    # bounce at arena edges (keep inside +/- ARENA_SIZE)
    margin = 60
    if boss_pos[0] < -ARENA_SIZE + margin:
        boss_pos[0] = -ARENA_SIZE + margin
        boss_dir[0] *= -1
    if boss_pos[0] > ARENA_SIZE - margin:
        boss_pos[0] = ARENA_SIZE - margin
        boss_dir[0] *= -1
    if boss_pos[2] < -ARENA_SIZE + margin:
        boss_pos[2] = -ARENA_SIZE + margin
        boss_dir[1] *= -1
    if boss_pos[2] > ARENA_SIZE - margin:
        boss_pos[2] = ARENA_SIZE - margin
        boss_dir[1] *= -1

    # shooting — timed
    now = time.time()
    if now - _last_boss_shot > boss_shoot_interval:
        _last_boss_shot = now
        # fire one bullet toward player
        dx = tank_pos[0] - boss_pos[0]
        dz = tank_pos[2] - boss_pos[2]
        L = math.hypot(dx, dz)
        if L > 0:
            boss_bullets.append({
                'pos': [boss_pos[0], boss_pos[1], boss_pos[2]],
                'dir': [dx / L, 0.0, dz / L],
                'damage': 8
            })

# -------------------------
# Firing (player)
# -------------------------
def fire_bullet(mouse=False, ricochet=False):
    """Spawn bullet at tank cannon tip using body+turret angle. mouse arg just to indicate origin."""
    final_angle = tank_angle + turret_angle
    ang = math.radians(final_angle)
    dir_x = math.sin(ang)
    dir_z = math.cos(ang)
    # cannon tip offset
    body_ang = math.radians(tank_angle)
    start_x = tank_pos[0] + math.sin(body_ang) * 50.0
    start_z = tank_pos[2] + math.cos(body_ang) * 50.0
    start_y = tank_pos[1] + 17.0
    damage = 5 + cannon * 2
    bullet = {'pos': [start_x, start_y, start_z], 'dir': [dir_x, 0.0, dir_z], 'damage': damage}
    if ricochet:
        ricochet_bullets.append(bullet)
    else:
        bullets.append(bullet)

# -------------------------
# Input handlers
# -------------------------
def keyboardListener(key, x, y):
    global tank_pos, tank_angle, turret_angle, tank_health, boss_active, boss_hp
    global armor, cannon, speed, current_weather

    k = key.decode('utf-8') if isinstance(key, bytes) else key

    # movement step depends on speed upgrade
    move_step = BASE_MOVE_STEP + speed * 5.0

    # WASD discrete movement per keypress
    if k == 'w':
        tank_pos[0] += math.sin(math.radians(tank_angle)) * move_step
        tank_pos[2] += math.cos(math.radians(tank_angle)) * move_step
    if k == 's':
        tank_pos[0] -= math.sin(math.radians(tank_angle)) * move_step
        tank_pos[2] -= math.cos(math.radians(tank_angle)) * move_step
    if k == 'a':
        tank_angle += 5.0
    if k == 'd':
        tank_angle -= 5.0

    # fire (space) or via mouse
    if k == ' ':
        fire_bullet()

    # toggles / utility
    if k == 'c':
        # spawn/despawn boss
        global boss_active, boss_pos, boss_hp
        boss_active = not boss_active
        if boss_active:
            boss_hp = 100
            # place boss somewhere valid
            boss_pos = [random.uniform(-ARENA_SIZE/2, ARENA_SIZE/2), 30.0, random.uniform(-ARENA_SIZE/2, ARENA_SIZE/2)]
    if k == 'r':
        boss_hp = 100
        tank_health = 100

    # Upgrades: 1=armor,2=cannon,3=speed
    if k == '1':
        armor += 1
    if k == '2':
        cannon += 1
    if k == '3':
        speed += 1

    # Weather toggle (random)
    if k == 'v':
        current_weather = random.choice(weather_modes)

    # quick nudges for testing
    if k == 'i':
        tank_pos[2] -= 10
    if k == 'k':
        tank_pos[2] += 10
    if k == 'j':
        tank_pos[0] -= 10
    if k == 'l':
        tank_pos[0] += 10

def specialKeyListener(key, x, y):
    global turret_angle
    # rotate turret with arrow left/right
    if key == GLUT_KEY_LEFT:
        turret_angle += 5.0
    if key == GLUT_KEY_RIGHT:
        turret_angle -= 5.0

def mouseListener(button, state, x, y):
    # Left click fires normal shell, right click fires ricochet shell
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet(mouse=True, ricochet=False)
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        fire_bullet(mouse=True, ricochet=True)

# -------------------------
# Camera & core loop
# -------------------------
def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W / WIN_H, 0.1, 2000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2],
              0.0, 0.0, 0.0,
              0.0, 1.0, 0.0)

def idle():
    global last_frame_time, delta_time
    current_time = time.time()
    if last_frame_time == 0.0:
        last_frame_time = current_time
    delta_time = current_time - last_frame_time
    last_frame_time = current_time

    # update systems
    update_bullets()
    update_hazards()
    update_boss()
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WIN_W, WIN_H)
    setupCamera()

    # drawings
    draw_arena()
    draw_player_tank()
    draw_bullets_all()
    draw_boss_vis()

    # HUD (text)
    glColor3f(1.0, 1.0, 1.0)
    draw_text(10, WIN_H - 30, f"Tank HP: {tank_health}")
    draw_text(10, WIN_H - 60, f"Tank Angle: {tank_angle:.2f}")
    draw_text(10, WIN_H - 90, f"Turret Angle: {turret_angle:.2f}")
    draw_text(10, WIN_H - 120, f"Active Shells: {len(bullets) + len(ricochet_bullets)}")
    draw_text(10, WIN_H - 150, f"Weather: {current_weather}")
    if boss_active:
        draw_text(10, WIN_H - 180, f"Boss HP: {boss_hp}")
    draw_text(10, WIN_H - 210, f"Armor:{armor} Cannon:{cannon} Speed:{speed}")

    glutSwapBuffers()

# -------------------------
# Init / main
# -------------------------
def init_game():
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.1, 0.2, 0.35, 1.0)

def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"Ronokhetro - Full Game")
    init_game()
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    # start with respawn
    respawn_hazards()
    glutMainLoop()

if __name__ == "__main__":
    main()

