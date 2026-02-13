#!/usr/bin/env python3
"""
Command-Line Todo List Manager
A full-featured CLI todo app with priorities, due dates, and categories.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict
import argparse


class TodoItem:
    """Represents a single todo item."""

    def __init__(
        self,
        title: str,
        priority: str = "medium",
        due_date: Optional[str] = None,
        category: str = "general",
        completed: bool = False,
        created_at: Optional[str] = None,
        id: Optional[int] = None,
    ):
        self.id = id
        self.title = title
        self.priority = priority.lower()
        self.due_date = due_date
        self.category = category.lower()
        self.completed = completed
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "priority": self.priority,
            "due_date": self.due_date,
            "category": self.category,
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "TodoItem":
        """Create TodoItem from dictionary."""
        return cls(**data)

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(self.priority, "⚪")
        due = f" (due: {self.due_date})" if self.due_date else ""
        return f"{status} [{self.id}] {priority_emoji} {self.title}{due} [{self.category}]"


class TodoManager:
    """Manages todo items storage and operations."""

    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

    def __init__(self, data_file: str = "todos.json"):
        self.data_file = Path(data_file)
        self.todos: List[TodoItem] = []
        self.next_id = 1
        self.load()

    def load(self):
        """Load todos from JSON file."""
        if self.data_file.exists():
            with open(self.data_file, "r") as f:
                data = json.load(f)
                self.todos = [TodoItem.from_dict(item) for item in data]
                if self.todos:
                    self.next_id = max(todo.id for todo in self.todos) + 1

    def save(self):
        """Save todos to JSON file."""
        with open(self.data_file, "w") as f:
            json.dump([todo.to_dict() for todo in self.todos], f, indent=2)

    def add(
        self,
        title: str,
        priority: str = "medium",
        due_date: Optional[str] = None,
        category: str = "general",
    ) -> TodoItem:
        """Add a new todo item."""
        todo = TodoItem(
            title=title,
            priority=priority,
            due_date=due_date,
            category=category,
            id=self.next_id,
        )
        self.todos.append(todo)
        self.next_id += 1
        self.save()
        return todo

    def list(
        self,
        show_all: bool = False,
        category: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[TodoItem]:
        """List todo items with optional filtering."""
        todos = self.todos if show_all else [t for t in self.todos if not t.completed]

        if category:
            todos = [t for t in todos if t.category == category.lower()]
        if priority:
            todos = [t for t in todos if t.priority == priority.lower()]

        # Sort by priority, then due date
        todos.sort(
            key=lambda t: (
                self.PRIORITY_ORDER.get(t.priority, 3),
                t.due_date or "9999-99-99",
            )
        )
        return todos

    def complete(self, todo_id: int) -> bool:
        """Mark a todo as completed."""
        for todo in self.todos:
            if todo.id == todo_id:
                todo.completed = True
                self.save()
                return True
        return False

    def uncomplete(self, todo_id: int) -> bool:
        """Mark a todo as not completed."""
        for todo in self.todos:
            if todo.id == todo_id:
                todo.completed = False
                self.save()
                return True
        return False

    def delete(self, todo_id: int) -> bool:
        """Delete a todo item."""
        for i, todo in enumerate(self.todos):
            if todo.id == todo_id:
                del self.todos[i]
                self.save()
                return True
        return False

    def edit(
        self,
        todo_id: int,
        title: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        category: Optional[str] = None,
    ) -> bool:
        """Edit a todo item."""
        for todo in self.todos:
            if todo.id == todo_id:
                if title:
                    todo.title = title
                if priority:
                    todo.priority = priority.lower()
                if due_date is not None:
                    todo.due_date = due_date
                if category:
                    todo.category = category.lower()
                self.save()
                return True
        return False

    def stats(self) -> Dict:
        """Get todo statistics."""
        total = len(self.todos)
        completed = sum(1 for t in self.todos if t.completed)
        pending = total - completed
        by_priority = {"high": 0, "medium": 0, "low": 0}
        by_category: Dict[str, int] = {}

        for todo in self.todos:
            if not todo.completed:
                by_priority[todo.priority] = by_priority.get(todo.priority, 0) + 1
                by_category[todo.category] = by_category.get(todo.category, 0) + 1

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "by_priority": by_priority,
            "by_category": by_category,
        }

    def clear_completed(self) -> int:
        """Remove all completed todos. Returns count removed."""
        original_count = len(self.todos)
        self.todos = [t for t in self.todos if not t.completed]
        removed = original_count - len(self.todos)
        if removed > 0:
            self.save()
        return removed


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Command-Line Todo List Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s add "Buy groceries" --priority high --due 2025-12-25 --category shopping
  %(prog)s list
  %(prog)s list --category work --priority high
  %(prog)s done 1
  %(prog)s delete 1
  %(prog)s stats
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Add Todo
    add_parser = subparsers.add_parser("add", help="Add a new todo")
    add_parser.add_argument("title", help="Todo title")
    add_parser.add_argument(
        "-p",
        "--priority",
        choices=["high", "medium", "low"],
        default="medium",
        help="Priority level",
    )
    add_parser.add_argument("-d", "--due", help="Due date (YYYY-MM-DD)")
    add_parser.add_argument(
        "-c", "--category", default="general", help="Category (default: general)"
    )

    # List Todos
    list_parser = subparsers.add_parser("list", help="List todos")
    list_parser.add_argument("-a", "--all", action="store_true", help="Show completed todos too")
    list_parser.add_argument("-c", "--category", help="Filter by category")
    list_parser.add_argument(
        "-p", "--priority", choices=["high", "medium", "low"], help="Filter by priority"
    )

    # Done Todos
    done_parser = subparsers.add_parser("done", help="Mark todo as completed")
    done_parser.add_argument("id", type=int, help="Todo ID")

    # Undo Todo
    undo_parser = subparsers.add_parser("undo", help="Mark todo as not completed")
    undo_parser.add_argument("id", type=int, help="Todo ID")

    # Delete Todo
    delete_parser = subparsers.add_parser("delete", help="Delete a todo")
    delete_parser.add_argument("id", type=int, help="Todo ID")

    # Edit Todo
    edit_parser = subparsers.add_parser("edit", help="Edit a todo")
    edit_parser.add_argument("id", type=int, help="Todo ID")
    edit_parser.add_argument("-t", "--title", help="New title")
    edit_parser.add_argument(
        "-p", "--priority", choices=["high", "medium", "low"], help="New priority"
    )
    edit_parser.add_argument("-d", "--due", help="New due date (YYYY-MM-DD)")
    edit_parser.add_argument("-c", "--category", help="New category")

    # Stats
    subparsers.add_parser("stats", help="Show statistics")

    # Clear command
    subparsers.add_parser("clear", help="Remove all completed todos")

    return parser


def print_stats(stats: Dict):
    """Print formatted statistics."""
    print("\n" + "=" * 40)
    print("TODO STATISTICS")
    print("=" * 40)
    print(f"Total todos:    {stats['total']}")
    print(f"Completed:      {stats['completed']}")
    print(f"Pending:        {stats['pending']}")
    print(f"\nBy Priority (pending):")
    for priority, count in stats["by_priority"].items():
        emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        print(f"{emoji} {priority.capitalize()}: {count}")
    if stats["by_category"]:
        print(f"\nBy Category (pending):")
        for cat, count in sorted(stats["by_category"].items()):
            print(f"• {cat}: {count}")
    print("=" * 40 + "\n")


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = TodoManager()

    if args.command == "add":
        todo = manager.add(
            title=args.title,
            priority=args.priority,
            due_date=args.due,
            category=args.category,
        )
        print(f"✓ Added: {todo}")

    elif args.command == "list":
        todos = manager.list(show_all=args.all, category=args.category, priority=args.priority)
        if not todos:
            filter_info = []
            if args.category:
                filter_info.append(f"category='{args.category}'")
            if args.priority:
                filter_info.append(f"priority='{args.priority}'")
            filter_str = f" ({', '.join(filter_info)})" if filter_info else ""
            print(f"No todos found{filter_str}.")
        else:
            print(f"\n{'=' * 50}")
            print(f"TODO LIST{' (including completed)' if args.all else ''}")
            print(f"{'=' * 50}")
            for todo in todos:
                print(todo)
            print(f"{'=' * 50}")
            print(f"Showing {len(todos)} item(s)\n")

    elif args.command == "done":
        if manager.complete(args.id):
            print(f"✓ Marked todo #{args.id} as completed")
        else:
            print(f"✗ Todo #{args.id} not found")
            sys.exit(1)

    elif args.command == "undo":
        if manager.uncomplete(args.id):
            print(f"✓ Marked todo #{args.id} as not completed")
        else:
            print(f"✗ Todo #{args.id} not found")
            sys.exit(1)

    elif args.command == "delete":
        if manager.delete(args.id):
            print(f"✓ Deleted todo #{args.id}")
        else:
            print(f"✗ Todo #{args.id} not found")
            sys.exit(1)

    elif args.command == "edit":
        if manager.edit(
            args.id,
            title=args.title,
            priority=args.priority,
            due_date=args.due,
            category=args.category,
        ):
            print(f"✓ Updated todo #{args.id}")
        else:
            print(f"✗ Todo #{args.id} not found")
            sys.exit(1)

    elif args.command == "stats":
        print_stats(manager.stats())

    elif args.command == "clear":
        count = manager.clear_completed()
        print(f"✓ Cleared {count} completed todo(s)")


if __name__ == "__main__":
    main()
