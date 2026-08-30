# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""
Contract tests for nested pages:

- children are retrievable through the page detail endpoint (regression: the
  root-only list queryset used to exclude child pages from retrieve as well),
- the children endpoint returns direct child pages with sub_pages_count,
- reparenting a page under its own descendant is rejected (cycle guard),
- a page cannot be made its own parent.
"""

import pytest
from rest_framework import status

from plane.db.models import Page, Project, ProjectMember, ProjectPage


def _make_project(workspace, identifier):
    return Project.objects.create(
        name=f"Project {identifier}",
        identifier=identifier,
        workspace=workspace,
    )


def _make_page(workspace, project, owner, name="Page", parent=None):
    page = Page.objects.create(
        workspace=workspace,
        owned_by=owner,
        access=Page.PUBLIC_ACCESS,
        name=name,
        parent=parent,
    )
    ProjectPage.objects.create(workspace=workspace, project=project, page=page)
    return page


@pytest.mark.contract
class TestNestedPages:
    def _setup(self, workspace, create_user):
        project = _make_project(workspace, "PGS")
        ProjectMember.objects.create(workspace=workspace, project=project, member=create_user, role=20)
        return project

    def test_child_page_is_retrievable(self, session_client, create_user, workspace):
        """A child page must be fetchable through the detail endpoint."""
        project = self._setup(workspace, create_user)
        parent = _make_page(workspace, project, create_user, name="Parent")
        child = _make_page(workspace, project, create_user, name="Child", parent=parent)

        response = session_client.get(
            f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/{child.id}/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert str(response.data["id"]) == str(child.id)
        assert response.data["name"] == "Child"

    def test_children_endpoint_lists_direct_children_with_counts(self, session_client, create_user, workspace):
        """The children endpoint returns direct children only, each with sub_pages_count."""
        project = self._setup(workspace, create_user)
        root = _make_page(workspace, project, create_user, name="Root")
        child = _make_page(workspace, project, create_user, name="Child", parent=root)
        _make_page(workspace, project, create_user, name="GrandChild", parent=child)

        response = session_client.get(
            f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/{root.id}/children/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert str(response.data[0]["id"]) == str(child.id)
        # grandchild counted on the child row
        child_row = next(p for p in response.data if str(p["id"]) == str(child.id))
        assert child_row["sub_pages_count"] == 1

        # and the child's own children endpoint returns the grandchild
        response = session_client.get(
            f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/{child.id}/children/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["sub_pages_count"] == 0

    def test_roots_list_excludes_children(self, session_client, create_user, workspace):
        """The main pages list keeps returning roots only."""
        project = self._setup(workspace, create_user)
        root = _make_page(workspace, project, create_user, name="Root")
        _make_page(workspace, project, create_user, name="Child", parent=root)

        response = session_client.get(f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/")
        assert response.status_code == status.HTTP_200_OK
        ids = [str(p["id"]) for p in response.data]
        assert str(root.id) in ids
        assert all(p["parent"] is None for p in response.data if str(p["id"]) != str(root.id))

    def test_reparent_under_descendant_rejected(self, session_client, create_user, workspace):
        """Moving a page under one of its own descendants must fail."""
        project = self._setup(workspace, create_user)
        root = _make_page(workspace, project, create_user, name="Root")
        child = _make_page(workspace, project, create_user, name="Child", parent=root)

        response = session_client.patch(
            f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/{root.id}/",
            {"parent": str(child.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        root.refresh_from_db()
        assert root.parent_id is None

    def test_self_parent_rejected(self, session_client, create_user, workspace):
        """A page cannot be its own parent."""
        project = self._setup(workspace, create_user)
        page = _make_page(workspace, project, create_user, name="Solo")

        response = session_client.patch(
            f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/{page.id}/",
            {"parent": str(page.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_valid_reparent_allowed(self, session_client, create_user, workspace):
        """Reparenting to an unrelated page still works."""
        project = self._setup(workspace, create_user)
        page_a = _make_page(workspace, project, create_user, name="A")
        page_b = _make_page(workspace, project, create_user, name="B")

        response = session_client.patch(
            f"/api/workspaces/{workspace.slug}/projects/{project.id}/pages/{page_a.id}/",
            {"parent": str(page_b.id)},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        page_a.refresh_from_db()
        assert str(page_a.parent_id) == str(page_b.id)
