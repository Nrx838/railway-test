"""Build exercises.json: desk-friendly stretches from free-exercise-db + custom eye/wrist/neck moves."""
import json

IMG = "https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/exercises/{id}/1.jpg"
db = {x["id"]: x for x in json.load(open("free-exercise-db.json"))}

# id -> (zone, where, duration_sec, difficulty, steps)
FROM_DB = {
    # back
    "Chair_Lower_Back_Stretch": ("back", "seated", 40, 1, ["Sit tall, hold the seat with one hand", "Reach the other arm up and twist toward it", "Hold 15 sec, switch sides"]),
    "Spinal_Stretch": ("back", "seated", 40, 1, ["Sit tall, feet flat", "Twist your torso, hand on the chair back", "Hold 15 sec each side"]),
    "Chair_Upper_Body_Stretch": ("back", "seated", 30, 1, ["Sit on the edge, grip the chair back behind you", "Push chest forward, squeeze shoulder blades", "Hold 20 sec"]),
    "Upper_Back-Leg_Grab": ("back", "seated", 30, 1, ["Sit, fold forward over your thighs", "Hug your legs from underneath", "Round your upper back, hold 20 sec"]),
    "Middle_Back_Stretch": ("back", "standing", 40, 1, ["Stand, hands on hips", "Slowly twist left, then right", "5 twists each side"]),
    "Standing_Pelvic_Tilt": ("back", "standing", 40, 1, ["Stand, knees soft, hands on hips", "Tuck pelvis under, then tilt back", "10 slow tilts"]),
    "Upper_Back_Stretch": ("back", "standing", 30, 1, ["Clasp hands, reach forward", "Round your shoulders, drop your head", "Hold 20 sec"]),
    "Dynamic_Back_Stretch": ("back", "standing", 40, 2, ["Stand, arms out front", "Swing arms down and back, then overhead", "10 slow swings"]),
    "Standing_Lateral_Stretch": ("back", "standing", 40, 1, ["Feet wide, knees soft", "Reach one arm over your head to the side", "Hold 15 sec each side"]),
    "Overhead_Stretch": ("back", "standing", 30, 1, ["Lace fingers, palms to the ceiling", "Reach up tall, shoulders down", "Hold 20 sec, breathe"]),
    # shoulders
    "Shoulder_Circles": ("shoulders", "seated", 30, 1, ["Arms loose at your sides", "Roll shoulders back in big circles", "10 back, 10 forward"]),
    "Shoulder_Raise": ("shoulders", "seated", 30, 1, ["Lift shoulders up to your ears", "Hold 2 sec, drop them hard", "Repeat 10 times"]),
    "Shoulder_Stretch": ("shoulders", "seated", 40, 1, ["Pull one straight arm across your chest", "Hold it with the other hand", "15 sec each side"]),
    "Arm_Circles": ("shoulders", "standing", 40, 1, ["Arms straight out to the sides", "Small circles, getting bigger", "15 forward, 15 back"]),
    "Elbow_Circles": ("shoulders", "seated", 30, 1, ["Fingertips on shoulders", "Draw big circles with your elbows", "10 each direction"]),
    "Side_Wrist_Pull": ("shoulders", "standing", 40, 1, ["Hold one wrist overhead with the other hand", "Pull gently and lean to the side", "15 sec each side"]),
    "Upward_Stretch": ("shoulders", "standing", 30, 1, ["Hands overhead, palms together", "Reach up and slightly back", "Hold 20 sec"]),
    "Elbows_Back": ("shoulders", "standing", 30, 1, ["Hands on lower back, fingers down", "Pull elbows back, chest out", "Hold 20 sec"]),
    "Dynamic_Chest_Stretch": ("shoulders", "standing", 30, 1, ["Arms straight out in front", "Swing them wide open, then back", "10 swings"]),
    "Standing_Biceps_Stretch": ("shoulders", "standing", 30, 1, ["Clasp hands behind your back", "Straighten arms, lift them slightly", "Hold 20 sec"]),
    "Triceps_Stretch": ("shoulders", "seated", 40, 1, ["One hand behind your head", "Pull that elbow gently with the other hand", "15 sec each side"]),
    "Tricep_Side_Stretch": ("shoulders", "seated", 40, 1, ["Bring one arm across and over the opposite shoulder", "Push the elbow gently", "15 sec each side"]),
    "One_Arm_Against_Wall": ("shoulders", "wall", 40, 1, ["Bent arm against a wall or doorframe", "Turn your body away", "15 sec each side"]),
    # neck
    "Side_Neck_Stretch": ("neck", "seated", 30, 1, ["Shoulders relaxed", "Tilt ear toward shoulder", "15 sec each side"]),
    "Chin_To_Chest_Stretch": ("neck", "seated", 30, 1, ["Sit tall", "Slowly drop chin to chest", "Hold 20 sec, breathe"]),
    # wrists
    "Wrist_Circles": ("wrists", "seated", 30, 1, ["Arms out in front", "Rotate wrists in circles", "10 each direction"]),
    # legs / hips
    "Chair_Leg_Extended_Stretch": ("legs", "seated", 40, 1, ["Sit on the edge, one leg straight out", "Lean forward over it, back straight", "15 sec each leg"]),
    "Calf_Stretch_Hands_Against_Wall": ("legs", "wall", 40, 1, ["Hands on a wall, one foot back", "Press the back heel down", "15 sec each leg"]),
    "Calf_Stretch_Elbows_Against_Wall": ("legs", "wall", 40, 1, ["Forearms on a wall", "Lean in, heels on the floor", "Hold 20 sec"]),
    "Standing_Hip_Flexors": ("legs", "standing", 40, 1, ["Small step back with one foot", "Tuck pelvis, push hips forward", "15 sec each side"]),
    "Standing_Hip_Circles": ("legs", "standing", 40, 2, ["Hold the desk, stand on one leg", "Circle the other knee out wide", "8 circles each leg"]),
    "Front_Leg_Raises": ("legs", "standing", 40, 2, ["Hold the desk with one hand", "Swing one leg forward and back", "10 swings each leg"]),
    "Side_Leg_Raises": ("legs", "standing", 40, 2, ["Hold the desk, stand on one leg", "Swing the other leg side to side", "10 swings each leg"]),
    "Knee_Circles": ("legs", "standing", 30, 1, ["Feet together, hands on knees", "Circle knees slowly", "10 each direction"]),
    "Ankle_Circles": ("legs", "seated", 30, 1, ["Lift one foot", "Draw circles with your toes", "10 each direction, each foot"]),
    "Sit_Squats": ("legs", "standing", 40, 2, ["Stand in front of your chair", "Sit down slowly, stand right back up", "10 reps"]),
    "Standing_Toe_Touches": ("legs", "standing", 30, 2, ["Feet together, knees soft", "Reach down toward your toes", "Hold 20 sec"]),
    "Standing_Soleus_And_Achilles_Stretch": ("legs", "standing", 40, 1, ["One foot slightly in front", "Bend both knees, heels down", "15 sec each side"]),
}

