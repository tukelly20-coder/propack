"""
Script tao file cap nhat cho Mo ma lieu UI
Dung de dong goi cac file can cap nhat thanh file .zip
"""

import os
import sys
import json
import zipfile
from datetime import datetime

# Xu ly encoding cho Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Các file cần đóng gói cho update thường (py files)
UPDATE_FILES_PY = [
    "Mở mã liệu UI.py",
    "Mở mã liệu 打开链接VP.py",
    "add_query_all.py",
    "create_update.py",
    "network_update_template.txt"
]

# Tên thư mục onedir (đã đóng gói)
ONEDIR_FOLDER = "Mở mã liệu UI"  # Tên thư mục onedir khi build

# File version
VERSION_FILE = "version.json"


def get_current_version():
    """Lay version hien tai tu version.json"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('version', '0.0.0')
    return '0.0.0'


def bump_version(version_str):
    """Tang version len 1 phien ban moi"""
    # Tach phan so va phan text (neu co)
    import re
    match = re.match(r'([\d.]+)\s*(.*)', version_str.strip())
    if match:
        version_num = match.group(1)
        suffix = match.group(2).strip()
    else:
        version_num = version_str
        suffix = ''
    
    parts = version_num.split('.')
    if len(parts) >= 3:
        # Tang minor version (x.y.z -> x.y.(z+1))
        parts[-1] = str(int(parts[-1]) + 1)
    elif len(parts) == 2:
        parts.append('1')
    else:
        parts = ['1', '0', '0']
    
    new_version = '.'.join(parts)
    if suffix:
        new_version = f"{new_version} {suffix}"
    return new_version


def create_update_zip(new_version=None, output_folder="."):
    """
    Tao file cap nhat
    
    Args:
        new_version: Version moi (neu None se tu dong tang)
        output_folder: Thu muc luu file update
    """
    # Lay version hien tai
    current_version = get_current_version()
    print(f"Version hien tai: {current_version}")
    
    # Tinh version moi
    if new_version is None:
        new_version = bump_version(current_version)
    
    print(f"Version moi: {new_version}")
    
    # Kiem tra cac file nguon
    missing_files = []
    for filename in UPDATE_FILES_PY:
        if not os.path.exists(filename):
            missing_files.append(filename)
    
    if missing_files:
        print(f"\n[!] Canh bao: Thieu file(s): {missing_files}")
        print("Vui long dam bao cac file nay ton tai trong thu muc hien tai.")
        
        # Hoi co tiep tuc khong
        response = input("Tiep tuc dung chI co mot so file? (y/n): ")
        if response.lower() != 'y':
            print("Da huy.")
            return False
    
    # Tao ten file zip
    zip_filename = f"update_v{new_version}.zip"
    zip_path = os.path.join(output_folder, zip_filename)
    
    # Tao file zip
    print(f"\nDang tao {zip_filename}...")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in UPDATE_FILES_PY:
            if os.path.exists(filename):
                zipf.write(filename, filename)
                print(f"  + Added: {filename}")
            else:
                print(f"  - Missing: {filename}")
    
    print(f"[OK] Da tao: {zip_path}")
    
    # Tao file update_info.json
    info = {
        "version": new_version,
        "filename": zip_filename,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "changelog": input("Nhap mo ta thay doi (changelog): ") or "Cap nhat phien ban moi",
        "force_update": False
    }
    
    info_path = os.path.join(output_folder, "update_info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=4, ensure_ascii=False)
    
    print(f"[OK] Da tao: {info_path}")
    
    print("\n" + "="*50)
    print("HUONG DAN:")
    print("="*50)
    print("1. Copy 5 file sau len network share:")
    print(f"   - {zip_filename}")
    print(f"   - update_info.json")
    print(f"\n2. Network share path:")
    print(r"   \\192.168.2.165\越南vp共享文件夹\13-IT_data\Software\Tool_Open\updates")
    print("\n3. Khach hang bam 'Tro giup -> Kiem tra cap nhat...' de update")
    
    return True


def create_update_zip_auto(new_version=None, output_folder=".", changelog=""):
    """
    Tao file cap nhat (khong hoi input - dung cho automation)
    """
    # Lay version hien tai
    current_version = get_current_version()
    
    # Tinh version moi
    if new_version is None:
        new_version = bump_version(current_version)
    
    # Tao ten file zip
    zip_filename = f"update_v{new_version}.zip"
    zip_path = os.path.join(output_folder, zip_filename)
    
    # Kiem tra co file nao de dong goi khong
    has_files = False
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filename in UPDATE_FILES_PY:
            if os.path.exists(filename):
                zipf.write(filename, filename)
                has_files = True
    
    if not has_files:
        print("[!] Khong co file nao de dong goi!")
        os.remove(zip_path)
        return False
    
    # Tao file update_info.json
    info = {
        "version": new_version,
        "filename": zip_filename,
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "changelog": changelog or f"Cap nhat phien ban {new_version}",
        "force_update": False
    }
    
    info_path = os.path.join(output_folder, "update_info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=4, ensure_ascii=False)
    
    print(f"[OK] Created: {zip_filename}")
    print(f"[OK] Created: update_info.json")
    
    return True


def create_onedir_update(onedir_path, new_version=None, changelog="", output_folder="."):
    """
    Tao file cap nhat cho onedir
    
    Args:
        onedir_path: Duong dan den thu muc onedir
        new_version: Version moi (neu None se tu dong tang)
        changelog: Mo ta thay doi
        output_folder: Thu muc luu file update
    """
    # Kiem tra thu muc ton tai
    if not os.path.exists(onedir_path):
        print(f"[!] Thu muc khong ton tai: {onedir_path}")
        return False
    
    if not os.path.isdir(onedir_path):
        print(f"[!] Khong phai thu muc: {onedir_path}")
        return False
    
    # Lay version hien tai
    current_version = get_current_version()
    print(f"Version hien tai: {current_version}")
    
    # Tinh version moi
    if new_version is None:
        new_version = bump_version(current_version)
    
    print(f"Version moi: {new_version}")
    
    # Tao ten file zip
    zip_filename = f"onedir_v{new_version}.zip"
    zip_path = os.path.join(output_folder, zip_filename)
    
    # Tao file zip cho thu muc onedir
    print(f"\nDang tao {zip_filename} tu thu muc: {onedir_path}")
    
    # Lay ten cua thu muc onedir
    onedir_name = os.path.basename(onedir_path)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(onedir_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Tinh relative path
                rel_path = os.path.join(onedir_name, os.path.relpath(file_path, onedir_path))
                zipf.write(file_path, rel_path)
                print(f"  + Added: {rel_path}")
    
    print(f"[OK] Da tao: {zip_path}")
    
    # Tao file update_info.json
    info = {
        "version": new_version,
        "filename": zip_filename,
        "onedir_filename": zip_filename,  # Danh ro la file onedir
        "release_date": datetime.now().strftime("%Y-%m-%d"),
        "changelog": changelog or f"Cap nhat phien ban {new_version}",
        "force_update": False,
        "update_type": "onedir"  # Danh loai cap nhat
    }
    
    info_path = os.path.join(output_folder, "update_info.json")
    with open(info_path, 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=4, ensure_ascii=False)
    
    print(f"[OK] Da tao: {info_path}")
    
    print("\n" + "="*50)
    print("HUONG DAN:")
    print("="*50)
    print(f"1. Copy 2 file sau len network share:")
    print(f"   - {zip_filename}")
    print(f"   - update_info.json")
    print(f"\n2. Network share path:")
    print(r"   \\192.168.2.165\越南vp共享文件夹\13-IT_data\Software\Tool_Open\updates")
    print("\n3. Khach hang bam 'Tro giup -> Kiem tra cap nhat...' de update")
    print("\n[LUU Y] Cap nhat se thay the toan bo thu muc onedir!")
    
    return True


if __name__ == "__main__":
    print("="*50)
    print("TAO FILE CAP NHAT")
    print("="*50)
    print()
    
    # Kiem tra tham so dong lenh
    if len(sys.argv) > 1:
        first_arg = sys.argv[1]
        
        # Che do auto
        if first_arg == "onedir":
            # Che do onedir: create_update.py onedir <path> [version] [changelog]
            onedir_path = sys.argv[2] if len(sys.argv) > 2 else input("Nhap duong dan thu muc onedir: ").strip()
            new_version = sys.argv[3] if len(sys.argv) > 3 else None
            changelog = sys.argv[4] if len(sys.argv) > 4 else ""
            create_onedir_update(onedir_path, new_version, changelog)
        elif first_arg == "py":
            # Che do py: create_update.py py [version] [changelog]
            version = sys.argv[2] if len(sys.argv) > 2 else None
            changelog = sys.argv[3] if len(sys.argv) > 3 else ""
            create_update_zip_auto(version, changelog=changelog)
        else:
            # Cu du lieu version
            version = sys.argv[1] if sys.argv[1] != 'auto' else None
            changelog = sys.argv[2] if len(sys.argv) > 2 else ""
            create_update_zip_auto(version, changelog=changelog)
    else:
        # Che do tuong tac
        print("Chon loai cap nhat:")
        print("  1 - Cap nhat file .py (cho chay python)")
        print("  2 - Cap nhat thu muc onedir (cho chay .exe)")
        print()
        
        choice = input("Chon (1/2): ").strip()
        
        if choice == "2":
            # Che do onedir
            onedir_path = input("Nhap duong dan thu muc onedir: ").strip().strip('"')
            new_version = input("Nhap version moi (de trong de tu dong tang): ").strip()
            if not new_version:
                new_version = None
            changelog = input("Nhap mo ta thay doi: ") or "Cap nhat phien ban moi"
            create_onedir_update(onedir_path, new_version, changelog)
        else:
            create_update_zip()
