from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import time

# --- Game Configuration & State ---

# Camera-related variables
camera_pos = (0, 150, 400) # Raised camera for a better top-down view
fovY = 60

# Arena properties
ARENA_SIZE = 300
WALL_HEIGHT = 50

# --- Player Tank State ---
tank_pos = [0, 10, 0] # x, y, z position.
tank_angle = 0.0 # The direction the tank body is facing.
turret_angle = 0.0 # The direction the turret is facing, relative to the body.
TANK_MOVE_SPEED = 250.0 # Units per second
TANK_ROTATE_SPEED = 100.0 # Degrees per second
TURRET_ROTATE_SPEED = 120.0 # Degrees per second for the turret

# --- Bullet Properties ---
bullets = [] # A list to store all active bullets.
BULLET_SPEED = 250.0 # Speed of the shells.

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

    # --- NEW: Turret and Cannon now have their own rotation ---
    glPushMatrix()
    glRotatef(turret_angle, 0, 1, 0) # Apply turret rotation

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
    
    glPopMatrix() # End turret/cannon transformations
    
    glPopMatrix() # End tank transformations

def draw_bullets():
    """Draws all active bullets."""
    glColor3f(1.0, 0.8, 0.0) # Yellow color for shells
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet['pos'][0], bullet['pos'][1], bullet['pos'][2])
        gluSphere(gluNewQuadric(), 3, 10, 10) # Draw bullet as a small sphere
        glPopMatrix()

# --- Game Logic and State Updates ---

def update_bullets():
    """Updates the position of each bullet and removes it if it goes off-screen."""
    global bullets
    for bullet in bullets[:]:
        bullet['pos'][0] += bullet['dir'][0] * BULLET_SPEED * delta_time
        bullet['pos'][2] += bullet['dir'][2] * BULLET_SPEED * delta_time
        
        if not (-ARENA_SIZE < bullet['pos'][0] < ARENA_SIZE and -ARENA_SIZE < bullet['pos'][2] < ARENA_SIZE):
            bullets.remove(bullet)

def fire_bullet():
    """Creates a new bullet and adds it to the active bullets list."""
    # The final angle is the sum of the body's angle and the turret's relative angle
    final_angle = tank_angle + turret_angle
    angle_rad = math.radians(final_angle)
    
    dir_x = math.sin(angle_rad)
    dir_z = math.cos(angle_rad)

    # Calculate the bullet's starting position at the tip of the cannon
    # This also needs to account for the tank's body rotation
    body_angle_rad = math.radians(tank_angle)
    cannon_offset_z = 50.0
    start_x = tank_pos[0] + math.sin(body_angle_rad) * cannon_offset_z
    start_z = tank_pos[2] + math.cos(body_angle_rad) * cannon_offset_z
    start_y = 17

    bullets.append({
        'pos': [start_x, start_y, start_z],
        'dir': [dir_x, 0, dir_z]
    })

# --- Input Handlers ---

def keyboardListener(key, x, y):
    """Handles keyboard inputs for tank movement."""
    global tank_pos, tank_angle, delta_time

    move_amount = TANK_MOVE_SPEED * delta_time
    rotate_amount = TANK_ROTATE_SPEED * delta_time
    
    # Calculate potential next position
    angle_rad = math.radians(tank_angle)
    next_pos = list(tank_pos) # Create a copy

    if key == b'w':
        next_pos[0] += math.sin(angle_rad) * move_amount
        next_pos[2] += math.cos(angle_rad) * move_amount
    if key == b's':
        next_pos[0] -= math.sin(angle_rad) * move_amount
        next_pos[2] -= math.cos(angle_rad) * move_amount
    
    # --- NEW: Arena Boundary Check ---
    # Check if the next position is inside the arena walls (with a small buffer)
    buffer = 25 # Half of the tank's length
    if -ARENA_SIZE + buffer < next_pos[0] < ARENA_SIZE - buffer and \
       -ARENA_SIZE + buffer < next_pos[2] < ARENA_SIZE - buffer:
        tank_pos = next_pos # Only update position if it's valid

    if key == b'a':
        tank_angle += rotate_amount
    if key == b'd':
        tank_angle -= rotate_amount

def specialKeyListener(key, x, y):
    """Handles special key inputs for turret rotation."""
    global turret_angle
    rotate_amount = TURRET_ROTATE_SPEED * delta_time
    
    if key == GLUT_KEY_LEFT:
        turret_angle += rotate_amount
    if key == GLUT_KEY_RIGHT:
        turret_angle -= rotate_amount

def mouseListener(button, state, x, y):
    """Handles mouse inputs for firing bullets."""
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet()

# --- Core OpenGL Functions ---

def setupCamera():
    """Configures the camera's projection and view settings."""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 1.0, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_pos[0], camera_pos[1], camera_pos[2], 0, 0, 0, 0, 1, 0)

def idle():
    """Idle function that runs continuously."""
    global last_frame_time, delta_time
    
    current_time = time.time()
    if last_frame_time == 0:
        last_frame_time = current_time
    
    delta_time = current_time - last_frame_time
    last_frame_time = current_time
    
    update_bullets()
    
    glutPostRedisplay()

def showScreen():
    """Display function to render the entire game scene."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    # Draw all game elements
    draw_arena()
    draw_player_tank()
    draw_bullets()

    # Display game info text
    draw_text(10, 770, f"Tank Angle: {tank_angle:.2f}")
    draw_text(10, 740, f"Turret Angle: {turret_angle:.2f}")
    draw_text(10, 710, f"Active Shells: {len(bullets)}")

    glutSwapBuffers()

# --- Main Function ---

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(0, 0)
    wind = glutCreateWindow(b"Ronokhetro")

    glClearColor(0.1, 0.2, 0.35, 1.0)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    global last_frame_time
    last_frame_time = time.time()

    glutMainLoop()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
