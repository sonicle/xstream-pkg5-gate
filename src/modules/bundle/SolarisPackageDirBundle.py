#!/usr/bin/python
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

#
# Copyright 2007 Sun Microsystems, Inc.  All rights reserved.
# Use is subject to license terms.
#

import os
from pkg.sysvpkg import SolarisPackage
from pkg.cpiofile import CpioFile
from pkg.actions import *

class SolarisPackageDirBundle(object):

        def __init__(self, filename):
                self.pkg = SolarisPackage(filename)
                self.pkgname = self.pkg.pkginfo["PKG"]
                self.filename = filename

        def __iter__(self):
                faspac = []
                if "faspac" in self.pkg.pkginfo:
                        faspac = self.pkg.pkginfo["faspac"]

                # Want to access the manifest as a dict.
                pkgmap = {}
                for p in self.pkg.manifest:
                        pkgmap[p.pathname] = p

                for klass in faspac:
                        cf = CpioFile.open(os.path.join(
                            self.filename, "archive", klass + ".bz2"))
                        for ci in cf:
                                yield self.action(pkgmap[ci.name],
                                    ci.extractfile())

                for p in self.pkg.manifest:
                        # Just do the files that remain.  Only regular file
                        # types end up compressed; so skip them and only them.
                        if p.type in "fev" and p.klass in faspac:
                                continue

                        # These are the only valid file types in SysV packages
                        if p.type in "ifevbcdxpls":
                                yield self.action(p, os.path.join(self.filename,
                                    "reloc", p.pathname))

        def action(self, mapline, data):
                if mapline.type in "fev":
                        return file.FileAction(data, mode=mapline.mode,
                            owner=mapline.owner, group=mapline.group,
                            path=mapline.pathname)
                elif mapline.type in "dx":
                        return directory.DirectoryAction(mode=mapline.mode,
                            owner=mapline.owner, group=mapline.group,
                            path=mapline.pathname)
                elif mapline.type == "s":
                        return link.LinkAction(path=mapline.pathname,
                            target=mapline.target)
                elif mapline.type == "l":
                        return hardlink.HardLinkAction(path=mapline.pathname,
                            target=mapline.target)
                else:
                        return unknown.UnknownAction(path=mapline.pathname)

def test(filename):
        if os.path.isfile(os.path.join(filename, "pkginfo")) and \
            os.path.isfile(os.path.join(filename, "pkgmap")):
                return True

        return False
