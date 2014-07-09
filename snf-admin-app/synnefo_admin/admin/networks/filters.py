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


import logging
import re
from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.urlresolvers import reverse

from synnefo.db.models import (Network, VirtualMachine, NetworkInterface,
                               IPAddress)
from synnefo.logic.networks import validate_network_action
from synnefo.logic import networks
from astakos.im.user_utils import send_plain as send_email
from astakos.im.models import AstakosUser, Project

from eztables.views import DatatablesView
import django_filters

from synnefo_admin.admin.actions import (AdminAction, noop,
                                         has_permission_or_403)
from synnefo_admin.admin.utils import filter_owner_name, filter_id


class NetworkFilterSet(django_filters.FilterSet):

    """A collection of filters for VMs.

    This filter collection is based on django-filter's FilterSet.
    """

    networkid = django_filters.NumberFilter(label='Network ID',
                                            action=filter_id('id'))
    name = django_filters.CharFilter(label='Name', lookup_type='icontains')
    state = django_filters.MultipleChoiceFilter(
        label='Status', name='state', choices=Network.OPER_STATES)
    owner_name = django_filters.CharFilter(label='Owner Name',
                                           action=filter_owner_name)
    userid = django_filters.CharFilter(label='Owner UUID',
                                       lookup_type='icontains')

    class Meta:
        model = Network
        fields = ('networkid', 'name', 'state', 'public', 'drained',
                  'owner_name', 'userid',)
