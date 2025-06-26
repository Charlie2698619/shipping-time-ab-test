import subprocess
import sys

PYTHON_PATH = sys.executable    

simulation_steps = [
    "generate_stores.py",
    "generate_users.py",
    "generate_orders.py",
    "generate_logistics.py",
    "generate_order_items.py",
    "generate_user_behaviors.py",
    "generate_reviews.py",
]

def run_script(path):
    print(f"▶ Running: {path}")
    result = subprocess.run([PYTHON_PATH, path], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Completed: {path}\n")
    else:
        print(f"❌ Error in {path}:\n{result.stderr}")
        exit(1)

if __name__ == "__main__":
    print("🚀 Starting full data simulation...")
    for step in simulation_steps:
        run_script(step)
    print("✅ All simulation steps completed successfully.")
