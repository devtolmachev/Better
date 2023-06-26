def make_dict_human_readable(data: dict,
                             keyring_data: dict[str, str]):
    for old, new in list(keyring_data.items()):

        if old in data:
            data[new] = data[old]
            del data[old]
            del keyring_data[old]

        elif any([
                    data.get(x) is not None
                    for x in list(data.keys())
                ]):
            for x in list(data.keys()):
                if data.get(x) is not None:
                    data[x][new] = data[x][old]
                    del data[x][old]
                    if keyring_data.get(old) and all(
                        [data[x].get(old) is None]
                    ):
                        del keyring_data[old]

    return data


data = {"NBA 2K23": {"guess": "0", "not_guess": "0"},
        "temp_counters": {"guess": "0", "not_guess": "0"}}

keyring_data = {
    "NBA 2K23": 'Кибер баскет',
    "temp_counters": "временные счетчики",
    "guess": "угадал",
    "not_guess": "не угадал",
    "a": "b"
}

print(make_dict_human_readable(data, keyring_data))
