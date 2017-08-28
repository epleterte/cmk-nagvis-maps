#!/usr/bin/python
# Christian Bryn <chr.bryn@gmail.com> 2017
# Generates Nagvis maps from host groups
# Can be configured to only generate maps from hostgroups with given prefix

from __future__ import print_function

import socket
import os
import sys
import json
import yaml
import requests
import argparse

MOCK_DATA = True
DEBUG = True

config_path = os.path.expanduser("~/.nagmaps.yml")

example_yaml_config = """groups:
  cust-finance:
    logo: 'financelogo.png'
    url: 'https://confluence.example.com/INT/finance'
  cust-catering:
    logo: 'cateringlogo.png'
    url: 'https://confluence.example.com/INT/catering'"""

## config defaults
#config = {
#    'mqtt_server': 'mqttserver',
#    'mqtt_topics': {
#        'home/bedroom/sensor2': ['temperature']
#    },
#    'carbon_server': 'graphiteserver',
#    'carbon_port': 2003
#}

# os.path.dirname(os.path.realpath(__file__))
config = {
    'hostgroup_include': [],
    'hostgroup_exclude': [],
    'hostgroup_prefix': [''],
    'hostgroup_postfix': [''],
    'backend': 'localhost',
    'image_path': sys.path[0],
    'nagvis_image_path': '',
    'debug': True
}

argparse = argparse.ArgumentParser()
argparse.add_argument('-D', '--dump-config', action='store_true')
argparse.add_argument('-o', '--output-dir', nargs=1, default='.')
args = argparse.parse_args()

if os.path.exists(config_path):
    with open(config_path, 'r') as ymlfile:
        yml = yaml.load(ymlfile)
        # merge config:
        config.update(yml)
else:
    print('no config file found at %s, using defaults' % config_path)

if args.dump_config:
  print(config)
  sys.exit()
if args.output_dir != '':
  if not os.path.exists(args.output_dir):
    print("Output directory %s does not exist!" %s (args.output_dir)) 
    sys.exit(1)

if MOCK_DATA:
    response = '[["cust-finance"], ["cust-catering"]]'
else:
    if config['livestatus_socket'] != '':
        if os.path.exists(config['livestatus_socket']):
            socket_path = config['livestatus_socket']
    else:
        if 'OMD_ROOT' in os.environ:
            socket_path = os.path.join(os.environ['OMD_ROOT'], 'tmp/run/live')
        else:
            if os.path.exists('/var/lib/nagios/rw/live'):
                socket_path = '/var/lib/nagios/rw/live'
            elif os.path.exists('/var/lib/icinga/rw/live'):
                socket_path = '/var/lib/icinga/rw/live'
            else:
                print("Failed to detect Livestatus socket - exiting...")
                sys.exit(1)
    if config['nagvis_image_path'] != '':
        if not os.path.exists(config['nagvis_image_path']):
            print('Nagvis image path: Directory does not exist: %s' % (config['nagvis_image_path']))
    else:
        if 'OMD_ROOT' in os.environ:
            config['nagvis_image_path'] = os.path.join(os.environ['OMD_ROOT'], 'local/share/nagvis/images/')
        else:
            print("Failed to detect Nagvis image path - exiting...")
            sys.exit(1)


    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(socket_path)
        #hostgroups = s.send("GET hostgroups\nColumns: name\nOutputFormat: json\nResponseHeader: fixed16\nColumnHeaders: on\n")
        s.send("GET hostgroups\nColumns: name\nOutputFormat: json\n")

        # Important: Close sending direction. That way
        # the other side knows we are finished.
        s.shutdown(socket.SHUT_WR)

        # Parse the answer into a table (a list of lists)
        #table = [ line.split(';') for line in answer.split('\n')[:-1] ]

        response = s.recv(100000000)
    except OSError as err:
        print("Could not fetch host groups from LiveStatus: %s" % (err))

#hostgroups = response.split('\n')
json=json.loads(response)
hostgroups = [x[0] for x in json]

target_hostgroups=[]

for group in hostgroups:
    if config['debug']: print("looking at group %s" % (group))
    if group in target_hostgroups:
        if config['debug']:
            print("group %s already in target_hostgroups" % (group))
        continue
    if len(config['hostgroup_exclude']) > 0:
        if group in config['hostgroup_exclude']:
            continue
    if len(config['hostgroup_include']) > 0:
        if group in config['hostgroup_include']:
            target_hostgroups.append(group)
        continue

    if len(config['hostgroup_prefix']) == 0 or len(config['hostgroup_postfix']) == 0:
        target_hostgroups.append(group)
        continue
    for prefix in config['hostgroup_prefix']:
        if group.startswith(prefix):
            target_hostgroups.append(group)
            if config['debug']: print("prefix match: group %s added to target_hostgroups" % (group))
            break
    else:
        print('should continue because of break')
        continue
    if group in target_hostgroups:
        #print('already got a group, continuing')
        continue
    for postfix in config['hostgroup_postfix']:
        if group.endswithwith(postfix):
            target_hostgroups.append(group)
            if config['debug']: print("postfix match: group %s added to target_hostgroups" % (group))
            break
    else:
        continue

if config['debug']: print(target_hostgroups)
if not os.path.exists(os.path.join(sys.path[0], config['image_path'])):
    os.makedirs(os.path.join(sys.path[0], config['image_path']))
for group in target_hostgroups:
    #logo = ''
    logo = 'placeholder.png'
    url = ''
    if 'groups' in config and group in config['groups']:
        if 'logo' in config['groups'][group]:
            logo = config['groups'][group]['logo']
            if logo.startswith('http'):
                if not os.path.exists(os.path.join(config['image_path'], os.path.basename(logo))):
                    try:
                        #requests.get(logo)
                        r = requests.get(logo, stream=True)
                        with open(os.path.join(config['image_path'], os.path.basename(logo)), 'wb') as fd:
                            for chunk in r.iter_content(chunk_size=128):
                                fd.write(chunk)
                    except OSError:
                        print("Error while trying to fetch and write to disk: %s" % logo)
          #else:
          #    if not os.path.exists:
          #        logo = ''

        if 'url' in config['groups'][group]:
            url = config['groups'][group]['url']
    nagvis_map = """define global {{
object_id=0
iconset=std_big
dynmap_object_filter=Filter: groups >= {group}\n
sources=dynmap
dynmap_object_types=host
grid_show=0
label_show=1
}}

define shape {{
icon={logo}
x=50
y=32
url={url}
url_target=_blank
}}""".format(group=group, logo=logo, url=url)
    print(nagvis_map)
    with open(os.path.join(args.output_dir, group + '.cfg'), 'w') as fd:
        fd.write(nagvis_map)

    nagvis_overview_map = """define global {
object_id=0
iconset=std_big
sources=dynmap
dynmap_object_types=hostgroup
grid_show=0
label_show=1
label_text=[name]
}"""
    x_cord = 192
    y_cord = 96
    row = 1
    col = 1
    max_col = 6

    for group in target_hostgroups:
        nagvis_overview_map += """

define hostgroup {{
object_id=1
hostgroup_name={0}
x={1}
y={2}
backend_id={3}
}}""".format(group, x_cord, y_cord, config['backend'])

        if col == max_col:
            row += 1
            col = 1
            x_cord = 192
            y_cord += 50
        else:
            col += 1
            x_cord += 96

    with open('overview.cfg', 'w') as fd:
        fd.write(nagvis_overview_map)
