/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useRef, useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import { ChevronRightIcon, PageIcon, PlusIcon } from "@plane/propel/icons";
import { Logo } from "@plane/propel/emoji-icon-picker";
import { TOAST_TYPE, setToast } from "@plane/propel/toast";
// plane imports
import { getPageName } from "@plane/utils";
// components
import { ListItem } from "@/components/core/list";
import { BlockItemAction } from "@/components/pages/list/block-item-action";
// hooks
import { usePlatformOS } from "@/hooks/use-platform-os";
// plane web hooks
import type { EPageStoreType } from "@/hooks/store";
import { usePage, usePageStore } from "@/hooks/store";

type TPageListBlock = {
  depth?: number;
  pageId: string;
  storeType: EPageStoreType;
};

export const PageListBlock = observer(function PageListBlock(props: TPageListBlock) {
  const { depth = 0, pageId, storeType } = props;
  // states
  const [isExpanded, setIsExpanded] = useState(false);
  // refs
  const parentRef = useRef<HTMLDivElement>(null);
  // hooks
  const page = usePage({
    pageId,
    storeType,
  });
  const pageStore = usePageStore(storeType);
  const { workspaceSlug, projectId } = useParams();
  const { isMobile } = usePlatformOS();
  // derived values
  if (!page) return null;
  const { name, logo_props, getRedirectionLink, sub_pages_count: subPagesCount } = page;

  const childIds = pageStore.getChildPageIds(pageId);
  const isLoadingChildren = !!pageStore.childLoader?.[pageId];
  const hasLoadedChildren = childIds !== undefined;
  const hasChildren = (subPagesCount ?? 0) > 0 || (childIds?.length ?? 0) > 0;

  const handleExpand = () => {
    const next = !isExpanded;
    setIsExpanded(next);
    // lazily fetch children the first time the row is expanded
    if (next && !hasLoadedChildren) {
      pageStore.fetchPageChildren(workspaceSlug?.toString() ?? "", projectId?.toString() ?? "", pageId).catch(() => {
        setToast({
          type: TOAST_TYPE.ERROR,
          title: "Error!",
          message: "Sub-pages could not be loaded. Please try again later.",
        });
      });
    }
  };

  const handleAddSubPage = () => {
    pageStore
      .createPage({ parent: pageId })
      .then(() => {
        // refresh children so the new sub-page shows up immediately
        if (hasLoadedChildren) {
          return pageStore.fetchPageChildren(workspaceSlug?.toString() ?? "", projectId?.toString() ?? "", pageId);
        }
        setIsExpanded(true);
        return undefined;
      })
      .catch(() => {
        setToast({
          type: TOAST_TYPE.ERROR,
          title: "Error!",
          message: "Sub-page could not be created. Please try again.",
        });
      });
  };

  return (
    <>
      <ListItem
        prependTitleElement={
          <span className="flex items-center gap-1">
            {/* expand toggle */}
            {hasChildren ? (
              <button
                type="button"
                className="grid size-4 flex-shrink-0 place-items-center rounded-sm hover:bg-layer-transparent-hover"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleExpand();
                }}
              >
                <ChevronRightIcon
                  className={`size-3 text-tertiary transition-transform ${isExpanded ? "rotate-90" : ""}`}
                />
              </button>
            ) : (
              <span className="size-4 flex-shrink-0" />
            )}
            {logo_props?.in_use ? (
              <Logo logo={logo_props} size={16} type="lucide" />
            ) : (
              <PageIcon className="h-4 w-4 text-tertiary" />
            )}
          </span>
        }
        appendTitleElement={
          hasChildren && !isLoadingChildren ? (
            <span className="text-11 text-tertiary">{childIds?.length ?? subPagesCount}</span>
          ) : null
        }
        title={getPageName(name)}
        itemLink={getRedirectionLink()}
        actionableItems={
          <>
            {/* quick add sub-page */}
            {!page.archived_at && pageStore.canCurrentUserCreatePage && (
              <button
                type="button"
                aria-label="Add sub-page"
                className="grid size-5 place-items-center rounded-sm opacity-0 transition-opacity group-hover:opacity-100"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  handleAddSubPage();
                }}
              >
                <PlusIcon className="size-3.5 text-tertiary" />
              </button>
            )}
            <BlockItemAction page={page} parentRef={parentRef} storeType={storeType} />
          </>
        }
        isMobile={isMobile}
        parentRef={parentRef}
      />
      {/* children */}
      {isExpanded && (
        <div className="pl-5">
          {(childIds ?? []).map((childId) => (
            <PageListBlock key={childId} pageId={childId} storeType={storeType} depth={depth + 1} />
          ))}
        </div>
      )}
    </>
  );
});
