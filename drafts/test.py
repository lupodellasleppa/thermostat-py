def dict_diff(d1, d2, c=1, res={}):
    # print(f'{c}\td1: {d1}\n\td2: {d2}\n\tres: {res}')
    for k in d1:
        # print(f'{c}\tres: {res}')
        if k not in d2:
            res[k] = d1[k]
        else:
            res[k] = d2[k]
            res[k].update({kk:v for kk, v in d1[k].items() if kk not in d2[k]})
    return res

if __name__ == '__main__':
    settings_file = {'mode': {'auto': False, 'program': 0, 'manual': False, 'desired_temp': 20.0}, 'temperatures': {'room': 20.0}, 'log': {'loglevel': 'info', 'global_log_path': '', 'session_log_path': '', 'last_day_on': '1970-01-01', 'time_elapsed': '0:00:00'}, 'configs': {'UDP_IP': '192.168.0.10', 'UDP_port': 9000}, 'poll_intervals': {'settings': 5, 'temperature': 60}}
    settings_changes = {'mode': {'manual': True}}
    settings_changes = {
        k:(
            {kk:v for kk, v in settings_file[k].items()}
            if k not in settings_changes
            else {kk:(
                v if kk not in settings_changes[k]
                else settings_changes[k][kk]
            ) for kk, v in settings_file[k].items()}
        ) for k in settings_file
    }
    print(settings_changes)
    print(settings_changes == settings_file)
    # print(dict_diff(example_settings, settings_changes))
