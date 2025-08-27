def build_redis_key(data: dict):
    data_list = [f"{key}:{value}" for key, value in data.items()]
    data_str = "_".join(data_list)
    return data_str
