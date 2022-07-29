def dict_to_config(d):
    result = []
    for section in d.keys():
        result.append("{0:23s} {1}\n".format("SERVERNAME", section))
        for k,v in d[section].items():
            result.append("{0:23s} {1}\n".format(k, v))
        result.append("\n")
    return result