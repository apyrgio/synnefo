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

from django import forms

import django_filters


class SnfDateRangeField(forms.MultiValueField):

    """Form that accepts a range of DateTimeFields."""

    def __init__(self, *args, **kwargs):
        fields = (
            forms.DateTimeField(),
            forms.DateTimeField(),
        )
        super(SnfDateRangeField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return slice(*data_list)
        return None


# As much as we'd like to use django-filter's DateRangeFilter, it is fairly
# limited in what it does and not suitable to our needs. The RangeFilter on the
# other hand is exactly what we need. However, it accepts only decimals for its
# range. Therefore, we will extend this filter class by accepting only dates.
class SnfDateRangeFilter(django_filters.RangeFilter):

    """Custom class for date-range filters.

    It is based on Django's __range lookup method and uses the DateTimeField
    form, which means that both of the following inputs are accepted:

        yy-mm-dd h:m:s
        yy-mm-dd

    Note that the last method gets automatically expanded to yy-mm-dd 00:00.
    Therefore, if one wants to include the whole day, the correct input should
    either be:

        yy-mm-dd 23:59:59

    or simply the next day.
    """

    field_class = SnfDateRangeField
