# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Module imports
from .base import BaseSerializer

from plane.db.models import Estimate, EstimatePoint
from plane.db.models.estimate import EstimateType
from plane.utils.estimates import is_valid_time_estimate_value

from rest_framework import serializers


class EstimateSerializer(BaseSerializer):
    type = serializers.ChoiceField(choices=EstimateType.choices, required=False)

    class Meta:
        model = Estimate
        fields = "__all__"
        read_only_fields = ["workspace", "project"]


class EstimatePointSerializer(BaseSerializer):
    def validate(self, data):
        if not data:
            raise serializers.ValidationError("Estimate points are required")
        value = data.get("value")
        if value and len(value) > 20:
            raise serializers.ValidationError("Value can't be more than 20 characters")
        estimate = getattr(self.instance, "estimate", None) or self.context.get("estimate")
        estimate_type = getattr(estimate, "type", None) or self.context.get("estimate_type")
        if estimate_type == EstimateType.TIME and value not in (None, ""):
            if not is_valid_time_estimate_value(value):
                raise serializers.ValidationError("Time estimates must be positive values in 0.5-hour increments")
        return data

    class Meta:
        model = EstimatePoint
        fields = "__all__"
        read_only_fields = ["estimate", "workspace", "project"]


class EstimateReadSerializer(BaseSerializer):
    points = EstimatePointSerializer(read_only=True, many=True)

    class Meta:
        model = Estimate
        fields = "__all__"
        read_only_fields = ["points", "name", "description"]


class WorkspaceEstimateSerializer(BaseSerializer):
    points = EstimatePointSerializer(read_only=True, many=True)

    class Meta:
        model = Estimate
        fields = "__all__"
        read_only_fields = ["points", "name", "description"]
