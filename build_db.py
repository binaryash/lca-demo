#!/usr/bin/env python3

import os
import shutil

# --- CONFIGURATION ---
# Docker Path (Primary)
bw_dir = "/app/bw_data"

# Local Fallback (If not running in Docker)
if not os.path.exists("/app"):
    bw_dir = os.path.join(os.getcwd(), "bw_data_local")

os.environ["BRIGHTWAY2_DIR"] = bw_dir

# Ensure directory exists
if not os.path.exists(bw_dir):
    os.makedirs(bw_dir)

from brightway2 import projects, bw2setup, BW2Package, databases
from bw2data.utils import download_file
import zipfile

def bake_db():
    print(f"🍞 STARTING DATABASE BAKE in: {bw_dir}")
    
    # 1. Setup Project
    projects.set_current("brightway-forwast")
    bw2setup()

    # 2. Download FORWAST if missing
    if "forwast" not in databases:
        print("⬇️ Downloading FORWAST IO Database (this may take a minute)...")
        try:
            f = download_file("forwast.bw2package.zip", url="http://lca-net.com/wp-content/uploads/")
            
            print("📦 Extracting...")
            zipfile.ZipFile(f).extractall(os.path.dirname(f))
            
            print("💾 Importing to SQLite...")
            BW2Package.import_file(f.replace(".zip", ""))
            
            # Cleanup
            if os.path.exists(f):
                os.remove(f)
            
        except Exception as e:
            print(f"❌ ERROR Baking DB: {e}")
            raise e
    
    print("✅ DATABASE SUCCESSFULLY BAKED.")
    print(f"📂 Data stored in: {os.environ['BRIGHTWAY2_DIR']}")

if __name__ == "__main__":
    bake_db()
