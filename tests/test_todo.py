"""Tests for todo CLI manager."""

import json
import tempfile
from pathlib import Path
import pytest
from todo import TodoItem, TodoManager


class TestTodoItem:
    """Test TodoItem class."""

    def test_todo_creation(self):
        todo = TodoItem("Test task", priority="high", category="work")
        assert todo.title == "Test task"
        assert todo.priority == "high"
        assert todo.category == "work"
        assert not todo.completed

    def test_todo_to_dict(self):
        todo = TodoItem("Test", id=1)
        data = todo.to_dict()
        assert data["title"] == "Test"
        assert data["id"] == 1

    def test_todo_from_dict(self):
        data = {
            "id": 1,
            "title": "Test",
            "priority": "medium",
            "due_date": None,
            "category": "general",
            "completed": False,
            "created_at": "2025-01-01T00:00:00"
        }
        todo = TodoItem.from_dict(data)
        assert todo.id == 1
        assert todo.title == "Test"


class TestTodoManager:
    """Test TodoManager class."""

    @pytest.fixture
    def temp_manager(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            f.write('[]')
            temp_path = f.name
        manager = TodoManager(temp_path)
        yield manager
        Path(temp_path).unlink(missing_ok=True)

    def test_add_todo(self, temp_manager):
        todo = temp_manager.add("New task", priority="high")
        assert todo.id == 1
        assert todo.title == "New task"
        assert len(temp_manager.todos) == 1

    def test_list_pending_only(self, temp_manager):
        temp_manager.add("Task 1")
        temp_manager.add("Task 2")
        temp_manager.complete(1)
        pending = temp_manager.list(show_all=False)
        assert len(pending) == 1
        assert pending[0].title == "Task 2"

    def test_complete_todo(self, temp_manager):
        temp_manager.add("Task")
        assert temp_manager.complete(1)
        assert temp_manager.todos[0].completed

    def test_delete_todo(self, temp_manager):
        temp_manager.add("Task")
        assert temp_manager.delete(1)
        assert len(temp_manager.todos) == 0

    def test_edit_todo(self, temp_manager):
        todo = temp_manager.add("Original")
        assert temp_manager.edit(1, title="Updated", priority="high")
        assert temp_manager.todos[0].title == "Updated"
        assert temp_manager.todos[0].priority == "high"

    def test_stats(self, temp_manager):
        temp_manager.add("Task 1", priority="high")
        temp_manager.add("Task 2", priority="low")
        temp_manager.complete(1)
        stats = temp_manager.stats()
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert stats["pending"] == 1
        assert stats["by_priority"]["low"] == 1

    def test_filter_by_category(self, temp_manager):
        temp_manager.add("Work task", category="work")
        temp_manager.add("Personal task", category="personal")
        work_todos = temp_manager.list(category="work")
        assert len(work_todos) == 1
        assert work_todos[0].category == "work"