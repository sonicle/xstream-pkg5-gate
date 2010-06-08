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
# Copyright (c) 2008, 2010, Oracle and/or its affiliates. All rights reserved.
#

import testutils
if __name__ == "__main__":
        testutils.setup_environment("../../../proto")
import pkg5unittest

import os
import pkg.client.image as image
import tempfile
import unittest


class TestPkgPublisherBasics(pkg5unittest.SingleDepotTestCase):
        # Only start/stop the depot once (instead of for every test)
        persistent_setup = True

        def test_pkg_publisher_bogus_opts(self):
                """ pkg bogus option checks """

                self.image_create(self.rurl)

                self.pkg("set-publisher -@ test3", exit=2)
                self.pkg("publisher -@ test5", exit=2)
                self.pkg("set-publisher -k", exit=2)
                self.pkg("set-publisher -c", exit=2)
                self.pkg("set-publisher -O", exit=2)
                self.pkg("unset-publisher", exit=2)

        def test_publisher_add_remove(self):
                """pkg: add and remove a publisher"""

                self.image_create(self.rurl)

                self.pkg("set-publisher -O http://%s1 test1" % self.bogus_url,
                    exit=1)
                self.pkg("set-publisher --no-refresh -O http://%s1 test1" %
                    self.bogus_url)
                self.pkg("publisher | grep test")
                self.pkg("set-publisher -P -O http://%s2 test2" %
                    self.bogus_url, exit=1)
                self.pkg("set-publisher -P --no-refresh -O http://%s2 test2" %
                    self.bogus_url)
                self.pkg("publisher | grep test2")
                self.pkg("unset-publisher test1")
                self.pkg("publisher | grep test1", exit=1)

                # Verify that compatibility commands for publisher work (only
                # minimal verification is needed since these commands map
                # directly to the publisher ones).  All of these are deprecated
                # and will be removed at a future date.
                self.pkg("authority test2")
                self.pkg("set-authority --no-refresh -O http://%s2 test1" %
                    self.bogus_url)
                self.pkg("unset-authority test1")

                # Now verify that partial success (3) or complete failure (1)
                # is properly returned if an attempt to remove one or more
                # publishers only results in some of them being removed:

                # ...when one of two provided is unknown.
                self.pkg("set-publisher --no-refresh -O http://%s2 test3" %
                    self.bogus_url)
                self.pkg("unset-publisher test3 test4", exit=3)

                # ...when one of two provided is preferred (test2).
                self.pkg("set-publisher --no-refresh -O http://%s2 test3" %
                    self.bogus_url)
                self.pkg("unset-publisher test2 test3", exit=3)

                # ...when all provided are unknown.
                self.pkg("unset-publisher test3 test4", exit=1)
                self.pkg("unset-publisher test3", exit=1)

                # ...when all provided are preferred.
                self.pkg("unset-publisher test2", exit=1)

                # Now verify that success occurs when attempting to remove
                # one or more publishers:

                # ...when one is provided and not preferred.
                self.pkg("set-publisher --no-refresh -O http://%s2 test3" %
                    self.bogus_url)
                self.pkg("unset-publisher test3")

                # ...when two are provided and not preferred.
                self.pkg("set-publisher --no-refresh -O http://%s2 test3" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh -O http://%s2 test4" %
                    self.bogus_url)
                self.pkg("unset-publisher test3 test4")

        def test_publisher_uuid(self):
                """verify uuid is set manually and automatically for a
                publisher"""

                self.image_create(self.rurl)
                self.pkg("set-publisher -O http://%s1 --no-refresh --reset-uuid test1" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh --reset-uuid test1")
                self.pkg("set-publisher -O http://%s1 --no-refresh test2" %
                    self.bogus_url)
                self.pkg("publisher test2 | grep 'Client UUID: '")
                self.pkg("publisher test2 | grep -v 'Client UUID: None'")

        def test_publisher_bad_opts(self):
                """pkg: more insidious option abuse for set-publisher"""

                self.image_create(self.rurl)

                key_fh, key_path = tempfile.mkstemp()
                cert_fh, cert_path = tempfile.mkstemp()

                self.pkg(
                    "set-publisher -O http://%s1 test1 -O http://%s2 test2" %
                    (self.bogus_url, self.bogus_url), exit=2)

                self.pkg("set-publisher -O http://%s1 test1" % self.bogus_url,
                    exit=1)
                self.pkg("set-publisher -O http://%s2 test2" % self.bogus_url,
                    exit=1)
                self.pkg("set-publisher --no-refresh -O https://%s1 test1" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh -O http://%s2 test2" %
                    self.bogus_url)

                self.pkg("set-publisher --no-refresh -k %s test1" % key_path)
                os.close(key_fh)
                os.unlink(key_path)
                self.pkg("set-publisher --no-refresh -k %s test2" % key_path,
                    exit=1)

                self.pkg("set-publisher --no-refresh -c %s test1" % cert_path)
                os.close(cert_fh)
                os.unlink(cert_path)
                self.pkg("set-publisher --no-refresh -c %s test2" % cert_path,
                    exit=1)

                self.pkg("publisher test1")
                self.pkg("publisher test3", exit=1)
                self.pkg("publisher -H | grep URI", exit=1)

                # Now verify that setting ssl_cert or ssl_key to "" works.
                self.pkg('set-publisher --no-refresh -c "" test1')
                self.pkg('publisher -H test1 | grep "SSL Cert: None"')

                self.pkg('set-publisher --no-refresh -k "" test1')
                self.pkg('publisher -H test1 | grep "SSL Key: None"')

        def test_publisher_validation(self):
                """Verify that we catch poorly formed auth prefixes and URL"""

                self.image_create(self.rurl, prefix="test")

                self.pkg("set-publisher -O http://%s1 test1" % self.bogus_url,
                    exit=1)
                self.pkg("set-publisher --no-refresh -O http://%s1 test1" %
                    self.bogus_url)

                self.pkg(("set-publisher -O http://%s2 " % self.bogus_url) +
                    "$%^8", exit=1)
                self.pkg(("set-publisher -O http://%s2 " % self.bogus_url) +
                    "8^$%", exit=1)
                self.pkg("set-publisher -O http://*^5$% test2", exit=1)
                self.pkg("set-publisher -O http://%s1:abcde test2" %
                    self.bogus_url, exit=1)
                self.pkg("set-publisher -O ftp://%s2 test2" % self.bogus_url,
                    exit=1)

        def test_missing_perms(self):
                """Bug 2393"""

                self.image_create(self.rurl, prefix="test")

                self.pkg("set-publisher --no-refresh -O http://%s1 test1" %
                    self.bogus_url, su_wrap=True, exit=1)
                self.pkg("set-publisher --no-refresh -O http://%s1 foo" %
                    self.bogus_url)
                self.pkg("publisher | grep foo")
                self.pkg("set-publisher -P --no-refresh -O http://%s2 test2" %
                    self.bogus_url, su_wrap=True, exit=1)
                self.pkg("unset-publisher foo", su_wrap=True, exit=1)
                self.pkg("unset-publisher foo")

                self.pkg("set-publisher -m http://%s1 test" % self.bogus_url,
                    su_wrap=True, exit=1)
                self.pkg("set-publisher -m http://%s2 test" %
                    self.bogus_url)

                self.pkg("set-publisher -M http://%s2 test" %
                    self.bogus_url, su_wrap=True, exit=1)
                self.pkg("set-publisher -M http://%s2 test" %
                    self.bogus_url)

                # Now change the first publisher to a https URL so that
                # certificate failure cases can be tested.
                key_fh, key_path = tempfile.mkstemp(dir=self.test_root)
                cert_fh, cert_path = tempfile.mkstemp(dir=self.test_root)

                self.pkg("set-publisher --no-refresh -O https://%s1 test1" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh -c %s test1" % cert_path)
                self.pkg("set-publisher --no-refresh -k %s test1" % key_path)

                os.close(key_fh)
                os.close(cert_fh)

                # Make the cert/key unreadable by unprivileged users.
                os.chmod(key_path, 0000)
                os.chmod(cert_path, 0000)

                # Verify that an unreadable/invalid certificate results in a
                # partial failure when displaying publisher information.
                self.pkg("publisher test1", exit=3)
                self.pkg("publisher test1", su_wrap=True, exit=3)

        def test_publisher_tsv_format(self):
                """Ensure tsv formatted output is correct."""

                self.image_create(self.rurl)

                self.pkg("set-publisher --no-refresh -O https://%s1 test1" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh -O http://%s2 test2" %
                    self.bogus_url)

                base_string = ("test\ttrue\ttrue\ttrue\torigin\tonline\t"
                    "%s/\n"
                    "test1\ttrue\tfalse\ttrue\torigin\tonline\t"
                    "https://test.invalid1/\n"
                    "test2\ttrue\tfalse\ttrue\torigin\tonline\t"
                    "http://test.invalid2/\n" % self.rurl)
                # With headers
                self.pkg("publisher -F tsv")
                expected = "PUBLISHER\tSTICKY\tPREFERRED\tENABLED" \
                    "\tTYPE\tSTATUS\tURI\n" + base_string
                output = self.reduceSpaces(self.output)
                self.assertEqualDiff(expected, output)

                # Without headers
                self.pkg("publisher -HF tsv")
                expected = base_string
                output = self.reduceSpaces(self.output)
                self.assertEqualDiff(expected, output)

        def test_system_repository_publisher(self):
                """Test that system repositories can be added and
                removed using the set-publisher interface."""

                self.image_create(self.rurl)

                sock_path = os.path.join(self.test_root, "/tmp/test_sock")

                self.pkg("set-publisher --no-refresh --system-repo=file://%s1 "
                    "--socket-path=%s test1" % (self.bogus_url, sock_path),
                    exit=1)
                self.pkg("set-publisher --no-refresh --system-repo=http://%s1 "
                    "--socket-path=%s test1" % (self.bogus_url, sock_path))
                self.pkg("set-publisher --no-refresh -O http://%s1 test1" %
                    self.bogus_url, exit=1)
                self.pkg("set-publisher --no-refresh -O http://%s2 test1" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh --clear-system-repo test1")
                self.pkg("set-publisher --no-refresh -O http://%s1 test1" %
                    self.bogus_url)
                self.pkg("set-publisher --no-refresh --system-repo=http://%s1 "
                    "--socket-path=%s test1" % (self.bogus_url, sock_path),
                    exit=1)
                self.pkg("unset-publisher test1")


class TestPkgPublisherMany(pkg5unittest.ManyDepotTestCase):
        # Only start/stop the depot once (instead of for every test)
        persistent_setup = True

        foo1 = """
            open foo@1,5.11-0
            close """

        bar1 = """
            open bar@1,5.11-0
            close """

        baz1 = """
            open baz@1,5.11-0
            close """

        test3_pub_cfg = {
            "publisher": {
                "alias": "t3",
                "prefix": "test3",
            },
            "repository": {
                "collection_type": "supplemental",
                "description": "This repository serves packages for test3.",
                "legal_uris": "http://www.opensolaris.org/os/copyrights,"
                        "http://www.opensolaris.org/os/tou,"
                        "http://www.opensolaris.org/os/trademark",
                "name": "The Test3 Repository",
                "refresh_seconds": 86400,
                "registration_uri": "",
                "related_uris": "http://pkg.opensolaris.org/contrib,"
                        "http://jucr.opensolaris.org/pending,"
                        "http://jucr.opensolaris.org/contrib",
            },
        }

        def setUp(self):
                # This test suite needs actual depots.
                pkg5unittest.ManyDepotTestCase.setUp(self, ["test1", "test2",
                    "test3",  "test1", "test1", "test3"], start_depots=True)

                durl1 = self.dcs[1].get_depot_url()
                self.pkgsend_bulk(durl1, self.foo1)

                durl2 = self.dcs[2].get_depot_url()
                self.pkgsend_bulk(durl2, self.bar1)

                durl3 = self.dcs[3].get_depot_url()
                self.pkgsend_bulk(durl3, self.baz1)

                self.image_create(durl1, prefix="test1")
                self.pkg("set-publisher -O " + durl2 + " test2")
                self.pkg("set-publisher -O " + durl3 + " test3")

        def __test_mirror_origin(self, etype, add_opt, remove_opt):
                durl1 = self.dcs[1].get_depot_url()
                durl4 = self.dcs[4].get_depot_url()
                durl5 = self.dcs[5].get_depot_url()

                # Test single add.
                self.pkg("set-publisher %s http://%s1 test1" % (add_opt,
                    self.bogus_url))
                self.pkg("set-publisher %s http://%s2 test1" % (add_opt,
                    self.bogus_url))
                self.pkg("set-publisher %s http://%s5" % (add_opt,
                    self.bogus_url), exit=2)
                self.pkg("set-publisher %s test1" % add_opt, exit=2)
                self.pkg("set-publisher %s http://%s1 test1" % (add_opt,
                    self.bogus_url), exit=1)
                self.pkg("set-publisher %s http://%s5 test11" % (add_opt,
                    self.bogus_url), exit=1)
                self.pkg("set-publisher %s %s7 test1" % (add_opt,
                    self.bogus_url), exit=1)

                # Test single remove.
                self.pkg("set-publisher %s http://%s1 test1" % (remove_opt,
                    self.bogus_url))
                self.pkg("set-publisher %s http://%s2 test1" % (remove_opt,
                    self.bogus_url))
                self.pkg("set-publisher %s test11 http://%s2 http://%s4" % (
                    remove_opt, self.bogus_url, self.bogus_url), exit=2)
                self.pkg("set-publisher %s http://%s5" % (remove_opt,
                    self.bogus_url), exit=2)
                self.pkg("set-publisher %s test1" % remove_opt, exit=2)
                self.pkg("set-publisher %s http://%s5 test11" % (remove_opt,
                    self.bogus_url), exit=1)
                self.pkg("set-publisher %s http://%s6 test1" % (remove_opt,
                    self.bogus_url), exit=1)
                self.pkg("set-publisher %s %s7 test1" % (remove_opt,
                    self.bogus_url), exit=1)

                # Test a combined add and remove.
                self.pkg("set-publisher %s %s test1" % (add_opt, durl4))
                self.pkg("set-publisher %s %s %s %s test1" % (add_opt, durl5,
                    remove_opt, durl4))
                self.pkg("publisher | grep %s.*%s" % (etype, durl5))
                self.pkg("publisher | grep %s.*%s" % (etype, durl4), exit=1)
                self.pkg("set-publisher %s %s test1" % (remove_opt, durl5))

                # Verify that if one of multiple URLs is not a valid URL, pkg
                # will exit with an error, and does not add the valid one.
                self.pkg("set-publisher %s %s %s http://b^^^/ogus test1" % (
                    add_opt, durl4, add_opt), exit=1)
                self.pkg("publisher | grep %s.*%s" % (etype, durl4), exit=1)

                # Verify that multiple can be added at one time.
                self.pkg("set-publisher %s %s %s %s test1" % (add_opt, durl4,
                    add_opt, durl5))
                self.pkg("publisher | grep %s.*%s" % (etype, durl4))
                self.pkg("publisher | grep %s.*%s" % (etype, durl5))

                # Verify that multiple can be removed at one time.
                self.pkg("set-publisher %s %s %s %s test1" % (remove_opt, durl4,
                    remove_opt, durl5))
                self.pkg("publisher | grep %s.*%s" % (etype, durl4), exit=1)
                self.pkg("publisher | grep %s.*%s" % (etype, durl5), exit=1)

        def __verify_pub_cfg(self, prefix, pub_cfg):
                """Private helper method to verify publisher configuration."""

                img = image.Image(self.get_img_path(), should_exist=True)
                pub = img.get_publisher(prefix=prefix)
                for section in pub_cfg:
                        for prop, val in pub_cfg[section].iteritems():
                                if section == "publisher":
                                        pub_val = getattr(pub, prop)
                                else:
                                        pub_val = getattr(
                                            pub.selected_repository, prop)

                                if prop in ("legal_uris", "mirrors", "origins",
                                    "related_uris"):
                                        # The publisher will have these as lists,
                                        # so transform both sets of data first
                                        # for reliable comparison.  Remove any
                                        # trailing slashes so comparison can
                                        # succeed.
                                        if not val:
                                                val = set()
                                        else:
                                                val = set(val.split(","))
                                        new_pub_val = set()
                                        for u in pub_val:
                                                uri = u.uri
                                                if uri.endswith("/"):
                                                        uri = uri[:-1]
                                                new_pub_val.add(uri)
                                        pub_val = new_pub_val
                                self.assertEqual(val, pub_val)

        def test_set_auto(self):
                """Verify that set-publisher -p works as expected."""

                # XXX can't test multiple publisher configuration case as
                # depot doesn't support that yet (i.e. publisher/0 response
                # does not contain multiple publishers).  So this only tests
                # the single add/update case for the moment.
                durl1 = self.dcs[1].get_depot_url()
                durl3 = self.dcs[3].get_depot_url()
                durl4 = self.dcs[4].get_depot_url()
                self.image_create(durl1, prefix="test1")

                # Should fail because test3 publisher does not exist.
                self.pkg("publisher test3", exit=1)

                # Should fail because repository is for test3 not test2.
                self.pkg("set-publisher -p %s test2" % durl3, exit=1)

                # Verify that a publisher can be configured even if the
                # the repository's publisher configuration does not
                # include origin information.  In this case, the client
                # will assume that the provided repository URI for
                # auto-configuration is also the origin to use for
                # all configured publishers.
                t3cfg = {
                    "publisher": {
                        "prefix": "test3",
                    },
                    "repository": {
                        "origins": durl3,
                    },
                }
                self.pkg("set-publisher -p %s" % durl3)

                # Load image configuration to verify publisher was configured
                # as expected.
                self.__verify_pub_cfg("test3", t3cfg)

                # Update configuration of just this depot with more information
                # for comparison basis.
                self.dcs[3].stop()

                # Origin and mirror info wasn't known until this point, so add
                # it to the test configuration.
                t3cfg = self.test3_pub_cfg.copy()
                t3cfg["repository"]["origins"] = durl3
                t3cfg["repository"]["mirrors"] = ",".join((durl1, durl3, durl4))
                for section in t3cfg:
                        for prop, val in t3cfg[section].iteritems():
                                self.dcs[3].set_property(section, prop, val)
                self.dcs[3].start()

                # Should succeed and configure test3 publisher.
                self.pkg("set-publisher -p %s" % durl3)

                # Load image configuration to verify publisher was configured
                # as expected.
                self.__verify_pub_cfg("test3", t3cfg)

                # Now test the update case.  This verifies that the existing,
                # configured origins and mirrors will not be lost (only added
                # to) and that new data will be accepted.
                durl6 = self.dcs[6].get_depot_url()
                self.dcs[6].stop()
                t6cfg = {}
                for section in t3cfg:
                        t6cfg[section] = {}
                        for prop in t3cfg[section]:
                                val = t3cfg[section][prop]
                                if prop == "refresh_seconds":
                                        val = 1800
                                elif prop == "collection_type":
                                        val = "core"
                                elif prop not in ("alias", "prefix"):
                                        # Clear all other props.
                                        val = ""
                                t6cfg[section][prop] = val
                t6cfg["repository"]["origins"] = ",".join((durl3, durl6))
                t6cfg["repository"]["mirrors"] = ",".join((durl1, durl3, durl4,
                    durl6))
                for section in t6cfg:
                        for prop, val in t6cfg[section].iteritems():
                                self.dcs[6].set_property(section, prop, val)
                self.dcs[6].start()

                # Should fail since even though repository publisher prefix
                # matches test3, the new origin isn't configured for test3,
                # and as a result isn't a known source for publisher updates.
                self.pkg("set-publisher -p %s" % durl6, exit=1)

                # So, add the new origin to the publisher.
                self.pkg("set-publisher -g %s test3" % durl6)
                self.pkg("set-publisher -p %s" % durl6)

                # Load image configuration to verify publisher was configured
                # as expected.
                self.__verify_pub_cfg("test3", t6cfg)

        def test_set_mirrors_origins(self):
                """Test set-publisher functionality for mirrors and origins."""

                durl1 = self.dcs[1].get_depot_url()
                self.image_create(durl1, prefix="test1")

                # Test short options for mirrors.
                self.__test_mirror_origin("mirror", "-m", "-M")

                # Test long options for mirrors.
                self.__test_mirror_origin("mirror", "--add-mirror",
                    "--remove-mirror")

                # Test short options for origins.
                self.__test_mirror_origin("origin", "-g", "-G")

                # Test long options for origins.
                self.__test_mirror_origin("origin", "--add-origin",
                    "--remove-origin")

                # Finally, verify that if multiple origins are present that -O
                # will discard all others.
                durl4 = self.dcs[4].get_depot_url()
                durl5 = self.dcs[5].get_depot_url()
                self.pkg("set-publisher -g %s -g %s test1" % (durl4, durl5))
                self.pkg("set-publisher -O %s test1" % durl4)
                self.pkg("publisher | grep origin.*%s" % durl1, exit=1)
                self.pkg("publisher | grep origin.*%s" % durl5, exit=1)

        def test_enable_disable(self):
                """Test enable and disable."""

                self.pkg("publisher")
                self.pkg("publisher | grep test1")
                self.pkg("publisher | grep test2")

                self.pkg("set-publisher -d test2")
                self.pkg("publisher | grep test2") # always show
                self.pkg("publisher -n | grep test2", exit=1) # unless -n

                self.pkg("list -a bar", exit=1)
                self.pkg("publisher -a | grep test2")
                self.pkg("set-publisher -P test2", exit=1)
                self.pkg("publisher test2")
                self.pkg("set-publisher -e test2")
                self.pkg("publisher | grep test2")
                self.pkg("list -a bar")

                self.pkg("set-publisher --disable test2")
                self.pkg("publisher | grep test2")
                self.pkg("publisher -n | grep test2", exit=1)
                self.pkg("list -a bar", exit=1)
                self.pkg("publisher -a | grep test2")
                self.pkg("set-publisher --enable test2")
                self.pkg("publisher | grep test2")
                self.pkg("list -a bar")

                # should fail because test is the preferred publisher
                self.pkg("set-publisher -d test1", exit=1)
                self.pkg("set-publisher --disable test1", exit=1)

        def test_search_order(self):
                """Test moving search order around"""
                # following should be order from above test
                self.pkg("publisher") # ease debugging
                self.pkg("publisher -H | head -1 | egrep test1")
                self.pkg("publisher -H | head -2 | egrep test2")
                self.pkg("publisher -H | head -3 | egrep test3")
                # make test2 disabled, make sure order is preserved                
                self.pkg("set-publisher --disable test2")
                self.pkg("publisher") # ease debugging
                self.pkg("publisher -H | head -1 | egrep test1")
                self.pkg("publisher -H | head -2 | egrep test2")
                self.pkg("publisher -H | head -3 | egrep test3")
                self.pkg("set-publisher --enable test2")
                # make test3 preferred
                self.pkg("set-publisher -P test3")
                self.pkg("publisher") # ease debugging
                self.pkg("publisher -H | head -1 | egrep test3")
                self.pkg("publisher -H | head -2 | egrep test1")
                self.pkg("publisher -H | head -3 | egrep test2")
                # move test3 after test1
                self.pkg("set-publisher --search-after=test1 test3")
                self.pkg("publisher") # ease debugging              
                self.pkg("publisher -H | head -1 | egrep test1")
                self.pkg("publisher -H | head -2 | egrep test3")
                self.pkg("publisher -H | head -3 | egrep test2")
                # move test2 before test3
                self.pkg("set-publisher --search-before=test3 test2")
                self.pkg("publisher") # ease debugging              
                self.pkg("publisher -H | head -1 | egrep test1")
                self.pkg("publisher -H | head -2 | egrep test2")
                self.pkg("publisher -H | head -3 | egrep test3")
                # make sure we cannot get ahead or behind of ourselves
                self.pkg("set-publisher --search-before=test3 test3", exit=1)
                self.pkg("set-publisher --search-after=test3 test3", exit=1)


if __name__ == "__main__":
        unittest.main()
