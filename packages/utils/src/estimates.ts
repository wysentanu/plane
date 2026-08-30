/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

// plane web constants
import { EEstimateSystem } from "@plane/constants";

export const isValidEstimatePointValue = (value: string, estimateType: EEstimateSystem): boolean => {
  const numericValue = Number(value);

  return (
    Number.isFinite(numericValue) &&
    numericValue > 0 &&
    (estimateType !== EEstimateSystem.TIME || Number.isInteger(numericValue * 2))
  );
};

export const formatEstimateTime = (value: string | number | undefined | null): string => {
  if (value === undefined || value === null || (typeof value === "string" && value.trim() === "")) return "";

  const hours = Number(value);
  return Number.isFinite(hours) ? `${hours}h` : "";
};

export const isEstimatePointValuesRepeated = (
  estimatePoints: string[],
  estimateType: EEstimateSystem,
  newEstimatePoint?: string
) => {
  const currentEstimatePoints = estimatePoints.map((estimatePoint) => estimatePoint.trim());
  let isRepeated = false;

  if (newEstimatePoint === undefined) {
    if (estimateType === EEstimateSystem.CATEGORIES) {
      const points = new Set(currentEstimatePoints);
      if (points.size != currentEstimatePoints.length) isRepeated = true;
    } else if ([EEstimateSystem.POINTS, EEstimateSystem.TIME].includes(estimateType)) {
      currentEstimatePoints.map((point) => {
        if (Number(point) === Number(newEstimatePoint)) isRepeated = true;
      });
    }
  } else {
    if (estimateType === EEstimateSystem.CATEGORIES) {
      currentEstimatePoints.map((point) => {
        if (point === newEstimatePoint.trim()) isRepeated = true;
      });
    } else if ([EEstimateSystem.POINTS, EEstimateSystem.TIME].includes(estimateType)) {
      currentEstimatePoints.map((point) => {
        if (Number(point) === Number(newEstimatePoint.trim())) isRepeated = true;
      });
    }
  }

  return isRepeated;
};
