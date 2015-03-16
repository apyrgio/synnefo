# Copyright (C) 2010-2014 GRNET S.A.
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

from django.conf import settings
from synnefo.db import models
from snf_django.lib.api import faults
from synnefo.api.util import get_image_dict, get_vm
from synnefo.plankton import backend
from synnefo.cyclades_settings import cyclades_services, BASE_HOST
from synnefo.lib import join_urls
from synnefo.lib.services import get_service_path


def mark_volume_as_deleted(volume, immediate=False):
    if volume.delete_on_termination:
        volume.status = "DELETED" if immediate else "DELETING"
    else:
        volume.status = "DETACHING"

    if immediate:
        volume.deleted = True
    volume.save()


def is_volume_type_detachable(volume_type):
    """Check if the volume type is detachable."""
    if volume_type is None:
        raise faults.BadRequest("Volume type must be provided")
    if (volume_type.disk_template in
            settings.CYCLADES_DETACHABLE_DISK_TEMPLATES):
        return True
    else:
        return False


def assert_detachable_volume_type(volume_type):
    """Assert that the volume type is detachable.

    Raise a BadRequest exception in case the volume type is not detachable.
    """
    if not is_volume_type_detachable(volume_type):
        raise faults.BadRequest("Volume type '%s' is not detachable" %
                                volume_type.name)


def assign_volume_to_server(server, volume, index=None):
    """Assign a volume to a server.

    This function works at DB level. It associates the volume with server and
    calculates the index of the volume in the server, if not given.
    """
    if volume.index is None and index is None:
        # Get an list of indexes of the volumes that are attached to the given
        # VM.
        indexes = map(lambda v: v.index, server.volumes.filter(deleted=False))
        if indexes is []:
            # If the server has no volumes, automatically assign the index 0.
            index = 0
        else:
            # Else, find the largest index and add 1.
            index = reduce(max, indexes) + 1

    volume.index = index
    volume.machine = server
    volume.save()

    return volume


def get_volume(user_id, volume_id, for_update=False,
               non_deleted=False,
               exception=faults.ItemNotFound):
    volumes = models.Volume.objects
    if for_update:
        volumes = volumes.select_for_update()
    try:
        volume_id = int(volume_id)
    except (TypeError, ValueError):
        raise faults.BadRequest("Invalid volume id: %s" % volume_id)
    try:
        volume = volumes.get(id=volume_id, userid=user_id)
        if non_deleted and volume.deleted:
            raise faults.BadRequest("Volume '%s' has been deleted."
                                    % volume_id)
        return volume
    except models.Volume.DoesNotExist:
        raise exception("Volume %s not found" % volume_id)


def get_volume_type(volume_type_id, for_update=False, include_deleted=False,
                    exception=faults.ItemNotFound):
    vtypes = models.VolumeType.objects
    if not include_deleted:
        vtypes = vtypes.filter(deleted=False)
    if for_update:
        vtypes = vtypes.select_for_update()
    try:
        vtype_id = int(volume_type_id)
    except (TypeError, ValueError):
        raise faults.BadRequest("Invalid volume id: %s" % volume_type_id)
    try:
        return vtypes.get(id=vtype_id)
    except models.VolumeType.DoesNotExist:
        raise exception("Volume type %s not found" % vtype_id)


def get_snapshot(user_id, snapshot_id, exception=faults.ItemNotFound):
    try:
        with backend.PlanktonBackend(user_id) as b:
            return b.get_snapshot(snapshot_id)
    except faults.ItemNotFound:
        raise exception("Snapshot %s not found" % snapshot_id)


def get_image(user_id, image_id, exception=faults.ItemNotFound):
    try:
        return get_image_dict(image_id, user_id)
    except faults.ItemNotFound:
        raise exception("Image %s not found" % image_id)


def get_server(user_id, server_id, for_update=False, non_deleted=False,
               exception=faults.ItemNotFound):
    try:
        server_id = int(server_id)
    except (TypeError, ValueError):
        raise faults.BadRequest("Invalid server id: %s" % server_id)
    try:
        return get_vm(server_id, user_id, for_update=for_update,
                      non_deleted=non_deleted, non_suspended=True)
    except faults.ItemNotFound:
        raise exception("Server %s not found" % server_id)


VOLUME_URL = \
    join_urls(BASE_HOST,
              get_service_path(cyclades_services, "volume", version="v2.0"))

VOLUMES_URL = join_urls(VOLUME_URL, "volumes/")
SNAPSHOTS_URL = join_urls(VOLUME_URL, "snapshots/")


def volume_to_links(volume_id):
    href = join_urls(VOLUMES_URL, str(volume_id))
    return [{"rel": rel, "href": href} for rel in ("self", "bookmark")]


def snapshot_to_links(snapshot_id):
    href = join_urls(SNAPSHOTS_URL, str(snapshot_id))
    return [{"rel": rel, "href": href} for rel in ("self", "bookmark")]


def update_snapshot_state(snapshot_id, user_id, state):
    """Update the state of a snapshot in Pithos.

    Use PithosBackend in order to update the state of the snapshots in
    Pithos DB.

    """
    with backend.PlanktonBackend(user_id) as b:
        return b.update_snapshot_state(snapshot_id, state=state)
