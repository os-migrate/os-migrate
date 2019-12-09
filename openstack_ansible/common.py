import yaml
from plugins.os_ansible.const import DEFAULTS
from plugins.os_ansible.config import VARS_PATH


class ExtraDumper(yaml.Dumper):

    def increase_indent(self, flow=False, indentless=False):
        return super(ExtraDumper, self).increase_indent(flow, False)


def yaml_dump(content):
    return yaml.dump(content,
                     Dumper=ExtraDumper,
                     default_flow_style=False,
                     sort_keys=False)


def value(data, name, key):
    if key not in data:
        return False
    if data[key] is None:
        return False
    if not isinstance(data[key], bool) and not data[key]:
        return False
    if data[key] == DEFAULTS[name].get(key):
        return False
    return True


def write_yaml(content, path):
    with open(path, "w") as f:
        f.write("---\n")
        f.write(yaml_dump(content))


def add_vars(content, path, header=None, footer=None):
    with open(path, "a") as f:
        if header:
            f.write(header)
        f.write(yaml_dump(content))
        if footer:
            f.write(footer)


def optimize(data, use_vars=True, var_name=None):
    if not data:
        return []
    all_keys = []
    for d in data:
        values = d.values()
        # Extract all possible keys from module
        all_keys += [j for i in list(values) for j in list(i)]
    all_keys = list(set(all_keys))
    # Name of the module
    main_key = list(data[0].keys())[0]
    # Fullfil by vaulue|default(omit)
    templ = {main_key: {k: "{{ %s | default(omit) }}" % k for k in all_keys}}
    templ.update({'loop': [list(i.values())[0] for i in data]})
    for k in all_keys:
        k_values = [i.get(k) for i in templ['loop']]
        if any([isinstance(y, dict) for y in k_values]):
            continue
        if any([isinstance(y, list) for y in k_values]):
            continue
        allv = list(set(k_values))
        if len(allv) == 1:
            templ[main_key][k] = allv[0]
            for d in templ['loop']:
                del d[k]
    if use_vars:
        var_list = templ.pop('loop')
        templ['loop'] = "{{ %s }}" % var_name
        add_vars(
            {var_name: var_list},
            VARS_PATH,
            header="# %s section\n" % var_name)
    return templ
