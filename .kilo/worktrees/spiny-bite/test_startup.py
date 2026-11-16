import sys
sys.path.insert(0, 'src')
import db_helper

print("[TEST] Starting full initialization sequence...")

# Step 1: init_db() - creates V1 schema if needed
db_helper.init_db()
print("[TEST] init_db() completed")

# Step 2: migrate_to_v2() - migrate to V2
result = db_helper.migrate_to_v2()
print(f"[TEST] migrate_to_v2() returned: {result}")

# Step 3: ensure_default_users() - create default users
db_helper.ensure_default_users()
print("[TEST] ensure_default_users() completed")

print("\n[TEST] Full startup sequence completed successfully - no errors!")
