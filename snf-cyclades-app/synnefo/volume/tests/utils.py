# Copyright (C) 2010-2015 GRNET S.A.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import django.test
from django.test.utils import override_settings
from synnefo.volume import util
from snf_django.lib.api import faults
from synnefo.db import models_factory as mf


class MockVolumeType(object):

    def __init__(self, disk_template):
        self.disk_template = disk_template
        self.name = "name_" + disk_template


mock_templates = ("template1", "template2")
missing_msg = "Volume type must be provided"
wrong_msg = "Volume type 'name_template3' is not detachable"


@override_settings(CYCLADES_DETACHABLE_DISK_TEMPLATES=mock_templates)
class DetachableVolumeTypesTest(django.test.TestCase):

    """Test utils for detachable volume types."""

    def test_detachable_volumes_utils(self):
        # No volume type
        volume_type = None
        with self.assertRaisesMessage(faults.BadRequest, missing_msg):
            util.is_volume_type_detachable(volume_type)

        # Non-detachable template
        volume_type = MockVolumeType("template3")
        self.assertEqual(util.is_volume_type_detachable(volume_type), False)

        # Detachable template
        volume_type = MockVolumeType("template2")
        self.assertEqual(util.is_volume_type_detachable(volume_type), True)

        # Non-detachable template and assert
        volume_type = MockVolumeType("template3")
        with self.assertRaisesMessage(faults.BadRequest, wrong_msg):
            util.assert_detachable_volume_type(volume_type)

        # Detachable template and assert
        volume_type = MockVolumeType("template1")
        util.assert_detachable_volume_type(volume_type)


class VolumeUtilsTest(django.test.TestCase):

    """Various tests for volume utils."""

    #def setUp(self):
        #self.userid = "test_user"
        #self.size = 1
        #self.vm = mf.VirtualMachineFactory()
        #self.vm = mf.VirtualMachineFactory(
        #    userid=self.userid,
        #    flavor__volume_type__disk_template="ext_archipelago")
        #self.kwargs = {"user_id": self.userid,
        #               "size": self.size,
        #               "server_id": self.vm.id}

    def test_assign_to_server(self):
        """Test if volume assignment to server works properly"""
        # Test if a volume is associated with a server and that the index is 0
        vm = mf.VirtualMachineFactory()
        vol1 = mf.VolumeFactory()
        util.assign_volume_to_server(vm, vol1)
        self.assertEqual(vol1.machine, vm)
        self.assertEqual(vm.volumes.all(), [vol1])
        self.assertEqual(vol1.index, 0)

        # Test that a new volume gets the index 1 automatically
        vol2 = mf.VolumeFactory()
        util.assign_volume_to_server(vm, vol2)
        self.assertEqual(vol2.machine, vm)
        self.assertItemsEqual(vm.volumes.all(), [vol1, vol2])
        self.assertEqual(vol2.index, 1)

        # Test that the index can be set by the user
        vol2 = mf.VolumeFactory()
        util.assign_volume_to_server(vm, vol2, index=3)
        self.assertEqual(vol2.machine, vm)
        self.assertItemsEqual(vm.volumes.all(), [vol1, vol2, vol2])
        self.assertEqual(vol2.index, 3)
