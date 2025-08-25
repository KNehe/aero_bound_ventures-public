def build_flight_search_key(flight_data: dict):
    flight_data_list = [f"{key}:{value}" for key, value in flight_data.items()]
    flight_data_str = "_".join(flight_data_list)
    return flight_data_str
