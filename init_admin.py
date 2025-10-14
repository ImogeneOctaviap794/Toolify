#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Toolify: Empower any LLM with function calling capabilities.
# Copyright (C) 2025 FunnyCups (https://github.com/funnycups)

"""
Admin initialization script for Toolify
Generates hashed password and JWT secret for admin authentication
"""

import sys
import yaml
from getpass import getpass
from admin_auth import hash_password, generate_jwt_secret


def init_admin():
    """Initialize admin credentials"""
    print("=" * 60)
    print("Toolify Admin 管理员初始化")
    print("=" * 60)
    print()
    
    # Get username
    username = input("Enter admin username (default: admin): ").strip()
    if not username:
        username = "admin"
    
    # Get password
    while True:
        password = getpass("Enter admin password: ")
        if len(password) < 8:
            print("❌ Password must be at least 8 characters long")
            continue
        
        password_confirm = getpass("Confirm admin password: ")
        if password != password_confirm:
            print("❌ Passwords do not match")
            continue
        
        break
    
    # Generate hashed password
    print("\n⏳ Generating secure credentials...")
    hashed_password = hash_password(password)
    jwt_secret = generate_jwt_secret()
    
    # Display results
    print("\n" + "=" * 60)
    print("✅ Admin credentials generated successfully!")
    print("=" * 60)
    print(f"\nUsername: {username}")
    print(f"Hashed Password: {hashed_password}")
    print(f"JWT Secret: {jwt_secret}")
    print("\n" + "=" * 60)
    print("Configuration for config.yaml:")
    print("=" * 60)
    print("""
admin_authentication:
  username: "{}"
  password: "{}"
  jwt_secret: "{}"
""".format(username, hashed_password, jwt_secret))
    
    # Ask if user wants to update config.yaml
    print("\n" + "=" * 60)
    update = input("Update config.yaml automatically? (y/n): ").strip().lower()
    
    if update == 'y':
        try:
            # Read current config
            config_path = "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Update admin_authentication
            config['admin_authentication'] = {
                'username': username,
                'password': hashed_password,
                'jwt_secret': jwt_secret
            }
            
            # Write back
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print(f"✅ Successfully updated {config_path}")
            print("\n⚠️  Please restart the Toolify service for changes to take effect.")
        
        except FileNotFoundError:
            print(f"❌ config.yaml not found. Please create it from config.example.yaml first.")
            print("   You can manually add the admin_authentication section shown above.")
        
        except Exception as e:
            print(f"❌ Failed to update config.yaml: {e}")
            print("   You can manually add the admin_authentication section shown above.")
    
    else:
        print("\n📋 Please manually add the admin_authentication section to your config.yaml")
    
    print("\n" + "=" * 60)
    print("后续步骤:")
    print("1. 确保 config.yaml 中包含 admin_authentication 配置")
    print("2. 重启 Toolify Admin 服务")
    print("3. 访问管理界面: http://localhost:8000/admin")
    print("=" * 60)


if __name__ == "__main__":
    try:
        init_admin()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        sys.exit(1)

