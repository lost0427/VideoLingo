from ruamel.yaml import YAML
from typing import Any
import os, sys
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_PATH = 'config.yaml'
config_lock = threading.Lock()

def get_user_config_path(username: str = None) -> str:
    if username:
        user_config_path = os.path.join('users', username, 'config.yaml')
        if os.path.exists(user_config_path):
            return user_config_path
    return CONFIG_PATH

yaml = YAML()
yaml.preserve_quotes = True

def load_key(key: str, username: str = None) -> Any:
    CONFIG_PATH = get_user_config_path(username)
    with config_lock:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

    keys = key.split('.')
    value = data
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            raise KeyError(f"Key '{k}' not found in configuration")
    return value

def update_key(key: str, new_value: Any, username: str = None) -> bool:
    config_path = get_user_config_path(username)
    with config_lock:
        with open(config_path, 'r', encoding='utf-8') as file:
            data = yaml.load(file)

        keys = key.split('.')
        current = data
        for k in keys[:-1]:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return False

        if isinstance(current, dict) and keys[-1] in current:
            current[keys[-1]] = new_value
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(data, file)
            return True
        else:
            raise KeyError(f"Key '{keys[-1]}' not found in configuration")
        
# basic utils
def get_joiner(language):
    if language in load_key('language_split_with_space'):
        return " "
    elif language in load_key('language_split_without_space'):
        return ""
    else:
        raise ValueError(f"Unsupported language code: {language}")

if __name__ == "__main__":
    print(load_key('language_split_with_space'))