# No photos in the db for these; image generated later.
CUSTOM = [
    ("Chin_Tucks", "Chin Tucks", "neck", "seated", 30, 1, ["Look straight ahead", "Pull your chin back, make a double chin", "Hold 3 sec, 10 reps"]),
    ("Neck_Rotations", "Neck Rotations", "neck", "seated", 30, 1, ["Sit tall", "Turn your head slowly left, then right", "5 each side, no rushing"]),
    ("Upper_Trap_Stretch", "Upper Trap Stretch", "neck", "seated", 40, 1, ["Hand over the top of your head", "Gently pull your ear to your shoulder", "15 sec each side"]),
    ("Armpit_Sniff", "Levator Scapulae Stretch", "neck", "seated", 40, 1, ["Turn your head 45° to one side", "Look down toward your armpit", "15 sec each side"]),
    ("Eyes_20_20_20", "20-20-20 Rule", "eyes", "seated", 20, 1, ["Find something about 20 feet away", "Look at it for 20 seconds", "Blink slowly"]),
    ("Eyes_Palming", "Palming", "eyes", "seated", 30, 1, ["Rub your palms until warm", "Cup them over closed eyes", "Breathe for 30 sec"]),
    ("Eyes_Circles", "Eye Circles", "eyes", "seated", 20, 1, ["Keep your head still", "Roll your eyes in a big circle", "5 each direction"]),
    ("Eyes_Near_Far", "Near-Far Focus", "eyes", "seated", 30, 1, ["Hold your thumb 10 inches away", "Focus on it, then on something far", "Switch 10 times"]),
    ("Eyes_Blink_Reset", "Blink Reset", "eyes", "seated", 20, 1, ["Blink fast for 10 seconds", "Close your eyes for 10 seconds", "Repeat twice"]),
    ("Eyes_Figure_Eight", "Figure Eight", "eyes", "seated", 20, 1, ["Imagine a big 8 on the wall", "Trace it slowly with your eyes", "5 times, then reverse"]),
    ("Wrist_Flexor_Stretch", "Wrist Flexor Stretch", "wrists", "seated", 40, 1, ["Arm straight, palm up", "Pull fingers down and back", "15 sec each hand"]),
    ("Wrist_Extensor_Stretch", "Wrist Extensor Stretch", "wrists", "seated", 40, 1, ["Arm straight, palm down", "Pull the back of your hand toward you", "15 sec each hand"]),
    ("Prayer_Stretch", "Prayer Stretch", "wrists", "seated", 30, 1, ["Palms together in front of your chest", "Lower hands slowly, keep palms pressed", "Hold 20 sec"]),
    ("Finger_Spreads", "Finger Spreads", "wrists", "seated", 20, 1, ["Spread your fingers as wide as you can", "Hold 3 sec, then relax", "10 reps"]),
    ("Fist_Release", "Fist Clench & Release", "wrists", "seated", 20, 1, ["Make a tight fist", "Explode fingers open", "10 reps, then shake it out"]),
]

