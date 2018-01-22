:earth_americas: cmk-nagvis-maps
===============

This project reads hostgroup data off of Livestatus, and generates a dynamic Nagvis map for each group.
In addition an 'overview map' of all hostgroups in the given backend is generated.

Installation
============

    git clone https://github.com/epleterte/cmk-nagvis-maps.git
    cd cmk-nagvis-maps
    sudo cp nagvis-maps /usr/local/bin/

Configuration
=============
Configuration lives in _~/.nagmaps.yml_

Example config - groups are found in Livestatus, and complemented with data specified in the config it it exists:

    backend: 'livestatus1'
    hostgroup_prefix: 'cust-'
    groups:
      cust-finance:
        logo: 'financelogo.png'
        url: 'https://confluence.example.com/INT/finance'
      cust-catering:
        logo: 'cateringlogo.png'
        url: 'https://confluence.example.com/INT/catering'


This is the full set of configuration parameters:

    groups            - A hash of groups. Each entry is the name of a hostgroup.
                        Each group can take the following parameters:
                        
        logo          - The logo to use for the group. Files will be read from 'image_path'.
                        'logo' can also take URLs and fetch images remotely.
        url           - specify a URL to link to for this group
    hostgroup_include - Specific hostgroups to include (excludes all other groups)
    hostgroup_exclude - Specific hostgroups to exclude (includes all but these)
    hostgroup_prefix  - Includes hostgroups with the given prefix, excludes others
    hostgroup_postfix - Includes hostgroups with the given postfix, excludes others
    backend           - Specify livestatus backend. Default is localhost.
    image_path        - Specify where images (logos) should be fetched from.
    nagvis_image_path - Nagvis image path (eg. $OMD_ROOT/local/share/nagvis/images/)
    loglevel          - Loglevel: info, warning, error, critical. Default is warning.
    livestatus_socket - Livestatus socket path. Default: Autodetect


Usage
=====

Once the config is properly set up, run the script to generate maps.
The script will write files to the directory specified by the `-o` argument if present. If not, autodetection is attempted (_$OMD_ROOT/etc/nagvis/maps_, _/etc/nagvis/maps_).

    nagvis-maps -o /etc/nagvis/maps/

The script can be run from cron to ensure generation of maps on a regular basis.

    */30 * * * * nagvis-maps

License
=======

This software is licensed under the ISC license
