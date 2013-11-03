#!/usr/bin/env python

import os
import sys
import logging
import subprocess

from workflow import check_gitinfo

external_path = os.path.join(os.getcwd(), "External/")

def generate_version_header(path):
    changes, version = check_gitinfo()
    if changes:
        version = "%s+CHANGES" % (version,)
    template = r"""#ifndef __VERSION_H
#define __VERSION_H

/* Automatically generated version header
   Do not modify, changes will be lost */

const char * const VERSION = "%s";
#endif
"""

    with open(path, 'w') as f:
        f.write(template % (version,))

action = None
print sys.argv
if len(sys.argv) != 1:
    action = sys.argv[1]

logging.info("Running CMake as appropriate...")
for root, dirs, files in os.walk(external_path):
    for d in dirs:
        path = os.path.join(external_path, d)
        cmake_path = os.path.join(path, "CMakeLists.txt")
        if not os.path.exists(cmake_path):
            # logging.warning("No CMakeLists.txt found for %s", path)
            continue
        args = ["cmake", cmake_path.replace(" ", "\ ")]
        args = ' '.join(args)
        subprocess.check_call(args, shell=True)

logging.info("Running make...")
for root, dirs, files in os.walk(external_path):

    old_dir = os.getcwd()

    for d in dirs:
        # Determine if a Makefile is present
        path = os.path.join(external_path, d)

        makef_path = os.path.join(path, "Makefile")

        if not os.path.exists(makef_path):
            logging.warning("No Makefile found for %s", path)
            continue

        os.chdir(path)

        args = ["make"]
        if action is not None:
            args.append(action)
        args = ' '.join(args)
        logging.warning(args)
        try:
            logging.info("Writing version header...")
            generate_version_header(os.path.join(path, "version.h"))
            logging.info("Running make...")
            subprocess.check_call(args, shell=True)
        finally:
            os.chdir(old_dir)


