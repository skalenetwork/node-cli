def safe_get_config(config, key):
    try:
        return config[key]
    except KeyError as e:
        print(f'No such key in config: {key}')
        return None
