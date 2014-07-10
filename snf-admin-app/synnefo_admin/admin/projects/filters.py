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
from operator import itemgetter

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from django.core.urlresolvers import reverse

from synnefo.db.models import (VirtualMachine, Network, Volume,
                               NetworkInterface, IPAddress)
from astakos.im.models import (AstakosUser, Project, ProjectResourceGrant,
                               Resource)

from eztables.views import DatatablesView
from synnefo_admin.admin.actions import (AdminAction, noop,
                                         has_permission_or_403)
from astakos.im.user_utils import send_plain as send_email
from astakos.im.functions import (validate_project_action, ProjectConflict,
                                  approve_application, deny_application,
                                  suspend, unsuspend, terminate, reinstate)
from astakos.im.quotas import get_project_quota

from synnefo.util import units

import django_filters
from django.db.models import Q

from synnefo_admin.admin.utils import is_resource_useful, filter_id

from synnefo_admin.admin.actions import (AdminAction, noop,
                                         has_permission_or_403)


def get_status_choices():
    """Get all possible project statuses from Project model."""
    project_states = Project.O_STATE_DISPLAY.itervalues()
    return [(value.upper(), '_') for value in project_states]


def filter_status(queryset, choices):
    """Filter project status.

    Filter by project and last application status.
    """
    choices = choices or ()
    if len(choices) == len(get_status_choices()):
        return queryset
    q = Q()
    for c in choices:
        status = getattr(Project, 'O_%s' % c.upper())
        q |= Q(last_application__state=status) | Q(state=status)
    return queryset.filter(q).distinct()


class ProjectFilterSet(django_filters.FilterSet):

    """A collection of filters for Projects.

    This filter collection is based on django-filter's FilterSet.
    """

    id = django_filters.CharFilter(label='Project ID', action=filter_id('id'))
    realname = django_filters.CharFilter(label='Name', lookup_type='icontains')
    uuid = django_filters.CharFilter(label='UUID', lookup_type='icontains')
    description = django_filters.CharFilter(label='Description',
                                            lookup_type='icontains')
    status = django_filters.MultipleChoiceFilter(
        label='Status', action=filter_status, choices=get_status_choices())
    is_base = django_filters.BooleanFilter(label='System')

    class Meta:
        model = Project
        fields = ['id', 'uuid', 'realname', 'description', 'is_base']