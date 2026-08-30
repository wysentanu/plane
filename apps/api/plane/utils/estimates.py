# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from decimal import Decimal, InvalidOperation


def is_valid_time_estimate_value(value):
    try:
        hours = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return False

    return hours.is_finite() and hours > 0 and hours % Decimal("0.5") == 0
