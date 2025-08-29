Ronokhetro: 3D Tank Arena 💣
Ronokhetro (Bengali for "Battlefield") is a fast-paced 3D tank shooter built from the ground up using Python and the PyOpenGL library. Take control of your tank and survive against endless waves of increasingly difficult enemies in a dynamic arena. Use your score to upgrade your tank and become an unstoppable force!

<img width="1249" height="928" alt="image" src="https://github.com/user-attachments/assets/80a35096-224f-40b1-b88b-eade1d7393f9" />


✨ Key Features
Endless Wave System: Face off against progressively harder waves of enemy scout and juggernaut tanks. The battle only ends when you do!

Epic Boss Battles: Every third wave, a powerful Boss Tank appears! This massive enemy features higher health and a devastating three-shot spread attack that will test your skills.

Tank Upgrade System: Don't just survive—evolve! Use the score you earn from destroying enemies to purchase permanent upgrades for your tank in real-time:

Armor (U): Increase your maximum health to withstand more punishment.

Cannon (I): Boost your fire rate to overwhelm your foes.

Speed (O): Enhance your movement and rotation speed to outmaneuver the enemy.

Environmental Hazards: The arena is not always a safe place! Watch out for dangerous lava pits that will rapidly drain your health if you drive through them.

Dynamic Day/Night Cycle & Weather: The battle rages on through a full day/night cycle that affects the ambient lighting. During the darkest parts of the night, rain will fall, adding to the atmosphere.

🎮 How to Play
The controls are simple and intuitive, designed to get you right into the action.

Action	Control
Move Forward	W Key
Move Backward	S Key
Rotate Tank Left	A Key
Rotate Tank Right	D Key
Aim Turret Left	Left Arrow Key
Aim Turret Right	Right Arrow Key
Fire Cannon	Left Mouse Button
Upgrade Armor	U Key (costs score)
Upgrade Cannon	I Key (costs score)
Upgrade Speed	O Key (costs score)
Restart Game	R Key (after Game Over)

Export to Sheets
🛠️ Technical Details
This project is a demonstration of classic, immediate-mode OpenGL programming. It does not use modern shaders but instead relies on the fixed-function pipeline for rendering.

Language: Python 3

Graphics API: OpenGL

Libraries:

PyOpenGL and PyOpenGL-accelerate for OpenGL bindings.

GLUT (OpenGL Utility Toolkit) for windowing and event handling.

🚀 Setup and Installation
To run this project on your local machine, follow these simple steps:

Clone the repository:

Bash

git clone https://github.com/SHA-fayet/Ronokhetro-Battle_Ground.git
cd your-repo-name
Install the required dependencies:
This project requires PyOpenGL and PyOpenGL-accelerate. You can install them using pip.

Bash

pip install PyOpenGL PyOpenGL-accelerate
Run the game:
Execute the Python script from your terminal.

Bash

python your_script_name.py
Enjoy the battle!