GRID_IMG = "https://raw.githubusercontent.com/Nrx838/railway-test/coach-gary/img/{id}.jpg"

# Cut from the user's generated 4x4 grid (img/). Same model/studio as the db photos.
CUSTOM += [
    ("Scalene_Stretch", "Scalene Stretch", "neck", "seated", 40, 1, ["Hand flat on your collarbone", "Tilt your head back and away", "15 sec each side"]),
    ("SCM_Stretch", "Front Neck Stretch", "neck", "seated", 40, 1, ["Hand on your collarbone", "Turn your head away and look up", "15 sec each side"]),
    ("Neck_Flexion", "Neck Flexion Stretch", "neck", "seated", 30, 1, ["Sit tall, hands on knees", "Drop your chin toward your chest", "Hold 20 sec"]),
    ("Neck_Extension", "Neck Extension Stretch", "neck", "seated", 30, 1, ["Sit tall", "Slowly look up at the ceiling", "Hold 15 sec, come back slowly"]),
    ("Lateral_Neck_Stretch", "Lateral Neck Stretch", "neck", "seated", 30, 1, ["Hands on knees", "Ear toward shoulder, no hands", "15 sec each side"]),
    ("Neck_Isometric", "Neck Isometric Hold", "neck", "seated", 40, 2, ["Hand on the side of your head", "Push your head into it, don't move", "10 sec each side, twice"]),
    ("Shoulder_Rolls_Forward", "Shoulder Rolls (Forward)", "shoulders", "seated", 30, 1, ["Arms loose", "Roll shoulders forward in big circles", "10 slow rolls"]),
    ("Shoulder_Rolls_Backward", "Shoulder Rolls (Backward)", "shoulders", "seated", 30, 1, ["Arms loose", "Roll shoulders back in big circles", "10 slow rolls"]),
    ("Shoulder_Blade_Squeeze", "Shoulder Blade Squeeze", "shoulders", "seated", 30, 1, ["Sit tall, arms by your sides", "Squeeze shoulder blades together", "Hold 5 sec, 8 reps"]),
    ("Chest_Opener", "Chest Opener", "shoulders", "seated", 30, 1, ["Arms wide, palms up", "Open your chest, look slightly up", "Hold 20 sec"]),
    ("Seated_Upper_Back_Stretch", "Seated Upper Back Stretch", "back", "seated", 30, 1, ["Clasp hands, arms straight out", "Round your back, tuck your head", "Hold 20 sec"]),
    ("Side_Reach", "Seated Side Reach", "back", "seated", 40, 1, ["One hand on your knee", "Reach the other arm up and over", "15 sec each side"]),
]
HAS_GRID_IMG = {c[0] for c in CUSTOM}  # both generated grids cover every custom move

pool = []
for ex_id, (zone, where, dur, diff, steps) in FROM_DB.items():
    src = db[ex_id]  # KeyError here = typo in id
    pool.append({"id": ex_id, "name": src["name"], "zone": zone, "where": where,
                 "duration_sec": dur, "difficulty": diff, "steps": steps,
                 "image_url": IMG.format(id=ex_id), "source": "free-exercise-db"})
for ex_id, name, zone, where, dur, diff, steps in CUSTOM:
    pool.append({"id": ex_id, "name": name, "zone": zone, "where": where,
                 "duration_sec": dur, "difficulty": diff, "steps": steps,
                 "image_url": GRID_IMG.format(id=ex_id) if ex_id in HAS_GRID_IMG else None,
                 "source": "custom"})

json.dump(pool, open("exercises.json", "w"), indent=1, ensure_ascii=False)

from collections import Counter
print(len(pool), Counter(p["zone"] for p in pool), "no image:", sum(p["image_url"] is None for p in pool))
