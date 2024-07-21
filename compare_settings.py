import os
import sys
from importlib import import_module
from pprint import pprint

def load_settings(settings_module):
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
    settings = import_module(settings_module)
    return {k: v for k, v in settings.__dict__.items() if k.isupper()}

def compare_settings(settings_module_1, settings_module_2):
    settings_1 = load_settings(settings_module_1)
    settings_2 = load_settings(settings_module_2)
    
    settings_1_keys = set(settings_1.keys())
    settings_2_keys = set(settings_2.keys())
    
    common_keys = settings_1_keys & settings_2_keys
    different_keys_1 = settings_1_keys - settings_2_keys
    different_keys_2 = settings_2_keys - settings_1_keys
    
    print("\nSettings only in {}:".format(settings_module_1))
    pprint(different_keys_1)
    
    print("\nSettings only in {}:".format(settings_module_2))
    pprint(different_keys_2)
    
    print("\nDifferences in common settings:")
    for key in common_keys:
        if settings_1[key] != settings_2[key]:
            print(f"{key}:")
            print(f"  {settings_module_1}: {settings_1[key]}")
            print(f"  {settings_module_2}: {settings_2[key]}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_settings.py <settings_module_1> <settings_module_2>")
        sys.exit(1)
    
    settings_module_1 = sys.argv[1]
    settings_module_2 = sys.argv[2]
    
    compare_settings(settings_module_1, settings_module_2)
